import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from app.models.question import QuestionType, ConfidenceLevel, AnswerSource


class QuestionOptionSchema(BaseModel):
    key: str  # e.g., "A", "B", "1", "a"
    text: str


class QuestionBase(BaseModel):
    question_number: Optional[str] = None
    question_text: str
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    options: Optional[List[QuestionOptionSchema]] = None
    answer: Optional[str] = None
    answer_explanation: Optional[str] = None
    answer_source: AnswerSource = AnswerSource.NOT_FOUND
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH
    source_pages: List[int]
    has_images_or_tables: bool = False
    extracted_images: Optional[List[str]] = None
    review_reasons: Optional[List[str]] = None


class QuestionCreate(QuestionBase):
    document_id: str
    raw_extracted_text: Optional[str] = None
    bbox_data: Optional[Dict[str, Any]] = None


class QuestionResponse(QuestionBase):
    id: str
    document_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class StandardStructuredQuestion(BaseModel):
    id: str
    question_number: Optional[str] = None
    question: str
    options: List[Dict[str, str]] = []
    answer: Optional[str] = None
    answer_source: str
    source_pages: List[int]
    confidence: float
    confidence_level: str
    has_images: bool = False
    review_reasons: List[str] = []
