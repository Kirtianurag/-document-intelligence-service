import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.models.question import AnswerSource

logger = logging.getLogger(__name__)

# Patterns for Answer Keys in Text
ANSWER_KEY_HEADER_PATTERNS = [
    r'ANSWER\s*KEY',
    r'SOLUTIONS?',
    r'CORRECT\s*ANSWERS?',
    r'ANSWER\s*SHEET',
]

# Patterns for individual answer lines: 1. A, Q1: B, 1-(C), 1. (a)
ANSWER_ITEM_PATTERNS = [
    r'(?:Q|Q\.)?\s*(\d+)\s*[\.\:\-\s]\s*[\(\[]?([A-Da-d1-4])[\)\]]?',   # 1. A or 1: (B) or Q1. C
    r'(\d+)\s*\rightarrow\s*([A-Da-d1-4])',                             # 1 -> A
]


class AnswerMatcher:
    """Answer Key Extractor & Matcher for internal & linked documents."""

    @staticmethod
    def extract_answer_keys_from_pages(pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scan pages for explicit Answer Key sections.
        Returns list of parsed answer keys: [{"question_number": "1", "raw_answer": "A", "parsed_answer": "A", "source_page": 1}]
        """
        extracted_keys = []

        for p in pages_data:
            page_num = p["page_num"]
            text = p["text"]

            lines = text.split("\n")
            in_answer_section = False

            for line in lines:
                line_upper = line.strip().upper()

                if any(re.search(pat, line_upper) for pat in ANSWER_KEY_HEADER_PATTERNS):
                    in_answer_section = True
                    continue

                if in_answer_section or "1." in line or "Q1" in line:
                    matches = AnswerMatcher._parse_line_answers(line)
                    for q_num, ans in matches:
                        extracted_keys.append({
                            "question_number": str(q_num),
                            "raw_answer": ans,
                            "parsed_answer": ans.upper(),
                            "source_page": page_num,
                            "confidence": 0.95 if in_answer_section else 0.70
                        })

        return extracted_keys

    @staticmethod
    def _parse_line_answers(line: str) -> List[Tuple[str, str]]:
        results = []
        for pat in ANSWER_ITEM_PATTERNS:
            for m in re.finditer(pat, line):
                q_num = m.group(1)
                ans = m.group(2)
                results.append((q_num, ans))
        return results

    @staticmethod
    def match_answers_to_questions(
        questions: List[Dict[str, Any]],
        answer_keys: List[Dict[str, Any]],
        is_linked_doc: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Match parsed answer keys to extracted questions.
        Updates question dicts in-place with answer, answer_source, explanation if available.
        """
        key_map = {ak["question_number"]: ak for ak in answer_keys}

        for q in questions:
            q_num = q.get("question_number")
            
            if q_num in key_map:
                ak = key_map[q_num]
                q["answer"] = ak["parsed_answer"]
                q["answer_source"] = AnswerSource.LINKED_DOC.value if is_linked_doc else AnswerSource.EMBEDDED_KEY.value
                q["answer_confidence"] = ak.get("confidence", 0.90)
            else:
                # Attempt embedded answer inline (e.g. "Answer: B" in question block)
                raw_text = q.get("raw_text", "")
                inline_match = re.search(r'(?:Ans(?:wer)?|Correct Option)\s*[\:\-]\s*[\(\[]?([A-Da-d1-4])[\)\]]?', raw_text, re.IGNORECASE)
                if inline_match:
                    q["answer"] = inline_match.group(1).upper()
                    q["answer_source"] = AnswerSource.EMBEDDED_KEY.value
                    q["answer_confidence"] = 0.90
                else:
                    q["answer"] = None
                    q["answer_source"] = AnswerSource.NOT_FOUND.value
                    q["answer_confidence"] = 0.0

        return questions
