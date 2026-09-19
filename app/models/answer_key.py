import uuid
import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class AnswerKey(Base):
    __tablename__ = "answer_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    question_number = Column(String(50), nullable=False)
    raw_answer = Column(Text, nullable=False)
    parsed_answer = Column(String(255), nullable=True)
    confidence = Column(Float, default=1.0)
    source_page = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="answer_keys")
