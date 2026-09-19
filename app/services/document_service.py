import os
import uuid
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from app.config import settings
from app.models.document import DocumentType


def validate_file(file: UploadFile) -> Tuple[str, int]:
    """Validate file extension, mime type, and file size."""
    filename = file.filename or "unknown"
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '.{ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Read bytes to check file size
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)  # Reset position

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed limit of {settings.MAX_FILE_SIZE_MB}MB."
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    return ext, file_size


def save_upload_file(file: UploadFile, ext: str) -> str:
    """Save upload file to storage directory safely."""
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    target_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    with open(target_path, "wb") as f:
        content = file.file.read()
        f.write(content)

    return target_path


def infer_document_type(filename: str, sample_text: str = "") -> DocumentType:
    """Heuristic determination of whether doc is question paper or answer key."""
    fn_lower = filename.lower()
    text_lower = sample_text.lower()

    if "answer" in fn_lower or "solution" in fn_lower or "key" in fn_lower:
        return DocumentType.ANSWER_KEY
    elif "answer key" in text_lower or "solutions" in text_lower and len(sample_text) < 1000:
        return DocumentType.ANSWER_KEY
    elif "question" in fn_lower or "paper" in fn_lower or "exam" in fn_lower:
        return DocumentType.QUESTION_PAPER
    return DocumentType.QUESTION_PAPER
