import uuid
import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FAILED = "FAILED"


class DocumentType(str, Enum):
    QUESTION_PAPER = "QUESTION_PAPER"
    ANSWER_KEY = "ANSWER_KEY"
    COMBINED = "COMBINED"
    UNKNOWN = "UNKNOWN"


class RelationshipType(str, Enum):
    ANSWER_KEY_FOR = "ANSWER_KEY_FOR"
    SUPPLEMENT_TO = "SUPPLEMENT_TO"


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, png, jpg, jpeg
    file_size = Column(Integer, nullable=False)  # bytes
    document_type = Column(String(50), default=DocumentType.UNKNOWN.value)
    status = Column(String(50), default=DocumentStatus.PENDING.value)
    page_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    metadata_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="documents")
    questions = relationship("Question", back_populates="document", cascade="all, delete-orphan")
    answer_keys = relationship("AnswerKey", back_populates="document", cascade="all, delete-orphan")
    logs = relationship("ProcessingLog", back_populates="document", cascade="all, delete-orphan")


class DocumentRelationship(Base):
    __tablename__ = "document_relationships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    target_document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    relationship_type = Column(String(50), default=RelationshipType.ANSWER_KEY_FOR.value)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
