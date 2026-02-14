# Clarity Couple Backend

Backend API for Clarity Couple, powered by FastAPI and Gemini 3.0 Flash.

## Features
- **RAG (Retrieval Augmented Generation)**: Uses `pgvector` and Gemini 3.0 Flash for context-aware chat.
- **Analysis Modes**: Quick Reply, Conflict Analysis, Pattern Detection, Specific Question.
- **Vector Database**: PostgreSQL with `pgvector` extension.
- **Multi-Key Management**: Intelligent round-robin allocation of 40 Gemini API keys.

## Setup

### 1. Environment
Copy `.env.example` to `.env` and fill in your Gemini API keys.
```bash
cp .env.example .env
```

### 2. Docker
Run with Docker Compose:
```bash
docker-compose up -d --build
```
The API will be available at `http://localhost:8000`.

### 3. Local Dev (Optional)
```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

## Endpoints
- `GET /api/v1/health`: Health check
- `POST /api/v1/chat`: Send message (RAG)
- `POST /api/v1/analysis/{mode}`: Analyze chat history
