from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.question import Question, ConfidenceLevel, QuestionType
from app.schemas.question import QuestionResponse

router = APIRouter(tags=["Questions"])


@router.get("/documents/{document_id}/questions", response_model=List[QuestionResponse])
def get_document_questions(
    document_id: str,
    confidence_level: Optional[ConfidenceLevel] = Query(None, description="Filter by confidence level"),
    question_type: Optional[QuestionType] = Query(None, description="Filter by question type"),
    needs_review_only: bool = Query(False, description="Filter questions that require human review"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all extracted questions for a given document with filtering options.
    """
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    query = db.query(Question).filter(Question.document_id == document_id)

    if confidence_level:
        query = query.filter(Question.confidence_level == confidence_level.value)
    if question_type:
        query = query.filter(Question.question_type == question_type.value)
    if needs_review_only:
        query = query.filter(Question.confidence_level.in_([ConfidenceLevel.NEEDS_REVIEW.value, ConfidenceLevel.LOW.value]))

    return query.order_by(Question.created_at.asc()).all()


@router.get("/questions/{question_id}", response_model=QuestionResponse)
def get_question_detail(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details for an individual question."""
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    # Check authorization via document ownership
    doc = db.query(Document).filter(Document.id == q.document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this question.")

    return q
