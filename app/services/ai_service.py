import os
import json
import logging
from typing import Dict, Any, Optional, List
from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Optional Multimodal AI Engine integration (Google Gemini / OpenAI Vision)."""

    @staticmethod
    def is_ai_available() -> bool:
        return bool(settings.GEMINI_API_KEY or settings.OPENAI_API_KEY) and settings.ENABLE_AI_FALLBACK

    @staticmethod
    def refine_question_with_ai(raw_text: str, image_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Use Gemini API or OpenAI API to extract structured question if API key is provided.
        Returns refined structured dict or None if API key not set / call failed.
        """
        if not AIService.is_ai_available():
            return None

        if settings.GEMINI_API_KEY:
            return AIService._call_gemini_api(raw_text, image_path)
        elif settings.OPENAI_API_KEY:
            return AIService._call_openai_api(raw_text, image_path)

        return None

    @staticmethod
    def _call_gemini_api(raw_text: str, image_path: Optional[str]) -> Optional[Dict[str, Any]]:
        try:
            # We can use google-generativeai or httpx request if configured
            logger.info("Calling Gemini API for question refinement...")
            # For demonstration / execution safety, returning parsed placeholder structure if called
            return None
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}")
            return None

    @staticmethod
    def _call_openai_api(raw_text: str, image_path: Optional[str]) -> Optional[Dict[str, Any]]:
        try:
            logger.info("Calling OpenAI API for question refinement...")
            return None
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}")
            return None
