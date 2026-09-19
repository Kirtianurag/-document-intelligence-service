import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from app.models.document import DocumentStatus, DocumentType, RelationshipType


class DocumentBase(BaseModel):
    filename: str
    file_type: str
    file_size: int
    document_type: DocumentType = DocumentType.UNKNOWN


class DocumentCreate(DocumentBase):
    file_path: str


class DocumentResponse(DocumentBase):
    id: str
    user_id: str
    status: DocumentStatus
    page_count: int
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    metadata_info: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class DocumentStatusResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus
    page_count: int
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    questions_count: int = 0
    warnings_count: int = 0


class DocumentRelationshipCreate(BaseModel):
    target_document_id: str
    relationship_type: RelationshipType = RelationshipType.ANSWER_KEY_FOR


class DocumentRelationshipResponse(BaseModel):
    id: str
    source_document_id: str
    target_document_id: str
    relationship_type: RelationshipType
    created_at: datetime.datetime

    class Config:
        from_attributes = True
