# Technical Guide: Rule-Anchored Localization QA System

## 🎯 System Overview

This system uses **AI-powered rule extraction** and **hybrid evaluation** to provide explainable, reproducible translation quality assessment. Here's how each component works:

## 🧠 1. LLM Integration & Rule Extraction

### How It Works
The system uses **Large Language Models** to automatically extract translation quality rules from style guide documents:

```
Style Guide Document → Document Parser → Rule Cue Detection → LLM Normalization → Structured Rules
```

### LM Studio Integration
Located in: `backend/app/services/lm_studio_client.py`

```python
# Chat completion for rule extraction
async def extract_rules_from_text(self, document_snippet: str, section_path: List[str]):
    rule_schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "extracted_rules",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "rules": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "rule_text": {"type": "string"},
                                "micro_class": {"type": "string"},
                                "examples_pos": {"type": "array"},
                                "examples_neg": {"type": "array"},
                                "severity_cue": {"type": "string"},
                                "regex_candidate": {"type": "boolean"}
                            }
                        }
                    }
                }
            }
        }
    }
```

### Rule Extraction Process
1. **Document Processing**: Converts DOCX/PDF/HTML/MD to structured markdown
2. **Cue Detection**: Finds rule indicators like "must", "never", "should", "avoid"
3. **LLM Processing**: Uses structured output to extract atomic, testable rules
4. **Classification**: Auto-categorizes rules by macro class (Punctuation, Terminology, etc.)
5. **Scoring Assignment**: Assigns default severity and weights based on linguistic cues

## 🔍 2. Embedding Service & Semantic Search

### Vector Embeddings
Located in: `backend/app/services/embedding_service.py`

The system creates vector embeddings for all extracted rules to enable semantic search:

```python
async def index_rules(self, rules: List[Rule]):
    # Combine rule text with examples for better retrieval
    texts = []
    for rule in rules:
        text = rule.rule_text
        if rule.examples_pos:
            text += " Examples: " + " ".join(rule.examples_pos)
        if rule.examples_neg:
            text += " Avoid: " + " ".join(rule.examples_neg)
        texts.append(text)
    
    # Get embeddings from LM Studio
    embeddings = await self.lm_client.get_embeddings(texts)
```

### Hybrid Search
The system combines **semantic similarity** with **keyword matching**:

```python
async def hybrid_search(self, query_text: str, top_k: int = 10):
    # Semantic similarity (embedding-based)
    semantic_sim = cosine_similarity(query_embedding, rule_embedding)
    
    # Keyword similarity (simple keyword matching)
    query_words = set(query_text.lower().split())
    rule_words = set(rule_text.lower().split())
    keyword_sim = len(query_words & rule_words) / max(len(query_words), 1)
    
    # Combined score (weighted)
    combined_score = 0.7 * semantic_sim + 0.3 * keyword_sim
```

## ⚙️ 3. Evaluation Engine Architecture

### Hybrid Evaluation Pipeline
Located in: `backend/app/services/evaluation_engine.py`

The evaluation combines **deterministic checks** with **AI analysis**:

```
Translation Input → Deterministic Validators → Rule Retrieval → LLM Analysis → Scoring → Report
```

### Step-by-Step Process

#### Step 1: Deterministic Validation
Fast, regex-based checks for mechanical rules:
- **Punctuation Width**: Half-width vs full-width in Chinese (！vs !)
- **Placeholder Preservation**: {name}, [tag], <element> consistency
- **Date Format**: ISO vs localized format (2025-09-01 vs 2025年9月1日)
- **Line Break Preservation**: Formatting consistency

#### Step 2: Semantic Rule Retrieval
```python
# Hybrid retrieval for LLM evaluation
query_text = f"Source: {source_text}\nTarget: {target_text}"
candidate_rules = await self.embedding_service.hybrid_search(
    query_text=query_text,
    top_k=20,
    locale=locale
)
```

#### Step 3: LLM Analysis
Uses structured output to evaluate translations:

