import logging
from typing import Dict, Any, List, Tuple
from app.models.question import ConfidenceLevel, QuestionType, AnswerSource
from app.models.review import LogCategory, LogLevel

logger = logging.getLogger(__name__)


class ConfidenceEngine:
    """
    Confidence & Validation Engine.
    Calculates numerical confidence_score (0.0 to 1.0) and assigns confidence_level & review flags.
    """

    @staticmethod
    def evaluate_question(q: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate confidence score for an extracted question.
        Modifies and returns question dict with confidence_score, confidence_level, review_reasons.
        """
        score = 0.0
        review_reasons = []

        q_type = q.get("question_type", QuestionType.MULTIPLE_CHOICE.value)
        q_text = q.get("question_text", "")
        options = q.get("options", [])
        source_pages = q.get("source_pages", [])
        answer_src = q.get("answer_source", AnswerSource.NOT_FOUND.value)
        ocr_used = q.get("ocr_used", False)

        # 1. Question Text Completeness (Weight: 0.35)
        text_score = 0.0
        if q_text and len(q_text.strip()) > 10:
            text_score = 1.0
            if any(char in q_text for char in ["?", ":", "following"]):
                text_score += 0.0  # good indicator
        elif q_text:
            text_score = 0.5
            review_reasons.append("Question text is unusually short.")
        else:
            review_reasons.append("Question text is empty or missing.")

        score += 0.35 * text_score

        # 2. Options Formatting & Count (Weight: 0.30)
        options_score = 1.0
        if q_type == QuestionType.MULTIPLE_CHOICE.value:
            if len(options) == 4:
                options_score = 1.0
            elif len(options) in (2, 3, 5):
                options_score = 0.75
                review_reasons.append(f"Non-standard option count: {len(options)} options extracted.")
            elif len(options) == 0:
                options_score = 0.20
                review_reasons.append("Multiple choice question with missing options.")
        score += 0.30 * options_score

        # 3. Source Pages & OCR Quality (Weight: 0.20)
        page_score = 1.0
        if len(source_pages) > 1:
            page_score -= 0.15
            review_reasons.append(f"Question spans across multiple pages ({', '.join(map(str, source_pages))}).")
        if ocr_used:
            page_score -= 0.10
            review_reasons.append("OCR was used due to scanned/low-resolution document.")

        page_score = max(0.0, page_score)
        score += 0.20 * page_score

        # 4. Answer Key Association (Weight: 0.15)
        answer_score = 0.40
        if answer_src != AnswerSource.NOT_FOUND.value:
            answer_score = 1.0
        else:
            review_reasons.append("Unmatched or uncertain answer key.")

        score += 0.15 * answer_score

        # Cap score between 0.0 and 1.0
        final_score = round(min(1.0, max(0.0, score)), 2)

        # Determine Confidence Level Classification
        if len(review_reasons) >= 2 or final_score < 0.50 or (q_type == QuestionType.MULTIPLE_CHOICE.value and len(options) == 0):
            level = ConfidenceLevel.NEEDS_REVIEW.value
        elif final_score >= 0.85:
            level = ConfidenceLevel.HIGH.value
        elif final_score >= 0.65:
            level = ConfidenceLevel.MEDIUM.value
        else:
            level = ConfidenceLevel.LOW.value

        q["confidence_score"] = final_score
        q["confidence_level"] = level
        q["review_reasons"] = review_reasons

        return q
