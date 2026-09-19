from app.services.question_extractor import QuestionExtractor


def test_question_segmentation():
    sample_pages = [{
        "page_num": 1,
        "text": """Q1. What is the derivative of x^2?
(A) 2x
(B) x
(C) x^2
(D) 0

Q2. What is 2 + 2?
(A) 3
(B) 4
""",
        "images": [],
        "ocr_used": False
    }]

    questions = QuestionExtractor.process_pages(sample_pages)
    assert len(questions) == 2
    assert questions[0]["question_number"] == "1"
    assert "derivative" in questions[0]["question_text"]
    assert len(questions[0]["options"]) == 4
    assert questions[0]["options"][0]["key"] == "A"
    assert questions[0]["options"][0]["text"] == "2x"

    assert questions[1]["question_number"] == "2"
    assert len(questions[1]["options"]) == 2


def test_multipage_question_segmentation():
    sample_pages = [
        {
            "page_num": 1,
            "text": "Q1. Question on Page 1 text...\n(A) Opt 1\n(B) Opt 2",
            "images": [],
            "ocr_used": False
        },
        {
            "page_num": 2,
            "text": "(C) Opt 3\n(D) Opt 4\n\nQ2. Question on Page 2",
            "images": [],
            "ocr_used": False
        }
    ]

    questions = QuestionExtractor.process_pages(sample_pages)
    assert len(questions) >= 1
    assert 1 in questions[0]["source_pages"]
