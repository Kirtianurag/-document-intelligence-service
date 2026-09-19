from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.answer_key import AnswerKey
from app.schemas.answer import AnswerKeyResponse

router = APIRouter(prefix="/documents", tags=["Answer Keys"])


@router.get("/{document_id}/answers", response_model=List[AnswerKeyResponse])
def get_document_answers(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve extracted answer key information for a document."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    answers = db.query(AnswerKey).filter(AnswerKey.document_id == document_id).all()
    return answers
