import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from app.models.question import QuestionType

logger = logging.getLogger(__name__)

# Regex Patterns for Questions
QUESTION_HEADER_PATTERNS = [
    r'^(?:Q(?:uestion)?\.?\s*)?(\d+)\.\s+',                     # 1. or Q1. or Question 1.
    r'^(?:Q(?:uestion)?\.?\s*)?(\d+)\)\s+',                     # 1) or Q1) or Question 1)
    r'^(?:Q(?:uestion)?\.?\s*)?\[(\d+)\]\s+',                   # [1] or Q[1]
    r'^(?:Q(?:uestion)?\.?\s*)?(\d+)\:?\s+',                    # Q1: or Question 1:
    r'^(?:Q|Q\.)\s*(\d+)\b',                                    # Q1 or Q.1
    r'^\((\d+)\)\s+',                                           # (1)
    r'^\(([ivx]{1,4}|[IVX]{1,4})\)\s+',                         # (i), (ii), (iv) - avoiding C and D MCQ options
]

# Regex Patterns for MCQ Options
OPTION_PATTERNS = [
    r'[\(\[]([A-Da-d1-4])[\)\]]\s+',                           # (A) or [A] or (1)
    r'(?:\b|^)([A-Da-d1-4])[\.\)]\s+',                         # A. or A) or 1.
]


class QuestionExtractor:
    """Intelligent Question Segmentation and Option Extractor."""

    @staticmethod
    def process_pages(pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process extracted pages data and segment into structured question dicts.
        Handles multi-page questions seamlessly.
        """
        raw_blocks = []

        for p in pages_data:
            page_num = p["page_num"]
            text = p["text"]
            images = p.get("images", [])
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            
            raw_blocks.append({
                "page_num": page_num,
                "lines": lines,
                "images": images,
                "ocr_used": p.get("ocr_used", False)
            })

        extracted_questions = QuestionExtractor._segment_questions(raw_blocks)
        return extracted_questions

    @staticmethod
    def _segment_questions(raw_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        questions = []
        current_q = None

        for block in raw_blocks:
            page_num = block["page_num"]
            lines = block["lines"]
            page_images = block["images"]

            for line in lines:
                header_match, q_num = QuestionExtractor._match_question_header(line)

                if header_match:
                    # Save previous question if exists
                    if current_q:
                        QuestionExtractor._finalize_question(current_q)
                        questions.append(current_q)

                    # Start new question
                    clean_text = line[header_match.end():].strip()
                    current_q = {
                        "question_number": str(q_num),
                        "raw_lines": [clean_text] if clean_text else [],
                        "source_pages": [page_num],
                        "images": list(page_images),
                        "ocr_used": block["ocr_used"],
                    }
                else:
                    if current_q:
                        current_q["raw_lines"].append(line)
                        if page_num not in current_q["source_pages"]:
                            current_q["source_pages"].append(page_num)
                        # Append images from subsequent page if question spans across
                        for img in page_images:
                            if img not in current_q["images"]:
                                current_q["images"].append(img)
                    else:
                        # Preamble or header before Q1
                        pass

        # Save last question
        if current_q:
            QuestionExtractor._finalize_question(current_q)
            questions.append(current_q)

        return questions

    @staticmethod
    def _match_question_header(line: str) -> Tuple[Optional[re.Match], Optional[str]]:
        for pat in QUESTION_HEADER_PATTERNS:
            m = re.search(pat, line)
            if m:
                q_num = m.group(1)
                return m, q_num
        return None, None

    @staticmethod
    def _finalize_question(q: Dict[str, Any]):
        """
        Parse raw_lines into question_text, options, question_type, and initial confidence.
        """
        full_text = "\n".join(q["raw_lines"]).strip()
        q["raw_text"] = full_text

        # Extract options
        options, body_text = QuestionExtractor._extract_options(full_text)
        q["question_text"] = body_text if body_text else full_text
        q["options"] = options

        # Infer question type
        if len(options) >= 2:
            q["question_type"] = QuestionType.MULTIPLE_CHOICE.value
        elif any(kw in full_text.lower() for kw in ["true or false", "true/false", "t/f"]):
            q["question_type"] = QuestionType.TRUE_FALSE.value
            if not options:
                q["options"] = [
                    {"key": "A", "text": "True"},
                    {"key": "B", "text": "False"}
                ]
        elif any(kw in full_text.lower() for kw in ["calculate", "find the value", "evaluate", "solve"]):
            q["question_type"] = QuestionType.NUMERICAL.value
        elif len(full_text.split()) > 40:
            q["question_type"] = QuestionType.ESSAY.value
        else:
            q["question_type"] = QuestionType.SHORT_ANSWER.value

        q["has_images_or_tables"] = len(q.get("images", [])) > 0

    @staticmethod
    def _extract_options(full_text: str) -> Tuple[List[Dict[str, str]], str]:
        """
        Separate options from main question text.
        Supports standard inline or newlined (A) ..., (B) ..., etc.
        """
        options = []
        
        # Check for inline or newline option patterns like (A) ... (B) ... or A) ... B) ...
        # Standard regex matcher for option blocks
        opt_matches = list(re.finditer(r'(?:^|\s|\n)([\(\[]?[A-Da-d1-4][\.\)\]])\s+([^\(\[\n]+)', full_text))

        if len(opt_matches) >= 2:
            # We found options!
            first_opt_start = opt_matches[0].start()
            body_text = full_text[:first_opt_start].strip()

            for match in opt_matches:
                raw_key = match.group(1).translate(str.maketrans("", "", "()[]."))
                opt_key = raw_key.upper()
                opt_val = match.group(2).strip()
                # Clean trailing option markers if glued
                opt_val = re.sub(r'[\(\[]?[A-D1-4][\.\)\]]\s*$', '', opt_val).strip()
                
                options.append({
                    "key": opt_key,
                    "text": opt_val
                })
            return options, body_text

        # Fallback line-by-line option parser
        lines = full_text.split("\n")
        body_lines = []
        for line in lines:
            line_str = line.strip()
            line_match = re.match(r'^[\(\[]?([A-Da-d1-4])[\.\)\]]\s*(.+)$', line_str)
            if line_match:
                key = line_match.group(1).upper()
                text = line_match.group(2).strip()
                options.append({"key": key, "text": text})
            elif not options:
                body_lines.append(line_str)
            else:
                # Continuation of previous option
                if options:
                    options[-1]["text"] += " " + line_str

        if len(options) >= 2:
            return options, "\n".join(body_lines).strip()

        return [], full_text
