# Document Intelligence & Question Extraction Service

Production-oriented **Document Intelligence & Question Extraction Service** built for **Pragati Bharati** using **FastAPI**, **PostgreSQL**, **Redis / Celery**, and a hybrid **OCR / AI Extraction Pipeline**.

The system accepts unstructured or semi-structured PDF documents and images (PNG, JPG, JPEG) containing examination material and converts them into structured, machine-readable questions with answer keys, source page mappings, confidence ratings, and review flags.

---

## Technical Stack & Architecture

- **API Layer**: FastAPI (Python 3.11+) with Pydantic v2 validation and OpenAPI Swagger UI.
- **Database**: PostgreSQL 15+ (with SQLAlchemy 2.0 ORM & Alembic migrations). SQLite fallback included for instant standalone zero-config evaluation.
- **Asynchronous Task Queue**: Celery 5+ with Redis broker/backend and local background task runner.
- **OCR & Document Parsing Engine**: PyMuPDF (`fitz`), Pillow, `pdf2image`, Tesseract OCR (`pytesseract`), regex heuristics, and optional Google Gemini / OpenAI vision integration.
- **Authentication**: JWT token authentication with OAuth2 Bearer password flow and bcrypt hashing.

---

## Quick Start & Running Instructions

### Option 1: Run Standalone (Zero-Config / No Docker Required)

1. **Clone & Install Dependencies**:
   ```bash
   git clone <repository_url>
   cd PNBC
   pip install -r requirements.txt
   ```

2. **Generate Sample Documents & Seed Data**:
   ```bash
   python scripts/generate_samples.py
   ```

3. **Run Demonstration Pipeline & Export Sample Outputs**:
   ```bash
   python scripts/test_demo_flow.py
   ```

4. **Start FastAPI Application Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   Open Swagger UI in browser: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

### Option 2: Run with Docker Compose (PostgreSQL + Redis + Worker + API)

```bash
docker-compose up --build
```
The API server will be available at `http://localhost:8000`.

---

## Running Automated Tests

Run the comprehensive pytest suite covering API endpoints, JWT auth, document validation, question extraction, multi-page joiner, and confidence scoring:

```bash
python -m pytest -v
```

---

## API Endpoints & Workflows

### Authentication
- `POST /api/v1/auth/register` — Register a new user account.
- `POST /api/v1/auth/token` — Authenticate and retrieve JWT Bearer token.

### Document Management
- `POST /api/v1/documents/upload` — Upload PDF/PNG/JPG file asynchronously.
- `GET /api/v1/documents/` — List all user uploaded documents.
- `GET /api/v1/documents/{document_id}` — Get document metadata and details.
- `GET /api/v1/documents/{document_id}/status` — Track real-time extraction progress and status.
- `POST /api/v1/documents/{document_id}/relationships` — Link related documents (e.g., Answer Key PDF to Question Paper PDF).
- `DELETE /api/v1/documents/{document_id}` — Delete document and associated extracted data.

### Question Retrieval & Details
- `GET /api/v1/documents/{document_id}/questions` — Retrieve extracted questions (supports filtering by `confidence_level`, `question_type`, `needs_review_only`).
- `GET /api/v1/questions/{question_id}` — Retrieve detailed information for an individual question.
- `GET /api/v1/documents/{document_id}/answers` — Retrieve parsed answer key information.
- `GET /api/v1/documents/{document_id}/review-items` — Retrieve questions flagged for human review.
- `GET /api/v1/documents/{document_id}/warnings` — Retrieve OCR quality warnings and processing logs.
- `GET /api/v1/documents/{document_id}/export` — Export structured JSON output conforming to Section 7 specification.

---

## Deliverables Included

1. **Complete Source Code**: Located in `app/` and `scripts/`.
2. **Database Migrations**: Located in `migrations/` (Alembic).
3. **Sample Input Documents**: Generated in `sample_data/` (`sample_1_clean.pdf`, `sample_2_scanned.png`, `sample_3_low_quality.pdf`, `sample_4_multipage_split.pdf`, `sample_5_question_paper.pdf`, `sample_5_answer_key.pdf`, `sample_6_invalid.txt`).
4. **Sample Extracted Outputs**: Exported JSON files in `sample_outputs/`.
5. **Setup Instructions**: Provided in this `README.md`.
6. **Architecture Documentation**: Detailed specifications and diagrams in `ARCHITECTURE.md`.
7. **Automated Tests**: Test suite in `tests/`.
8. **Postman Collection**: `Postman_Collection.json`.
9. **Swagger UI / OpenAPI Spec**: Available at `http://localhost:8000/docs`.
10. **Demonstration Script**: Executed via `python scripts/test_demo_flow.py`.

---

## Structured Output Schema Example (Section 7)

```json
{
  "id": "e41f23e1-a298-414a-8f62-efd7f94f5c94",
  "question_number": "1",
  "question": "What is the capital of France?",
  "question_type": "MULTIPLE_CHOICE",
  "options": [
    {"key": "A", "text": "Berlin"},
    {"key": "B", "text": "Paris"},
    {"key": "C", "text": "Madrid"},
    {"key": "D", "text": "Rome"}
  ],
  "answer": "B",
  "answer_source": "EMBEDDED_KEY",
  "source_pages": [1],
  "confidence": 0.95,
  "confidence_level": "HIGH",
  "has_images": false,
  "review_reasons": []
}
```
