import os
import time
import logging
from typing import Dict, Any, List
from celery import Celery
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, engine, Base
from app.models.document import Document, DocumentStatus, DocumentType, DocumentRelationship, RelationshipType
from app.models.question import Question, QuestionType, AnswerSource, ConfidenceLevel
from app.models.answer_key import AnswerKey
from app.models.review import ProcessingLog, LogLevel, LogCategory
from app.services.document_service import infer_document_type
from app.services.ocr_engine import OCREngine
from app.services.question_extractor import QuestionExtractor
from app.services.answer_matcher import AnswerMatcher
from app.services.confidence_engine import ConfidenceEngine

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "document_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


def process_document_pipeline(document_id: str) -> Dict[str, Any]:
    """
    Core document intelligence pipeline execution.
    Can be called synchronously by background task or asynchronously by Celery worker.
    """
    start_time = time.time()
    db: Session = SessionLocal()

    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found")
            return {"status": "FAILED", "error": "Document not found"}

        # Update status to PROCESSING
        doc.status = DocumentStatus.PROCESSING.value
        db.commit()

        # 1. OCR / Text Extraction
        pages_data = OCREngine.extract_pages(doc.file_path, doc.file_type)
        doc.page_count = len(pages_data)

        full_sample_text = "\n".join([p["text"] for p in pages_data[:2]])
        inferred_type = infer_document_type(doc.filename, full_sample_text)
        if doc.document_type == DocumentType.UNKNOWN.value:
            doc.document_type = inferred_type.value

        # Log OCR step
        log_entry = ProcessingLog(
            document_id=doc.id,
            log_level=LogLevel.INFO.value,
            category=LogCategory.OCR_QUALITY.value,
            message=f"Extracted {len(pages_data)} pages. OCR required: {any(p['ocr_used'] for p in pages_data)}"
        )
        db.add(log_entry)

        # Clear any old extracted questions or answer keys if re-processing
        db.query(Question).filter(Question.document_id == doc.id).delete()
        db.query(AnswerKey).filter(AnswerKey.document_id == doc.id).delete()

        # 2. Answer Key Extraction (if document is answer key or contains embedded answers)
        parsed_answer_keys = AnswerMatcher.extract_answer_keys_from_pages(pages_data)
        for ak in parsed_answer_keys:
            answer_key_obj = AnswerKey(
                document_id=doc.id,
                question_number=ak["question_number"],
                raw_answer=ak["raw_answer"],
                parsed_answer=ak["parsed_answer"],
                confidence=ak["confidence"],
                source_page=ak["source_page"]
            )
            db.add(answer_key_obj)
        db.commit()

        # 3. Question Extraction
        extracted_q_dicts = QuestionExtractor.process_pages(pages_data)

        # Check for linked Answer Key document if applicable
        linked_rel = db.query(DocumentRelationship).filter(
            DocumentRelationship.target_document_id == doc.id,
            DocumentRelationship.relationship_type == RelationshipType.ANSWER_KEY_FOR.value
        ).first()

        linked_answer_keys = []
        if linked_rel:
            ak_doc_id = linked_rel.source_document_id
            ak_rows = db.query(AnswerKey).filter(AnswerKey.document_id == ak_doc_id).all()
            linked_answer_keys = [
                {"question_number": ak.question_number, "parsed_answer": ak.parsed_answer, "confidence": ak.confidence}
                for ak in ak_rows
            ]

        # Combine embedded answer keys with linked answer keys
        all_answer_keys = parsed_answer_keys + linked_answer_keys
        extracted_q_dicts = AnswerMatcher.match_answers_to_questions(
            extracted_q_dicts,
            all_answer_keys,
            is_linked_doc=bool(linked_answer_keys)
        )

        # 4. Confidence Evaluation & Flagging
        needs_review = False
        saved_questions_count = 0

        for q_dict in extracted_q_dicts:
            evaluated_q = ConfidenceEngine.evaluate_question(q_dict)

            question_obj = Question(
                document_id=doc.id,
                question_number=evaluated_q.get("question_number"),
                question_text=evaluated_q.get("question_text", ""),
                question_type=evaluated_q.get("question_type", QuestionType.MULTIPLE_CHOICE.value),
                options=evaluated_q.get("options", []),
                answer=evaluated_q.get("answer"),
                answer_source=evaluated_q.get("answer_source", AnswerSource.NOT_FOUND.value),
                confidence_score=evaluated_q.get("confidence_score", 1.0),
                confidence_level=evaluated_q.get("confidence_level", ConfidenceLevel.HIGH.value),
                source_pages=evaluated_q.get("source_pages", [1]),
                has_images_or_tables=evaluated_q.get("has_images_or_tables", False),
                extracted_images=evaluated_q.get("images", []),
                raw_extracted_text=evaluated_q.get("raw_text", ""),
                review_reasons=evaluated_q.get("review_reasons", [])
            )
            db.add(question_obj)
            saved_questions_count += 1

            if evaluated_q.get("confidence_level") in [ConfidenceLevel.NEEDS_REVIEW.value, ConfidenceLevel.LOW.value]:
                needs_review = True
                # Log warning for human review
                db.add(ProcessingLog(
                    document_id=doc.id,
                    log_level=LogLevel.WARNING.value,
                    category=LogCategory.FORMATTING_ANOMALY.value,
                    message=f"Question {evaluated_q.get('question_number')} requires review: {', '.join(evaluated_q.get('review_reasons', []))}"
                ))

        elapsed_ms = int((time.time() - start_time) * 1000)
        doc.processing_time_ms = elapsed_ms
        doc.status = DocumentStatus.NEEDS_REVIEW.value if needs_review else DocumentStatus.COMPLETED.value
        db.commit()

        logger.info(f"Successfully processed document {document_id} in {elapsed_ms}ms with {saved_questions_count} questions.")
        return {
            "status": doc.status,
            "questions_extracted": saved_questions_count,
            "processing_time_ms": elapsed_ms
        }

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
        if 'doc' in locals() and doc:
            doc.status = DocumentStatus.FAILED.value
            doc.error_message = str(e)
            db.commit()
        return {"status": "FAILED", "error": str(e)}

    finally:
        db.close()


@celery_app.task(name="process_document_task")
def process_document_task(document_id: str):
    return process_document_pipeline(document_id)