```python
findings_schema = {
    "type": "json_schema",
    "json_schema": {
        "name": "evaluation_findings",
        "schema": {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "items": {
                        "properties": {
                            "rule_id": {"type": "string"},
                            "severity": {"enum": ["Minor", "Major", "Critical"]},
                            "justification": {"type": "string"},
                            "highlighted_text": {"type": "string"},
                            "span_start": {"type": "integer"},
                            "span_end": {"type": "integer"}
                        }
                    }
                }
            }
        }
    }
}
```

#### Step 4: Scoring Engine
```python
# Calculate weighted score with severity multipliers
severity_multipliers = {
    Severity.MINOR: 1,
    Severity.MAJOR: 2,
    Severity.CRITICAL: 3
}

base_score = 100
for finding in findings:
    penalty = rule.default_weight * severity_multipliers[finding.severity]
    total_penalty += penalty

# Apply category caps (e.g., max -30 for style/punctuation)
final_score = max(0, base_score - total_penalty)
```

## 📊 4. Rule Classification & Scoring

### Macro Classes
Rules are automatically classified into categories:

- **Accuracy**: Meaning preservation, correctness
- **Terminology**: Glossary terms, brand names, DNT lists
- **Mechanics**: Formatting, placeholders, technical elements
- **Punctuation**: Character width, punctuation rules
- **Style**: Tone, register, stylistic preferences
- **Legal**: Compliance, regulatory requirements
- **Standards**: ISO standards, industry specifications

### Default Weights by Category
```python
default_weights = {
    MacroClass.ACCURACY: 5,      # High impact
    MacroClass.TERMINOLOGY: 4,   # High impact
    MacroClass.MECHANICS: 3,     # Medium impact
    MacroClass.PUNCTUATION: 2,   # Lower impact
    MacroClass.STYLE: 1,         # Lowest impact
    MacroClass.LEGAL: 6,         # Highest impact
    MacroClass.STANDARDS: 3      # Medium impact
}
```

### Severity Determination
Based on linguistic cues in the original style guide:
- **"must", "never", "required", "mandatory"** → Major
- **"should", "recommended", "preferred"** → Minor
- **"avoid", "discouraged"** → Minor

## 🔧 5. LM Studio Configuration

### Required Models
1. **Chat Model**: `qwen/qwen3-1.7b`
   - Used for: Rule extraction, translation evaluation
   - Endpoint: `http://localhost:1234/v1/chat/completions`

2. **Embedding Model**: `text-embedding-qwen3-embedding-8b`
   - Used for: Rule indexing, semantic search
   - Endpoint: `http://127.0.0.1:1234/v1/embeddings`

### Structured Output Usage
The system uses JSON Schema to ensure consistent AI responses:

```python
# For rule extraction
response = await self.chat_completion(
    messages=messages,
    temperature=0.1,
    response_format=rule_schema
)

# For evaluation
response = await self.chat_completion(
    messages=messages,
    temperature=0.1,
    response_format=findings_schema
)
```

## 📈 6. Score Calculation Details

### Base Scoring Formula
```
Final Score = 100 - Total Penalties (with caps)

Where:
Penalty = Rule Weight × Severity Multiplier

Severity Multipliers:
- Minor: 1x
- Major: 2x  
- Critical: 3x
```

### Category Caps
To prevent any single category from dominating:
```python
# Style/Punctuation cap (max -30 points)
style_penalty = by_macro.get('Style', {}).get('penalty', 0)
punctuation_penalty = by_macro.get('Punctuation', {}).get('penalty', 0)

if style_penalty + punctuation_penalty > 30:
    excess = (style_penalty + punctuation_penalty) - 30
    total_penalty -= excess
```

### Score Bands
- **≥95**: Excellent
- **90-94**: Good  
- **80-89**: Fair
- **<80**: Needs Revision

## 🔄 7. Review & Override System

### Human Oversight
Located in: `backend/app/services/review_service.py`

Reviewers can override AI decisions:
- **Accept**: Confirm the finding is correct
- **Change Severity**: Adjust from Minor/Major/Critical
- **Dismiss**: Remove the finding entirely
- **Reclassify**: Change the rule category

