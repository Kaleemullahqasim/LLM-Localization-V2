from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import shutil
import uuid
from typing import List, Optional
import uvicorn

from .config import config
from .models import (
    DocumentUploadRequest, EvaluationRequest, ReviewOverrideRequest,
    KnowledgeBase, ScoreReport, FeedbackEvent
)
from .services.document_ingestion import DocumentIngestionService
from .services.evaluation_engine import EvaluationEngine
from .services.review_service import ReviewService

# Initialize FastAPI app
app = FastAPI(
    title="Rule-Anchored Localization QA System",
    description="MVP system for automated translation quality assessment",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ingestion_service = DocumentIngestionService()
evaluation_engine = EvaluationEngine()
review_service = ReviewService()

# Ensure data directories exist
os.makedirs(os.path.join(config.DATA_DIR, "uploads"), exist_ok=True)
os.makedirs(os.path.join(config.DATA_DIR, "knowledge_bases"), exist_ok=True)
os.makedirs(os.path.join(config.DATA_DIR, "evaluations"), exist_ok=True)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Rule-Anchored Localization QA System API", "status": "running"}

@app.post("/api/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    locale: str = "zh-CN"
):
    """Upload and ingest a style guide document"""
    
    # Validate file type
    allowed_extensions = ['.docx', '.pdf', '.html', '.htm', '.md', '.markdown']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_path = os.path.join(config.DATA_DIR, "uploads", f"{file_id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Ingest document and create knowledge base
        kb = await ingestion_service.ingest_document(file_path, locale)
        
        return {
            "message": "Document uploaded and processed successfully",
            "kb_version": kb.kb_version,
            "rule_count": kb.rule_count,
            "locale": kb.locale,
            "filename": file.filename
        }
        
    except Exception as e:
        # Clean up file if processing failed
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.get("/api/knowledge-bases")
async def list_knowledge_bases():
    """List all available knowledge bases"""
    kb_dir = os.path.join(config.DATA_DIR, "knowledge_bases")
    
    if not os.path.exists(kb_dir):
        return {"knowledge_bases": []}
    
    kb_files = [f for f in os.listdir(kb_dir) if f.endswith('.json') and f.startswith('kb_')]
    
    knowledge_bases = []
    for kb_file in kb_files:
        try:
            import json
            with open(os.path.join(kb_dir, kb_file), 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
                
            knowledge_bases.append({
                "kb_version": kb_data.get("kb_version"),
                "locale": kb_data.get("locale"),
                "rule_count": kb_data.get("rule_count"),
                "source_document": kb_data.get("source_document"),
                "created_at": kb_data.get("created_at")
            })
        except Exception as e:
            print(f"Error reading KB file {kb_file}: {e}")
            continue
    
    return {"knowledge_bases": knowledge_bases}

@app.post("/api/evaluate")
async def evaluate_translation(request: EvaluationRequest):
    """Evaluate a translation against the knowledge base"""
    
    try:
        print(f"🔍 Starting evaluation - Source: {request.source_text[:50]}...")
        print(f"   Target: {request.target_text[:50]}...")
        print(f"   Locale: {request.locale}, KB Version: {request.kb_version}")
        
        # Run evaluation
        score_report = await evaluation_engine.evaluate(
            source_text=request.source_text,
            target_text=request.target_text,
            locale=request.locale,
            kb_version=request.kb_version
        )
        
        print(f"✅ Evaluation completed - Score: {score_report.final_score}")
        return score_report.model_dump()
        
    except Exception as e:
        print(f"❌ Evaluation error: {str(e)}")
        print(f"   Request data: {request.model_dump()}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error during evaluation: {str(e)}")

@app.get("/api/evaluations")
async def list_evaluations():
    """List all evaluations"""
    eval_dir = os.path.join(config.DATA_DIR, "evaluations")
    
    if not os.path.exists(eval_dir):
        return {"evaluations": []}
    
    eval_files = [f for f in os.listdir(eval_dir) if f.endswith('.json') and f.startswith('eval_')]
    
    evaluations = []
    for eval_file in eval_files:
        try:
            import json
            with open(os.path.join(eval_dir, eval_file), 'r', encoding='utf-8') as f:
                eval_data = json.load(f)
                evaluations.append(eval_data)
        except Exception as e:
            print(f"Error reading eval file {eval_file}: {e}")
            continue
    
    # Sort by created_at descending
    evaluations.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return {"evaluations": evaluations}

@app.get("/api/evaluation/{job_id}")
async def get_evaluation(job_id: str):
    """Get evaluation results by job ID"""
    
    eval_file = os.path.join(config.DATA_DIR, "evaluations", f"eval_{job_id}.json")
    
    if not os.path.exists(eval_file):
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    try:
        import json
        with open(eval_file, 'r', encoding='utf-8') as f:
            evaluation_data = json.load(f)
        
        return evaluation_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading evaluation: {str(e)}")

@app.post("/api/review/override")
async def override_finding(request: ReviewOverrideRequest):
    """Override a finding from the evaluation"""
    
    try:
        # Process the override
        feedback_event = await review_service.process_override(request)
        
        return {
            "message": "Override processed successfully",
            "feedback_event": feedback_event.model_dump()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing override: {str(e)}")

@app.get("/api/rules/search")
async def search_rules(
    query: str,
    locale: str = "zh-CN",
    kb_version: str = None,
    top_k: int = 10
):
    """Search rules by text query"""
    
    try:
        from .services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        
        results = await embedding_service.hybrid_search(
            query_text=query,
            top_k=top_k,
            locale=locale,
            kb_version=kb_version
        )
        
        # Format results for API response
        formatted_results = []
        for result in results:
            rule = result['rule']
            formatted_results.append({
                "rule_id": rule.rule_id,
                "rule_text": rule.rule_text,
                "macro_class": rule.macro_class.value,
                "micro_class": rule.micro_class,
                "severity": rule.default_severity.value,
                "weight": rule.default_weight,
                "score": result['score'],
                "examples_pos": rule.examples_pos,
                "examples_neg": rule.examples_neg
            })
        
        return {"results": formatted_results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching rules: {str(e)}")

@app.delete("/api/knowledge-bases/{kb_version}")
async def delete_knowledge_base(kb_version: str):
    """Delete a knowledge base"""
    
    kb_dir = os.path.join(config.DATA_DIR, "knowledge_bases")
    
    try:
        # Find and delete the KB file
        kb_file = f"kb_{kb_version}.json"
        csv_file = f"points_table_{kb_version}.csv"
        
        kb_files = [f for f in os.listdir(kb_dir) if f.startswith(f"kb_{kb_version}_")]
        csv_files = [f for f in os.listdir(kb_dir) if f.startswith(f"points_table_{kb_version}_")]
        
        if not kb_files:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Delete files
        for file in kb_files:
            os.remove(os.path.join(kb_dir, file))
        for file in csv_files:
            os.remove(os.path.join(kb_dir, file))
        
        return {"message": f"Knowledge base {kb_version} deleted successfully"}
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting knowledge base: {str(e)}")

@app.get("/api/stats")
async def get_system_stats():
    """Get system statistics"""
    
    kb_dir = os.path.join(config.DATA_DIR, "knowledge_bases")
    eval_dir = os.path.join(config.DATA_DIR, "evaluations")
    
    stats = {
        "knowledge_bases": 0,
        "total_rules": 0,
        "evaluations": 0,
        "supported_locales": []
    }
    
    try:
        # Count knowledge bases
        if os.path.exists(kb_dir):
            kb_files = [f for f in os.listdir(kb_dir) if f.endswith('.json')]
            stats["knowledge_bases"] = len(kb_files)
            
            # Count total rules and extract locales
            import json
            locales = set()
            total_rules = 0
            
            for kb_file in kb_files:
                try:
                    with open(os.path.join(kb_dir, kb_file), 'r', encoding='utf-8') as f:
                        kb_data = json.load(f)
                        total_rules += kb_data.get("rule_count", 0)
                        locales.add(kb_data.get("locale", "unknown"))
                except:
                    continue
            
            stats["total_rules"] = total_rules
            stats["supported_locales"] = list(locales)
        
        # Count evaluations
        if os.path.exists(eval_dir):
            eval_files = [f for f in os.listdir(eval_dir) if f.endswith('.json')]
            stats["evaluations"] = len(eval_files)
    
    except Exception as e:
        print(f"Error getting stats: {e}")
    
    return stats

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)