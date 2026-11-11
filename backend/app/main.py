# main.py
import os
import sys
import traceback
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, SecretStr
import re
from langchain_groq import ChatGroq
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=False,
    traces_sample_rate=1.0,
)

if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ.setdefault("LANGCHAIN_PROJECT", "multi-agent-code-reviewer")

app = FastAPI()

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

from .agent_crew import app_graph

def evaluate_review_quality(code_context: str, review_text: str, api_key: str) -> dict:
    has_headers = bool(re.search(r'^#{1,3}\s+', review_text, re.MULTILINE))
    has_tables = "|" in review_text
    structural_score = 1.0 if (has_headers or has_tables) else 0.0

    llm_score = None
    if api_key:
        try:
            eval_llm = ChatGroq(
                api_key=api_key,
                model_name="openai/gpt-oss-20b",
                temperature=0.1
            )
            
            prompt = f"""You are a strict code review auditor. Evaluate the following AI-generated code review based on the repository context.
            
Repository Context:
{code_context[:5000]}

AI Code Review:
{review_text[:3000]}

Task: Rate the actionability and factual grounding on a scale of 1 to 5.
Output format: Return ONLY a single integer score from 1 to 5."""

            res = eval_llm.invoke([("user", prompt)])
            raw_content = res.content.strip() if res and res.content else ""
            match = re.search(r'([1-5])', raw_content)
            if match:
                llm_score = int(match.group(1))
        except Exception as e:
            print(f"--- [EVAL ERROR] Inline LLM Judge failed: {e} ---")

    return {
        "structural_compliance": structural_score,
        "llm_quality_judge": llm_score
    }

@app.post("/analyze")
def analyze_repo(request: RepoRequest):
    try:
        raw_user_key = request.groq_api_key.get_secret_value() if request.groq_api_key else None
        active_api_key = raw_user_key or os.getenv("GROQ_API_KEY")
        if not active_api_key:
            raise HTTPException(status_code=400, detail="No Groq API key provided.")

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
        err_type, err_value, err_tb = sys.exc_info()
        formatted_tb = "".join(traceback.format_exception(err_type, err_value, err_tb))
        print("CRASH TRACEBACK:\n", formatted_tb)
        raise HTTPException(status_code=500, detail=str(err_value))
