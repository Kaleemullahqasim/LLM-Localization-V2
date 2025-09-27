# Rule-Anchored Localization QA System - Backend

This is the backend API for the Rule-Anchored Localization QA System MVP.

## Quick Start

1. **Make sure LM Studio is running** with the required models:
   - Chat: `qwen/qwen3-1.7b` on `http://localhost:1234`
   - Embeddings: `text-embedding-qwen3-embedding-8b` on `http://127.0.0.1:1234`

2. **Run the startup script**:
   ```bash
   cd backend
   python start.py
   ```

   This will:
   - Create a virtual environment
   - Install dependencies
   - Create necessary data directories
   - Start the FastAPI server on http://localhost:8000

## Manual Setup (Alternative)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create data directories
mkdir -p data/{uploads,knowledge_bases,evaluations,embeddings,feedback}

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Document Ingestion
- `POST /api/upload-document` - Upload and process style guide
- `GET /api/knowledge-bases` - List available knowledge bases

### Evaluation
- `POST /api/evaluate` - Evaluate a translation
- `GET /api/evaluation/{job_id}` - Get evaluation results

### Review & Override
- `POST /api/review/override` - Override a finding

### Utilities
- `GET /api/rules/search` - Search rules by text
- `GET /api/stats` - System statistics
- `GET /` - Health check

## Core Components

### Data Models (`app/models/`)
- Rule, Finding, ScoreReport, FeedbackEvent
- Request/Response models for API

### Services (`app/services/`)
- **DocumentIngestionService**: Style guide → Knowledge base
- **LMStudioClient**: LLM integration (chat + embeddings)
- **EmbeddingService**: Vector search for rules
- **EvaluationEngine**: Main evaluation pipeline
- **DeterministicValidators**: Mechanical rule checks
- **ReviewService**: Handle reviewer overrides

### API (`app/main.py`)
- FastAPI application with all endpoints
- CORS enabled for frontend integration

## Testing the MVP

1. **Upload a style guide**:
   ```bash
   curl -X POST "http://localhost:8000/api/upload-document" \
        -F "file=@your_style_guide.docx" \
        -F "locale=zh-CN"
   ```

2. **Evaluate a translation**:
   ```bash
   curl -X POST "http://localhost:8000/api/evaluate" \
        -H "Content-Type: application/json" \
        -d '{
          "source_text": "Hello world!",
          "target_text": "你好世界!",
          "locale": "zh-CN"
        }'
   ```

3. **Check API documentation**: http://localhost:8000/docs

## Architecture

```
FastAPI Backend
├── Document Ingestion (DOCX/PDF/HTML/MD → KB)
├── Deterministic Validators (Punctuation, Placeholders, Dates)
├── LLM Evaluation (Retrieved rules → Findings)
├── Scoring Engine (Findings → Score with explanations)
└── Review System (Override findings, recalculate scores)
```

## Data Flow

1. **Ingestion**: Document → LLM extracts rules → Knowledge Base (JSON + CSV)
2. **Evaluation**: Source + Target → Deterministic checks + LLM evaluation → ScoreReport
3. **Review**: Reviewer overrides → FeedbackEvents → Updated scores

## Configuration

Edit `.env` file to configure:
- LM Studio endpoints and models
- Scoring parameters (severity multipliers, weights)
- File upload limits

## Acceptance Tests

The system should:
- ✅ Extract ≥30 rules from Shopify zh-CN guide
- ✅ Flag half-width punctuation in Chinese (！vs !)
- ✅ Detect placeholder violations ({name} modified)
- ✅ Catch date format issues (2025-09-01 vs 2025年9月1日)
- ✅ Generate ScoreReport with citations
- ✅ Allow reviewer overrides with score recalculation
- ✅ Produce identical results with same KB version