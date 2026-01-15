# AI-Powered Document Verification Platform

Lightweight, governance-oriented document verification demo:
- **Backend**: FastAPI (Python)
- **Frontend**: Streamlit
- **DB**: Postgres (Docker Compose)
- **RAG**: sentence-transformers + FAISS (local)
- **OCR**: pytesseract + OpenCV
- **Fraud**: imagehash perceptual hashing

> This is a demonstration-ready codebase. Replace placeholders and harden for production (auth, encryption, secrets management, monitoring).

---

## Quick start (development)

1. Copy `.env.example` to `.env` and edit values:
   ```bash
   cp .env.example .env
   ```

2. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

3. Backend API will be at `http://localhost:8000`.
4. Streamlit UI will be at `http://localhost:8501`.

### Local (without Docker)

1. Install Python 3.10+ and dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Start Postgres (Docker recommended):
   ```bash
   docker-compose up postgres -d
   ```

3. Create uploads directory:
   ```bash
   mkdir uploads
   ```

4. Run DB init:
   ```bash
   python scripts/init_db.py
   ```

5. Start backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. Start frontend (in a new terminal):
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

---

## Architecture overview

- **Upload flow**: Streamlit uploads file → backend `/upload` → file saved → BackgroundTasks triggers verification pipeline → job status stored → results available via `/status`.
- **Verification pipeline**: preprocess → OCR → classification → extraction → signature/stamp detection → fraud checks → RAG context indexing.
- **RAG chatbot**: local FAISS index built from `samples/sample_docs`; embeddings via `sentence-transformers/all-MiniLM-L6-v2`.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/api/upload` | Upload document for verification |
| GET | `/api/status/{job_id}` | Get verification job status |
| POST | `/api/correct/{job_id}` | Submit field corrections |
| POST | `/api/chat` | RAG chatbot query |

---

## Notes & TODOs

- **OCR**: Tesseract is used; for better regional accuracy, integrate commercial OCR or fine-tune models.
- **Scaling**: BackgroundTasks are fine for demo. For production, use Celery/RQ with Redis.
- **Security**: Add authentication, RBAC, HTTPS, encryption at rest, and secrets manager.
- **LLM**: The generator is a placeholder. Replace with your LLM API in `backend/app/services/rag.py`.
