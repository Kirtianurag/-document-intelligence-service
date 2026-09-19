from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.question import Question
from app.models.answer_key import AnswerKey
from app.schemas.common import DocumentExportResponse

router = APIRouter(prefix="/documents", tags=["Export"])


@router.get("/{document_id}/export", response_model=DocumentExportResponse)
def export_document_json(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export final extracted questions and associated data in a structured, system-independent format.
    Conforms to Section 7 of the specification.
    """
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    questions = db.query(Question).filter(Question.document_id == document_id).all()
    answer_keys = db.query(AnswerKey).filter(AnswerKey.document_id == document_id).all()

    formatted_questions = []
    confidence_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "NEEDS_REVIEW": 0}

    for q in questions:
        c_level = q.confidence_level or "HIGH"
        confidence_counts[c_level] = confidence_counts.get(c_level, 0) + 1

        formatted_questions.append({
            "id": q.id,
            "question_number": q.question_number,
            "question": q.question_text,
            "question_type": q.question_type,
            "options": q.options or [],
            "answer": q.answer,
            "answer_source": q.answer_source,
            "source_pages": q.source_pages,
            "confidence": q.confidence_score,
            "confidence_level": q.confidence_level,
            "has_images": q.has_images_or_tables,
            "extracted_images": q.extracted_images or [],
            "review_reasons": q.review_reasons or []
        })

    formatted_answers = [
        {
            "question_number": ak.question_number,
            "raw_answer": ak.raw_answer,
            "parsed_answer": ak.parsed_answer,
            "confidence": ak.confidence,
            "source_page": ak.source_page
        }
        for ak in answer_keys
    ]

    warnings = [log.message for log in doc.logs if log.log_level in ("WARNING", "ERROR")]

    return DocumentExportResponse(
        document_id=doc.id,
        filename=doc.filename,
        document_type=doc.document_type,
        page_count=doc.page_count,
        total_questions=len(formatted_questions),
        confidence_summary=confidence_counts,
        questions=formatted_questions,
        answer_keys=formatted_answers,
        warnings=warnings
    )