### Feedback Events
All overrides are logged for audit trails:
```python
feedback_event = FeedbackEvent(
    event_id=str(uuid.uuid4()),
    segment_id=finding.segment_id,
    rule_id=finding.rule_id,
    action=request.action,
    old_value=old_severity,
    new_value=new_severity,
    reason=request.reason,
    actor=request.reviewer
)
```

## 🗂️ 8. Data Storage & Versioning

### Knowledge Base Storage
- **Format**: JSON + CSV
- **Location**: `backend/data/knowledge_bases/`
- **Naming**: `kb_{version}_{locale}.json`
- **Content**: Full rule details, metadata, citations

### Evaluation Results
- **Format**: JSON
- **Location**: `backend/data/evaluations/`
- **Naming**: `eval_{job_id}.json`
- **Content**: Complete score report, findings, metadata

### Version Control
Every evaluation is stamped with:
- `kb_version`: Knowledge base version used
- `rubric_version`: Scoring rubric version
- `model_prompt_version`: LLM prompt version

This ensures **reproducible results**: Same input + same versions = identical scores.

## 🚀 9. Frontend Architecture

### Modern React Interface
- **Tabbed Navigation**: Evaluate, Upload, Knowledge Bases, Help
- **Real-time Updates**: Live score recalculation on overrides
- **Professional UI**: Customer-ready design with responsive layout
- **File Upload**: Drag-and-drop style guide upload
- **Detailed Reporting**: Score breakdowns, highlighted text, rule citations

### Key Features
1. **Translation Evaluation Tab**: Input source/target, select KB, get scored results
2. **Upload Tab**: Upload DOCX/PDF/HTML/MD files to create knowledge bases
3. **Knowledge Bases Tab**: Manage existing KBs, view rule counts, switch between versions
4. **Help Tab**: Comprehensive explanation of how the system works

## 🔍 10. Troubleshooting

### Common Issues

#### LM Studio Connection Errors
```bash
# Check if LM Studio is running
curl http://localhost:1234/v1/models

# Check embedding endpoint
curl -X POST http://127.0.0.1:1234/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"input": ["test"], "model": "text-embedding-qwen3-embedding-8b"}'
```

#### Missing Dependencies
```bash
# Backend
cd backend && source venv/bin/activate && pip install -r requirements.txt

# Frontend  
cd frontend && npm install
```

#### Port Conflicts
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- LM Studio: `http://localhost:1234`

## 📝 11. API Documentation

### Key Endpoints

#### Upload Document
```http
POST /api/upload-document
Content-Type: multipart/form-data

file: [DOCX/PDF/HTML/MD file]
locale: zh-CN
```

#### Evaluate Translation
```http
POST /api/evaluate
Content-Type: application/json

{
  "source_text": "Welcome to Shopify!",
  "target_text": "欢迎使用Shopify!",
  "locale": "zh-CN", 
  "kb_version": "2025.09.27-1609"
}
```

#### List Knowledge Bases
```http
GET /api/knowledge-bases
```

#### Override Finding
```http
POST /api/review/override
Content-Type: application/json

{
  "finding_id": "seg_12345",
  "action": "change_severity",
  "new_severity": "Minor",
  "reason": "Context allows this usage",
  "reviewer": "reviewer@company.com"
}
```

## 🎯 12. Next Steps & Enhancements

### Immediate Improvements
1. **Tool Calling**: Implement LM Studio function calling for deterministic checks
2. **Advanced RAG**: Improve rule retrieval with better chunking strategies
3. **Multi-model Support**: Add support for different LLM providers
4. **Batch Processing**: Handle multiple translations at once

### Future Features
1. **Active Learning**: Use feedback to improve rule extraction
2. **Rule Governance**: Workflow for approving/rejecting extracted rules
3. **Analytics Dashboard**: Trends, patterns, quality metrics over time
4. **CAT Tool Integration**: Plugin for translation memory systems

---

This system represents a **complete AI-powered localization QA pipeline** that scales human expertise while maintaining transparency and control. Every decision is explainable, every result is reproducible, and every rule is traceable back to its source.
