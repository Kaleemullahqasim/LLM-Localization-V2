# Rule-Anchored Localization QA System - MVP

> **An AI-powered system that automatically extracts translation quality rules from style guides and provides explainable, reproducible scoring for translations.**

## 🚀 Quick Start

### Prerequisites
1. **LM Studio running locally** with these models:
   - **Chat**: `qwen/qwen3-1.7b` on `http://localhost:1234`
   - **Embeddings**: `text-embedding-qwen3-embedding-8b` on `http://127.0.0.1:1234`

### Start the Backend
```bash
cd backend
python start.py
```

This automatically:
- Creates virtual environment
- Installs dependencies  
- Creates data directories
- Starts FastAPI server on http://localhost:8000

### Test the System
```bash
cd backend
python test_mvp.py
```

## 🏗️ System Overview

### What It Does
1. **📄 Document Ingestion**: Upload style guides (DOCX/PDF/HTML/MD) → AI extracts rules
2. **🔍 Translation Evaluation**: Submit translations → Get scored against rules with explanations
3. **👥 Human Review**: Reviewers can override AI findings and see score updates in real-time

### Key Features
- **🤖 LLM-Powered Rule Extraction**: Automatically creates rule knowledge bases from documents
- **⚡ Deterministic + AI Validation**: Fast mechanical checks + semantic LLM evaluation  
- **📊 Explainable Scoring**: Every deduction tied to specific rule with citation
- **🔄 Reproducible Results**: Same input + version = identical scores
- **👨‍💼 Human Oversight**: Reviewers maintain control with override capabilities

## 🛠️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Style Guide   │───▶│  Knowledge Base  │───▶│   Evaluation    │
│  (DOCX/PDF/MD)  │    │  (Rules + Meta)  │    │  (Score Report) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▲                        ▲
                         ┌──────┴──────┐        ┌────────┴────────┐
                         │ LLM Extract │        │ Deterministic + │
                         │    Rules    │        │  LLM Evaluate   │
                         └─────────────┘        └─────────────────┘
```

### Core Pipeline
1. **Ingestion**: Document → LLM → Atomic Rules → Knowledge Base (JSON + CSV)
2. **Evaluation**: Source + Target → Validators + Retrieval + LLM → Findings → Score
3. **Review**: Human Override → Feedback Events → Updated Score

## 📁 Project Structure

```
├── spec/
│   ├── PRD.md              # Product Requirements Document
│   └── tasks.md            # Implementation tasks
├── backend/
│   ├── app/
│   │   ├── models/         # Data models (Rule, Finding, ScoreReport)
│   │   ├── services/       # Core business logic
│   │   └── main.py         # FastAPI application
│   ├── data/               # Generated data (KBs, evaluations)
│   ├── start.py            # One-command startup
│   └── test_mvp.py         # System validation tests
└── README.md               # This file
```

## 🔧 API Endpoints

### Document Management
- `POST /api/upload-document` - Upload style guide, create KB
- `GET /api/knowledge-bases` - List available knowledge bases

### Evaluation  
- `POST /api/evaluate` - Evaluate translation against KB
- `GET /api/evaluation/{job_id}` - Get detailed results

### Review & Override
- `POST /api/review/override` - Override finding, recalculate score
- `GET /api/rules/search` - Search rules by text

### Utilities
- `GET /api/stats` - System statistics
- `GET /docs` - Interactive API documentation

## 🧪 Acceptance Tests

The MVP passes when:
- ✅ Upload Shopify zh-CN guide → ≥30 rules extracted
- ✅ Deterministic validators catch seeded violations:
  - Half-width punctuation in Chinese (! → ！)
  - Modified placeholders ({name} → {nome})  
  - Wrong date format (2025-09-01 → 2025年9月1日)
- ✅ ScoreReport shows findings with rule citations
- ✅ Reviewer can override severity, see live score update
- ✅ Same KB version → identical reproducible results

## 🎯 MVP Scope

### ✅ Included
- Document ingestion (DOCX/PDF/HTML/MD)
- Rule extraction via LLM with JSON schema
- 5 core deterministic validators  
- Hybrid rule retrieval (embeddings + keywords)
- LLM evaluation with structured output
- Scoring engine with severity multipliers
- Basic review interface via API
- Audit trail with feedback events

### 🚫 Out of Scope (V2+)
- Advanced UI/frontend
- Multi-language evaluation  
- CAT tool integration
- Analytics dashboards
- Global rubric updates
- Advanced category caps

## 🤝 Contributing

This is an MVP focused on proving the core concept. The system demonstrates:
1. **Automated rule extraction** from style guides
2. **Explainable scoring** with human oversight
3. **Reproducible results** with version control
4. **LLM integration** with local models (LM Studio)

## 🚦 Next Steps

1. **Test with your data**: Upload your style guide and test translations
2. **Frontend development**: Build React UI for easier review workflow  
3. **Performance optimization**: Improve rule retrieval and scoring speed
4. **Enterprise features**: User management, advanced analytics, integrations

---

**Built for**: Translation QA teams who want consistent, explainable, and improvable quality assessment that scales human expertise rather than replacing it.