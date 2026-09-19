import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.config import settings
from app.models.user import User
from app.models.document import Document, DocumentStatus, DocumentType, DocumentRelationship, RelationshipType
from app.models.question import Question
from app.schemas.document import (
    DocumentResponse,
    DocumentStatusResponse,
    DocumentRelationshipCreate,
    DocumentRelationshipResponse
)
from app.schemas.common import MessageResponse
from app.services.document_service import validate_file, save_upload_file
from app.worker.celery_worker import process_document_pipeline, process_document_task

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(DocumentType.UNKNOWN.value),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a PDF or image file (PNG, JPG, JPEG) for question extraction.
    Document processing happens asynchronously.
    """
    ext, file_size = validate_file(file)
    target_path = save_upload_file(file, ext)

    doc = Document(
        user_id=current_user.id,
        filename=file.filename or "uploaded_doc",
        file_path=target_path,
        file_type=ext,
        file_size=file_size,
        document_type=document_type if document_type in DocumentType.__members__ else DocumentType.UNKNOWN.value,
        status=DocumentStatus.PENDING.value
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Launch processing asynchronously
    if settings.USE_LOCAL_BACKGROUND_TASKS:
        background_tasks.add_task(process_document_pipeline, doc.id)
    else:
        process_document_task.delay(doc.id)

    return doc


@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all uploaded documents for the authorized user."""
    docs = db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    return docs


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details for a specific document."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return doc


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track real-time document processing status and question counts."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    questions_count = db.query(Question).filter(Question.document_id == doc.id).count()

    return DocumentStatusResponse(
        document_id=doc.id,
        filename=doc.filename,
        status=DocumentStatus(doc.status),
        page_count=doc.page_count,
        error_message=doc.error_message,
        processing_time_ms=doc.processing_time_ms,
        questions_count=questions_count,
        warnings_count=len(doc.logs) if doc.logs else 0
    )


@router.post("/{document_id}/relationships", response_model=DocumentRelationshipResponse)
def link_document_relationship(
    document_id: str,
    rel_in: DocumentRelationshipCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Associate a related document (e.g. link an Answer Key document to a Question Paper).
    Triggers re-processing of question paper to associate newly linked answer keys.
    """
    source_doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    target_doc = db.query(Document).filter(Document.id == rel_in.target_document_id, Document.user_id == current_user.id).first()

    if not source_doc or not target_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source or target document not found.")

    rel = DocumentRelationship(
        source_document_id=source_doc.id,
        target_document_id=target_doc.id,
        relationship_type=rel_in.relationship_type.value
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)

    # Trigger re-extraction of target question paper to apply new answer key matches
    background_tasks.add_task(process_document_pipeline, target_doc.id)

    return rel


@router.delete("/{document_id}", response_model=MessageResponse)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete document, physical file, and extracted questions."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    db.delete(doc)
    db.commit()
    return MessageResponse(message=f"Document '{doc.filename}' deleted successfully.")
