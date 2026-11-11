# main.py
import os
import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, SecretStr
import re
from langchain_groq import ChatGroq
import sentry_sdk

if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        send_default_pii=False,
        traces_sample_rate=1.0,
    )

if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ.setdefault("LANGCHAIN_PROJECT", "multi-agent-code-reviewer")

app = FastAPI()

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Fixed: Added https://cdn.jsdelivr.net to script-src so marked.js loads without CSP blocks
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline';"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://multiagentapp-7zwv.onrender.com", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_frontend():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(status_code=404, content={"error": "index.html not found in frontend directory"})

@app.get("/sentry-debug")
async def trigger_error():
    if os.getenv("RENDER") or os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=404, detail="Not found")
    try:
        raise Exception("Manual Sentry Test Triggered")
    except Exception as e:
        if os.getenv("SENTRY_DSN"):
            sentry_sdk.capture_exception(e)
        return {"status": "success", "message": "Test exception handled."}

class RepoRequest(BaseModel):
    repo_url: str
    groq_api_key: Optional[SecretStr] = None

from backend.app.agent_crew import app_graph

def evaluate_review_quality(code_context: str, review_text: Optional[str], api_key: str) -> dict:
    safe_review = review_text if review_text else ""
    
    has_headers = bool(re.search(r'^#{1,3}\s+', safe_review, re.MULTILINE))
    has_tables = "|" in safe_review
    structural_score = 1.0 if (has_headers or has_tables) else 0.0

    llm_score = 3  
    if api_key and safe_review.strip():
        try:
            eval_llm = ChatGroq(
                api_key=api_key,
                model_name="openai/gpt-oss-20b",
                temperature=0.1
            )
            prompt = f"""You are a strict code review auditor. Evaluate the following AI-generated code review based on the repository context.\n\nRepository Context:\n{code_context[:5000]}\n\nAI Code Review:\n{safe_review[:3000]}\n\nTask: Rate the actionability and factual grounding on a scale of 1 to 5.\nOutput format: Return ONLY a single integer score from 1 to 5."""
            res = eval_llm.invoke([("user", prompt)])
            raw_content = res.content.strip() if res and res.content else ""
            match = re.search(r'([1-5])', raw_content)
            if match:
                llm_score = int(match.group(1))
        except Exception:
            pass

    return {
        "structural_compliance": structural_score,
        "llm_quality_judge": llm_score
    }

@app.post("/analyze")
def analyze_repo(request: RepoRequest):
    try:
        clean_url = request.repo_url.strip()
        if not re.match(r"^https://github\.com/[\w-]+/[\w.-]+(\.git)?/?(\?.*)?(#.*)?$", clean_url):
            raise HTTPException(status_code=400, detail="Invalid GitHub repository URL format.")

        raw_user_key = request.groq_api_key.get_secret_value().strip() if request.groq_api_key else None
        if raw_user_key == "":
            raw_user_key = None

        if raw_user_key and not raw_user_key.startswith("gsk_"):
            raise HTTPException(status_code=400, detail="Invalid Groq API key format. Keys must start with 'gsk_'.")

        active_api_key = raw_user_key or os.getenv("GROQ_API_KEY")
        if not active_api_key:
            raise HTTPException(status_code=400, detail="No Groq API key provided. Please pass a valid BYOK key.")

        initial_state = {
            "repo_url": clean_url,
            "api_key": active_api_key,
            "assembled_context": "",
            "security_findings": "",
            "bug_findings": "",
            "final_review": ""
        }
        
        final_state = app_graph.invoke(initial_state)
        
        if not isinstance(final_state, dict) or "final_review" not in final_state or "assembled_context" not in final_state:
            raise HTTPException(status_code=500, detail="Agent graph execution returned malformed state output.")

        analysis_result = final_state["final_review"]
        assembled_code_context = final_state["assembled_context"]

        eval_results = evaluate_review_quality(
            code_context=assembled_code_context,
            review_text=analysis_result,
            api_key=active_api_key
        )

        return JSONResponse(content={
            "markdown": analysis_result,
            "evaluations": eval_results
        })
        
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")
