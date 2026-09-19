import datetime
from typing import Optional
from pydantic import BaseModel


class AnswerKeyBase(BaseModel):
    question_number: str
    raw_answer: str
    parsed_answer: Optional[str] = None
    confidence: float = 1.0
    source_page: int = 1


class AnswerKeyCreate(AnswerKeyBase):
    document_id: str


class AnswerKeyResponse(AnswerKeyBase):
    id: str
    document_id: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True
