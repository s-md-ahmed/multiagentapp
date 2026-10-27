# main.py
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, SecretStr

import sentry_sdk
from langsmith import Client, traceable
from langsmith.run_helpers import get_current_run_tree


from .agent_crew import app_graph

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=False,
    traces_sample_rate=1.0,
)

if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ.setdefault("LANGCHAIN_PROJECT", "multi-agent-code-reviewer")

app = FastAPI()
ls_client = Client()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://multiagentapp-7zwv.onrender.com", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
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
    return {"error": "index.html not found in frontend directory"}

@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0

class RepoRequest(BaseModel):
    repo_url: str
    groq_api_key: Optional[SecretStr] = None


@app.post("/analyze")
def analyze_repo(request: RepoRequest, background_tasks: BackgroundTasks):
    """Core production endpoint. Executes multi-agent review, auto-streams traces, and triggers async evals."""
    try:
        print(f"--- [DEBUG] Received request for repo: {request.repo_url} ---")
        
        raw_user_key = request.groq_api_key.get_secret_value() if request.groq_api_key else None
        active_api_key = raw_user_key or os.getenv("GROQ_API_KEY")
        if not active_api_key:
            raise HTTPException(status_code=400, detail="No Groq API key provided and server default is not set.")

        initial_state = {
            "repo_url": request.repo_url,
            "api_key": active_api_key,
            "assembled_context": "",
            "security_findings": "",
            "bug_findings": "",
            "final_review": ""
        }
        
        final_state = app_graph.invoke(initial_state)
        analysis_result = final_state["final_review"]
        assembled_code_context = final_state["assembled_context"]
        
        try:
            current_run_tree = get_current_run_tree()
            active_run_id = str(current_run_tree.id) if current_run_tree else None
        except Exception:
            active_run_id = None
        
        if active_run_id:
            background_tasks.add_task(
                background_evaluation_job,
                run_id=active_run_id,
                code_context=assembled_code_context,
                review_text=analysis_result,
                api_key=active_api_key
            )
        
        return {"markdown": analysis_result}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        err_str = str(e)
        if "git" in err_str.lower() or "clone" in err_str.lower() or "exit code" in err_str.lower():
            raise HTTPException(
                status_code=400, 
                detail="Could not clone repository. Please check that the URL is correct and the repository is public."
            )
        if "Please reduce the length" in err_str or "rate_limit_exceeded" in err_str or "413" in err_str:
            raise HTTPException(
                status_code=400, 
                detail="Repository context is too large for the model token limit. Try analyzing a smaller repository."
            )
            
        err_type, err_value, err_tb = sys.exc_info()
        formatted_tb = "".join(traceback.format_exception(err_type, err_value, err_tb))
        print("CRASH TRACEBACK:\n", formatted_tb)
        raise HTTPException(status_code=500, detail=str(err_value))
