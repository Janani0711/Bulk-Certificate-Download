# Bulk Certificate Generator API & Web Dashboard

A scalable backend REST API and Web Dashboard built with **Python**, **FastAPI**, **SQLAlchemy**, and **ReportLab** for processing bulk certificate generation requests for course and event participants.

---

## Features

- **Bulk Certificate Submission**: Submit certificate generation requests containing hundreds of recipients in a single batch.
- **Asynchronous Background Processing**: Offloads CPU-bound PDF rendering to background worker tasks so API requests remain fast and non-blocking.
- **Recipient Validation & Failure Isolation**: Validates recipient names, emails, and data formats per record. Individual recipient failures do not block other valid certificates in the same batch from being generated.
- **Real-Time Progress & Status Tracking**: Track total, processed, successful, and failed certificate counts along with progress percentage.
- **Customizable PDF Certificate Generation**: Generates high-resolution vector PDF certificates using ReportLab, complete with custom color themes (Navy/Gold, Emerald, Burgundy, Slate), custom header titles (*Certificate of Completion*, *Certificate of Achievement*, etc.), issuer details, issue dates, and unique verification codes.
- **Certificate Retrieval & Verification**:
  - Visual inline PDF preview without forcing auto-downloads
  - Individual PDF Certificate file download
  - Bulk ZIP archive download for all generated certificates in a batch
  - Public verification API endpoint & web portal to authenticate certificate validity by code

---

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entrypoint & static mounts
│   ├── config.py                 # Application settings & environment configuration
│   ├── database.py               # SQLAlchemy database session & engine management
│   ├── models.py                 # SQLAlchemy ORM models (GenerationJob, CertificateItem)
│   ├── schemas.py                # Pydantic data schemas for requests and responses
│   ├── static/
│   │   └── index.html            # Web Application Dashboard
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py             # Main API Router
│   │   └── endpoints/
│   │       ├── jobs.py           # Job submission, status tracking, bulk download
│   │       └── certificates.py   # Certificate metadata, preview, download & verification
│   └── services/
│       ├── __init__.py
│       ├── certificate_generator.py # ReportLab PDF layout & theme engine
│       ├── job_service.py        # Background processing worker & ZIP packager
│       └── validation_service.py # Recipient data validation rules
├── generated_certificates/       # File storage directory for generated PDFs & ZIPs
├── tests/                        # Automated Pytest test suite
│   ├── conftest.py
│   ├── test_jobs.py
│   ├── test_validation.py
│   ├── test_generator.py
│   └── test_certificates.py
├── pytest.ini
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Setup & Installation

### Prerequisites

- **Python 3.10+**
- `pip` package manager

### 1. Clone & Enter Project Directory

```bash
git clone <repository_url>
cd "Bulk certificate generation"
```

### 2. Create Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Application

Start the development server using `uvicorn`:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running:
- **Web Application Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Specs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Running Tests

Execute the automated test suite using `pytest`:

```bash
pytest
```

---

## API Usage Guide

### 1. Submit a Bulk Certificate Generation Request

**Endpoint:** `POST /api/v1/jobs`

**Request Body:**

```json
{
  "title": "Advanced Web Development Masterclass",
  "issuer_name": "Global Tech Institute",
  "issue_date": "2026-10-09",
  "template_type": "emerald_gold",
  "certificate_heading": "CERTIFICATE OF COMPLETION",
  "recipients": [
    {
      "recipient_name": "Alice Johnson",
      "recipient_email": "alice@example.com",
      "custom_attributes": {
        "score": "98%",
        "grade": "A+",
        "hours": "40 Hours"
      }
    },
    {
      "recipient_name": "Bob Smith",
      "recipient_email": "bob@example.com",
      "custom_attributes": {
        "score": "88%",
        "grade": "B+"
      }
    }
  ]
}
```

---

## Important Implementation & Design Decisions

### 1. Technology Selection
- **FastAPI**: Provides asynchronous Request-Response handling, background tasks, low memory overhead, and built-in OpenAPI schema generation.
- **SQLAlchemy ORM**: Database layer supporting SQLite for zero-setup execution and PostgreSQL/MySQL for production deployments via `DATABASE_URL`.
- **ReportLab**: High-resolution vector PDF generator for rendering certificates with precision geometry.

### 2. Asynchronous Bulk Processing Architecture
Offloads PDF rendering to background worker threads so batch requests return `202 Accepted` immediately without blocking HTTP connection handlers.

### 3. Recipient Failure Isolation
Processing pipeline validates each participant record independently. Invalid rows transition to `FAILED` with error descriptions, allowing valid records in the same batch to complete successfully.

### 4. Verification & Security
Generates unique verification codes (`CERT-XXXXXXXX`) and provides a public verification endpoint/portal (`GET /api/v1/certificates/verify/{code}`) to confirm certificate authenticity.
