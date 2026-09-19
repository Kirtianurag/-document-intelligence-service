import sys
import os
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.security import get_password_hash
from app.models.user import User
from app.models.document import Document, DocumentStatus, DocumentType, DocumentRelationship, RelationshipType
from app.models.question import Question
from app.models.answer_key import AnswerKey
from app.services.document_service import validate_file, save_upload_file, infer_document_type
from app.worker.celery_worker import process_document_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("demo_flow")

OUTPUT_DIR = "sample_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def run_full_demo():
    print("=" * 70)
    print("STARTING FULL SYSTEM DEMONSTRATION & EXTRACTED OUTPUT GENERATION")
    print("=" * 70)

    # 1. Initialize DB
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    # 2. Create Demo User
    demo_user = db.query(User).filter(User.email == "demo@pragatibharati.edu").first()
    if not demo_user:
        demo_user = User(
            email="demo@pragatibharati.edu",
            hashed_password=get_password_hash("DemoSecret123!"),
            is_active=True
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
    print(f"[DEMO] Authenticated Demo User: {demo_user.email} (ID: {demo_user.id})")

    samples = [
        ("sample_1_clean.pdf", "pdf", "sample_1_output.json"),
        ("sample_2_scanned.png", "png", "sample_2_output.json"),
        ("sample_3_low_quality.pdf", "pdf", "sample_3_output.json"),
        ("sample_4_multipage_split.pdf", "pdf", "sample_4_output.json"),
        ("sample_5_answer_key.pdf", "pdf", "sample_5_answer_key_output.json"),
        ("sample_5_question_paper.pdf", "pdf", "sample_5_question_paper_output.json"),
    ]

    processed_docs = {}

    for fn, ftype, out_json in samples:
        src_path = os.path.join("sample_data", fn)
        if not os.path.exists(src_path):
            print(f"[WARNING] File {src_path} not found. Skipping.")
            continue

        file_size = os.path.getsize(src_path)
        doc = Document(
            user_id=demo_user.id,
            filename=fn,
            file_path=src_path,
            file_type=ftype,
            file_size=file_size,
            document_type=DocumentType.UNKNOWN.value,
            status=DocumentStatus.PENDING.value
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        processed_docs[fn] = doc

        # Execute processing pipeline
        res = process_document_pipeline(doc.id)
        db.refresh(doc)

        print(f"\n[DEMO] Processed '{fn}': Status={doc.status}, Pages={doc.page_count}, Time={doc.processing_time_ms}ms")

        # Fetch questions and export JSON
        questions = db.query(Question).filter(Question.document_id == doc.id).all()
        answer_keys = db.query(AnswerKey).filter(AnswerKey.document_id == doc.id).all()

        output_data = {
            "document_id": doc.id,
            "filename": doc.filename,
            "document_type": doc.document_type,
            "status": doc.status,
            "page_count": doc.page_count,
            "processing_time_ms": doc.processing_time_ms,
            "total_questions": len(questions),
            "questions": [
                {
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
                    "review_reasons": q.review_reasons or []
                }
                for q in questions
            ],
            "answer_keys": [
                {
                    "question_number": ak.question_number,
                    "raw_answer": ak.raw_answer,
                    "parsed_answer": ak.parsed_answer,
                    "confidence": ak.confidence,
                    "source_page": ak.source_page
                }
                for ak in answer_keys
            ],
            "warnings": [log.message for log in doc.logs if log.log_level in ("WARNING", "ERROR")]
        }

        out_path = os.path.join(OUTPUT_DIR, out_json)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        print(f"  -> Exported structured JSON output to {out_path}")

    # Test cross-document linking (Sample 5 Question Paper + Sample 5 Answer Key)
    if "sample_5_question_paper.pdf" in processed_docs and "sample_5_answer_key.pdf" in processed_docs:
        q_doc = processed_docs["sample_5_question_paper.pdf"]
        a_doc = processed_docs["sample_5_answer_key.pdf"]

        print(f"\n[DEMO] Testing Cross-Document Answer Key Relationship Linking...")
        rel = DocumentRelationship(
            source_document_id=a_doc.id,
            target_document_id=q_doc.id,
            relationship_type=RelationshipType.ANSWER_KEY_FOR.value
        )
        db.add(rel)
        db.commit()

        # Re-process question paper
        process_document_pipeline(q_doc.id)
        db.refresh(q_doc)

        q_questions = db.query(Question).filter(Question.document_id == q_doc.id).all()
        print(f"  -> Re-processed Question Paper after linking. Answer Sources:")
        for q in q_questions:
            print(f"     Q{q.question_number}: Answer={q.answer}, Source={q.answer_source}, Confidence={q.confidence_score}")

    db.close()
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_full_demo()
