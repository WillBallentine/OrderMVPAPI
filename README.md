# Order MVP API

A production-ready REST API and React frontend for managing patient orders. Upload PDF documents — scanned faxes or text-based — to automatically extract structured patient data using OCR. No LLM required.

---

## Features

### API
- **Order CRUD** — create, read, update, and delete individual patient orders
- **Batch ingestion** — create up to 100 orders in a single atomic request
- **PDF extraction** — upload a PDF and extract patient first name, last name, and date of birth automatically
  - Text-based PDFs: pdfplumber (fast, sub-second)
  - Scanned/image PDFs: PyMuPDF + Tesseract OCR fallback with confidence scoring
- **Two document workflows** — extract-and-review (two steps) or extract-and-save (one step)
- **Authentication** — dual-mode: JWT bearer tokens for users, API key for service-to-service calls
- **User management** — register/login endpoints, role-based access control (admin/user)
- **Activity logging** — every request recorded to the database with method, path, status, and duration
- **Rate limiting** — 100 requests/minute per IP
- **Async OCR** — PDF extraction runs in a thread pool executor; the event loop is never blocked
- **Request validation** — Pydantic v2 validators on all inputs (name characters, password length, username format)
- **Docker** — single-command local setup with persistent SQLite volume

### Frontend (React)
- **Orders page** — full orders table with inline edit panel
- **Single PDF upload** — drag-and-drop, extract, review/edit extracted fields, save as order
- **Batch PDF upload** — select multiple PDFs, concurrent extraction with per-file progress, inline field editing, one-click batch save
- **Activity log** — live feed of all API activity with status code color coding
- **Auth flow** — register/login with JWT stored in localStorage, auto-redirect on token expiry

---

## Tech Stack

| Layer | Technologies |
|---|---|
| API | Python 3.12+, FastAPI, Uvicorn |
| Database | SQLAlchemy, SQLite (WAL mode) |
| PDF | pdfplumber, PyMuPDF, Tesseract OCR |
| Auth | python-jose (JWT), bcrypt |
| Rate limiting | slowapi |
| Tests | pytest, 123 tests, 95% coverage |
| Frontend | React 18, Vite, Tailwind CSS, React Router, Axios |
| Deployment | Render (API), Docker |

---

## Quickstart

### API — Local (Python)

```bash
# 1. Install Tesseract (required for scanned PDF support)
# macOS:   brew install tesseract
# Ubuntu:  apt-get install tesseract-ocr
# Windows: winget install UB-Mannheim.TesseractOCR

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — set API_KEY and SECRET_KEY to strong random values

# 4. Start the server
uvicorn app.main:app --reload
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### API — Docker

```bash
docker compose up --build
```

SQLite database is persisted in a named Docker volume (`db_data`).

### Frontend — Local

```bash
cd OrderMVPUI
npm install
# Set VITE_API_URL in .env (defaults to http://localhost:8000/api/v1)
npm run dev
```

Frontend: [http://localhost:5173](http://localhost:5173)

---

## Environment Variables

### API (`OrderMVPAPI/.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./orders.db` | SQLAlchemy connection string |
| `API_KEY` | `dev-api-key-change-in-production` | Service-to-service API key |
| `SECRET_KEY` | `change-this-secret-key-in-production` | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT token expiry |
| `MAX_UPLOAD_SIZE_MB` | `10` | Maximum PDF upload size |
| `RATE_LIMIT_REQUESTS` | `100` | Requests allowed per period |
| `RATE_LIMIT_PERIOD` | `minute` | Rate limit window |
| `ALLOWED_ORIGINS` | `["*"]` | CORS allowed origins |
| `DEBUG` | `false` | Enable debug mode |

Generate strong secrets:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Frontend (`OrderMVPUI/.env`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000/api/v1` | Base URL of the API |

---

## API Reference

All endpoints prefixed with `/api/v1`. Interactive docs at `/docs`.

### Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | None | Register a new user |
| `POST` | `/auth/login` | None | Login, receive JWT |

### Orders

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/orders/` | Required | Create a single order |
| `POST` | `/orders/batch` | Required | Create up to 100 orders atomically |
| `GET` | `/orders/` | Required | List orders (paginated) |
| `GET` | `/orders/{id}` | Required | Get order by ID |
| `PUT` | `/orders/{id}` | Required | Update order fields |
| `DELETE` | `/orders/{id}` | Required | Delete order |

### Documents

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/documents/extract` | Required | Extract patient info from PDF — does **not** save |
| `POST` | `/documents/order` | Required | Extract from PDF and create order in one step |

**Two document workflows:**

*Review before saving (two steps):*
1. `POST /documents/extract` → receive extracted fields
2. Verify or correct the values
3. `POST /orders/` → create the order with confirmed data

*Direct save (one step):*
1. `POST /documents/order` → order created immediately; returns 422 if any required field cannot be extracted

### Users

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/users/me` | JWT only | Get the current authenticated user |
| `GET` | `/users/` | Admin only | List all users |

### Activity Logs

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/activity-logs/` | Required | List activity logs (paginated, newest first) |

### Health

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Health check |

### Authentication

**JWT (user login):**
```
Authorization: Bearer <token>
```

**API key (service-to-service):**
```
X-API-Key: <key>
```

---

## Postman Collection

A full Postman collection is included at `Order MVP API.postman_collection.json`. Import it directly into Postman:

1. Open Postman → **Import** → select the `.json` file
2. Set the `baseUrl` collection variable to your API base URL:
   - Local: `http://localhost:8000`
   - Render: `https://orderapi-mvp.onrender.com`
3. Register a user via **Auth → Register User**, then login via **Auth → Login** to get a token
4. In Postman, go to the collection → **Authorization** tab → set type to **Bearer Token** and paste the token

Alternatively, import the OpenAPI spec directly from the running API:
```
https://orderapi-mvp.onrender.com/openapi.json
```

---

## Running Tests

```bash
# All tests excluding slow OCR tests
pytest tests/ --ignore=tests/unit/test_pdf_formats.py

# Full suite including OCR (requires Tesseract)
pytest tests/

# With coverage report
pytest tests/ --cov=app
```

123 tests, 95% coverage across unit and integration suites.

---

## Deployment (Render)

The included `render.yaml` configures a Render web service:
- Tesseract OCR installed at build time via `apt-get`
- `API_KEY` and `SECRET_KEY` auto-generated by Render (`generateValue: true`)
- All other environment variables set with sensible defaults

Push to a connected GitHub repo — Render picks up `render.yaml` automatically. No manual environment configuration needed.

> **Note:** Render's free tier uses ephemeral storage. The SQLite database is wiped on each restart. For persistent storage, set `DATABASE_URL` to a managed PostgreSQL connection string.

---

## Scalability Notes

This MVP uses SQLite and in-memory rate limiting, appropriate for a single-process deployment. Production path:

- **Database** — swap `DATABASE_URL` for PostgreSQL; no code changes required (SQLAlchemy abstraction)
- **Rate limiting** — configure slowapi with a Redis backend to share state across workers
- **PDF caching** — cache extraction results by SHA-256 of file bytes to skip re-OCR on duplicate uploads
- **Workers** — run multiple Uvicorn workers behind a reverse proxy (nginx, Render's load balancer)
- **OCR performance** — offload Tesseract to a dedicated service or use a managed OCR API for sub-second latency at scale
