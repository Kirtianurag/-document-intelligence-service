import uuid
import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class LogLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LogCategory(str, Enum):
    OCR_QUALITY = "OCR_QUALITY"
    PAGE_SPLIT = "PAGE_SPLIT"
    UNMATCHED_ANSWER = "UNMATCHED_ANSWER"
    FORMATTING_ANOMALY = "FORMATTING_ANOMALY"
    MISSING_OPTIONS = "MISSING_OPTIONS"
    FILE_IO = "FILE_IO"


class ProcessingLog(Base):
    __tablename__ = "processing_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    log_level = Column(String(20), default=LogLevel.INFO.value)
    category = Column(String(50), default=LogCategory.FORMATTING_ANOMALY.value)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="logs")
