import os
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

SAMPLE_DIR = "sample_data"
os.makedirs(SAMPLE_DIR, exist_ok=True)


def generate_sample_1_clean_pdf():
    doc = fitz.open()
    page = doc.new_page()

    text = """PRAGATI BHARATI ASSIGNMENT - MATHEMATICS & SCIENCE EXAM

Q1. What is the capital of France?
(A) Berlin
(B) Paris
(C) Madrid
(D) Rome

Q2. Which planet is known as the Red Planet?
(A) Venus
(B) Jupiter
(C) Mars
(D) Saturn

Q3. Calculate the derivative of f(x) = 3x^2 + 5x - 7.
(A) 6x + 5
(B) 3x + 5
(C) 6x - 7
(D) 3x^2 + 5

Q4. Solve the equation 2x + 10 = 20 for x.
(A) 5
(B) 10
(C) 15
(D) 20

ANSWER KEY:
1. B
2. C
3. A
4. A
"""
    page.insert_text((50, 50), text, fontsize=12)
    pdf_path = os.path.join(SAMPLE_DIR, "sample_1_clean.pdf")
    doc.save(pdf_path)
    doc.close()
    print(f"Generated {pdf_path}")


def generate_sample_2_scanned_png():
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    d = ImageDraw.Draw(img)

    text = """SAMPLE IMAGE QUESTION BANK

1. Which element has the chemical symbol 'O'?
(A) Gold
(B) Oxygen
(C) Silver
(D) Hydrogen

2. What is 15 multiplied by 4?
(A) 45
(B) 50
(C) 60
(D) 70

ANSWER KEY
1. B
2. C
"""
    d.text((40, 40), text, fill=(0, 0, 0))
    img_path = os.path.join(SAMPLE_DIR, "sample_2_scanned.png")
    img.save(img_path)
    print(f"Generated {img_path}")


def generate_sample_3_low_quality_pdf():
    doc = fitz.open()
    page = doc.new_page()

    # Intentionally noisy / low quality scan simulation text
    text = """SAMPLE LOW QUALITY & ROTATED SCAN

Q1. Unclear blur question text with noise...
(A) Option A
(B) Option B

Q2. What is the velocity of light in vacuum?
(A) 3 x 10^8 m/s
(B) 1.5 x 10^8 m/s
"""
    page.insert_text((50, 50), text, fontsize=11)
    pdf_path = os.path.join(SAMPLE_DIR, "sample_3_low_quality.pdf")
    doc.save(pdf_path)
    doc.close()
    print(f"Generated {pdf_path}")


def generate_sample_4_multipage_split_pdf():
    doc = fitz.open()
    page1 = doc.new_page()

    text_page1 = """PRAGATI BHARATI MULTI-PAGE QUESTION PAPER - PAGE 1

Q1. What is the primary function of mitochondria?
(A) Protein synthesis
(B) Energy production (ATP)
(C) DNA replication
(D) Lipid storage

Q2. A complex physics question starts on Page 1: Consider a particle of mass m moving under a central potential V(r) = -k/r. The orbit is closed and elliptical."""

    page1.insert_text((50, 50), text_page1, fontsize=12)

    page2 = doc.new_page()
    text_page2 = """PAGE 2 (CONTINUATION OF QUESTION PAPER)

What is the total mechanical energy of the particle in terms of semi-major axis 'a'?
(A) E = -k / (2a)
(B) E = -k / a
(C) E = -2k / a
(D) E = 0

ANSWER KEY:
1. B
2. A
"""
    page2.insert_text((50, 50), text_page2, fontsize=12)

    pdf_path = os.path.join(SAMPLE_DIR, "sample_4_multipage_split.pdf")
    doc.save(pdf_path)
    doc.close()
    print(f"Generated {pdf_path}")


def generate_sample_5_separate_question_and_answer_key():
    # Question paper PDF
    doc_q = fitz.open()
    page_q = doc_q.new_page()
    text_q = """PHYSICS MIDTERM EXAMINATION - QUESTION PAPER

Q1. State Newton's second law of motion.
(A) F = ma
(B) F = m/a
(C) F = m^2 a
(D) F = v/t

Q2. What is the SI unit of electric current?
(A) Volt
(B) Ohm
(C) Ampere
(D) Watt
"""
    page_q.insert_text((50, 50), text_q, fontsize=12)
    q_path = os.path.join(SAMPLE_DIR, "sample_5_question_paper.pdf")
    doc_q.save(q_path)
    doc_q.close()
    print(f"Generated {q_path}")

    # Answer Key PDF
    doc_a = fitz.open()
    page_a = doc_a.new_page()
    text_a = """PHYSICS MIDTERM EXAMINATION - OFFICIAL ANSWER KEY

SOLUTIONS & ANSWERS:
1. A
2. C
"""
    page_a.insert_text((50, 50), text_a, fontsize=12)
    a_path = os.path.join(SAMPLE_DIR, "sample_5_answer_key.pdf")
    doc_a.save(a_path)
    doc_a.close()
    print(f"Generated {a_path}")


def generate_sample_6_invalid_file():
    invalid_path = os.path.join(SAMPLE_DIR, "sample_6_invalid.txt")
    with open(invalid_path, "w") as f:
        f.write("This is an invalid file format (plain text) not accepted by the upload endpoint.")
    print(f"Generated {invalid_path}")


if __name__ == "__main__":
    generate_sample_1_clean_pdf()
    generate_sample_2_scanned_png()
    generate_sample_3_low_quality_pdf()
    generate_sample_4_multipage_split_pdf()
    generate_sample_5_separate_question_and_answer_key()
    generate_sample_6_invalid_file()
    print("All sample input documents successfully generated in 'sample_data/'!")
