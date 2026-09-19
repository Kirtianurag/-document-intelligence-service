import uuid
import datetime
from enum import Enum
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    NUMERICAL = "NUMERICAL"
    SHORT_ANSWER = "SHORT_ANSWER"
    TRUE_FALSE = "TRUE_FALSE"
    MATCHING = "MATCHING"
    ESSAY = "ESSAY"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class AnswerSource(str, Enum):
    EMBEDDED_KEY = "EMBEDDED_KEY"
    LINKED_DOC = "LINKED_DOC"
    INFERRED = "INFERRED"
    NOT_FOUND = "NOT_FOUND"


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    question_number = Column(String(50), nullable=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default=QuestionType.MULTIPLE_CHOICE.value)
    options = Column(JSON, nullable=True)  # List of {"key": "A", "text": "..."}
    answer = Column(Text, nullable=True)
    answer_explanation = Column(Text, nullable=True)
    answer_source = Column(String(50), default=AnswerSource.NOT_FOUND.value)
    confidence_score = Column(Float, default=1.0)
    confidence_level = Column(String(50), default=ConfidenceLevel.HIGH.value)
    source_pages = Column(JSON, nullable=False)  # List of integers e.g. [1, 2]
    has_images_or_tables = Column(Boolean, default=False)
    extracted_images = Column(JSON, nullable=True)  # List of image file paths
    raw_extracted_text = Column(Text, nullable=True)
    review_reasons = Column(JSON, nullable=True)  # List of review warning strings
    bbox_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="questions")
