import datetime
from typing import List, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class ProcessingLogResponse(BaseModel):
    id: str
    document_id: str
    log_level: str
    category: str
    message: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class DocumentExportResponse(BaseModel):
    document_id: str
    filename: str
    document_type: str
    page_count: int
    total_questions: int
    confidence_summary: dict
    questions: List[dict]
    answer_keys: List[dict]
    warnings: List[str]
