from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.question import Question, ConfidenceLevel
from app.models.review import ProcessingLog
from app.schemas.question import QuestionResponse
from app.schemas.common import ProcessingLogResponse

router = APIRouter(prefix="/documents", tags=["Review & Warnings"])


@router.get("/{document_id}/review-items", response_model=List[QuestionResponse])
def get_review_items(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve questions flagged for human review (low confidence, missing options, split questions, unmatched answers).
    """
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    questions = db.query(Question).filter(
        Question.document_id == document_id,
        Question.confidence_level.in_([ConfidenceLevel.NEEDS_REVIEW.value, ConfidenceLevel.LOW.value])
    ).all()

    return questions


@router.get("/{document_id}/warnings", response_model=List[ProcessingLogResponse])
def get_document_warnings(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve system processing warnings and logs for a document."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    logs = db.query(ProcessingLog).filter(ProcessingLog.document_id == document_id).order_by(ProcessingLog.created_at.asc()).all()
    return logs
