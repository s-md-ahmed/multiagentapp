import os
import sys
import traceback
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

import sentry_sdk

# 1. Initialize Sentry (Infra & Backend Ops Observability)
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=False,
    traces_sample_rate=1.0,
)

# 2. Configure LangSmith (Agentic Ops Observability)
# This hooks LangGraph execution traces straight into LangSmith if configured in Render
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ.setdefault("LANGCHAIN_PROJECT", "multi-agent-code-reviewer")

# ----------------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://multiagentapp-7zwv.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve path to the frontend folder at the root level
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Mount the static assets (CSS, JS) so the browser can load them
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# Serve the main index.html file at the root URL
@app.get("/")
def serve_frontend():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"error": "index.html not found in frontend directory"}

# Dedicated debug route to test Sentry error tracking live
@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0

@app.get("/run-evals", response_class=HTMLResponse)
def run_evals_route(groq_api_key: Optional[str] = None):
    """Triggers a live multi-agent evaluation test suite with real-time performance telemetry."""
    from .agent_crew import analyze_codebase
    
    active_key = groq_api_key or os.getenv("GROQ_API_KEY")
    if not active_key:
        return """
        <html>
            <head><title>Eval Error</title><script src="https://cdn.tailwindcss.com"></script></head>
            <body class="bg-slate-950 text-slate-100 flex items-center justify-center h-screen">
                <div class="bg-slate-900 border border-red-500/30 p-8 rounded-xl max-w-md text-center shadow-2xl">
                    <div class="text-red-400 text-4xl mb-3">⚠️</div>
                    <h1 class="text-xl font-bold mb-2">Missing API Key</h1>
                    <p class="text-slate-400 text-sm mb-4">Pass your Groq key in the URL query string like:</p>
                    <code class="bg-slate-950 px-3 py-1.5 rounded text-xs text-emerald-400 block break-all">/run-evals?groq_api_key=gsk_...</code>
                </div>
            </body>
        </html>
        """

    test_repo = "https://github.com/s-md-ahmed/multiagentapp"
    
    # Check LangSmith status for display
    langsmith_active = bool(os.getenv("LANGCHAIN_API_KEY"))
    tracing_status = "Active & Streaming 🚀" if langsmith_active else "Disabled (Set LANGCHAIN_API_KEY)"

    # Start tracking execution latency
    start_time = time.time()
    try:
        result = analyze_codebase(repo_url=test_repo, api_key=active_key)
        execution_latency = round(time.time() - start_time, 2)
    except Exception as e:
        execution_latency = round(time.time() - start_time, 2)
        return f"""
        <html>
            <head><title>Eval Failed</title><script src="https://cdn.tailwindcss.com"></script></head>
            <body class="bg-slate-950 text-slate-100 flex items-center justify-center h-screen">
                <div class="bg-slate-900 border border-red-500/30 p-8 rounded-xl max-w-md text-center shadow-2xl">
                    <div class="text-red-400 text-4xl mb-3">❌</div>
                    <h1 class="text-xl font-bold mb-2">Execution Failed ({execution_latency}s)</h1>
                    <p class="text-red-300 text-xs font-mono bg-slate-950 p-3 rounded">{str(e)}</p>
                </div>
            </body>
        </html>
        """

    required_sections = [
        "Architecture Overview",
        "Positive Aspects & Strengths",
        "Security Findings",
        "Bug Findings",
        "Recommendations & Prioritized Action Plan"
    ]
    
    missing = [sec for sec in required_sections if sec not in result]
    status = "PASS" if not missing else "FAILED"
    
    # Quantitative metrics tracking
    table_markers = result.count("|")
    action_items_estimate = result.lower().count("priority") + result.lower().count("backend team")
    sections_passed_str = f"{len(required_sections) - len(missing)}/{len(required_sections)}"

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Multi-Agent Performance Telemetry</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-950 text-slate-100 font-sans min-h-screen p-8">
        <div class="max-w-4xl mx-auto space-y-6">
            <!-- Header -->
            <div class="flex justify-between items-center bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
                <div>
                    <h1 class="text-2xl font-black tracking-tight text-white">⚡ Agent Telemetry & Tracing</h1>
                    <p class="text-slate-400 text-sm mt-1">LangSmith Status: <span class="text-indigo-400 font-medium">{tracing_status}</span></p>
                </div>
                <div>
                    <span class="px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider {'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' if status == 'PASS' else 'bg-red-500/10 text-red-400 border border-red-500/30'}">
                        {status}
                    </span>
                </div>
            </div>

            <!-- Metrics Grid -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
                    <p class="text-xs text-slate-400 font-medium">Execution Latency</p>
                    <p class="text-2xl font-bold text-amber-400 mt-1">{execution_latency} <span class="text-xs text-slate-500 font-normal">sec</span></p>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
                    <p class="text-xs text-slate-400 font-medium">Sections Passed</p>
                    <p class="text-2xl font-bold text-white mt-1">{sections_passed_str}</p>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
                    <p class="text-xs text-slate-400 font-medium">Table Density Score</p>
                    <p class="text-2xl font-bold text-indigo-400 mt-1">{table_markers} <span class="text-xs text-slate-500 font-normal">pipes</span></p>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
                    <p class="text-xs text-slate-400 font-medium">Action Items Tracked</p>
                    <p class="text-2xl font-bold text-emerald-400 mt-1">{action_items_estimate}</p>
                </div>
            </div>

            <!-- Preview Card -->
            <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
                <h2 class="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">Live Analysis Snippet Preview</h2>
                <pre class="bg-slate-950 p-4 rounded-xl text-xs text-slate-300 font-mono overflow-x-auto border border-slate-800/80 max-h-60">{result[:600]}...</pre>
            </div>
        </div>
    </body>
    </html>
    """

class RepoRequest(BaseModel):
    repo_url: str
    groq_api_key: Optional[str] = None

@app.post("/analyze")
def analyze_repo(request: RepoRequest):
    try:
        print(f"--- [DEBUG] Received request for repo: {request.repo_url} ---")
        
        active_api_key = request.groq_api_key or os.getenv("GROQ_API_KEY")
        
        if not active_api_key:
            raise HTTPException(status_code=400, detail="No Groq API key provided and server default is not set.")

        from .agent_crew import analyze_codebase
        
        analysis_result = analyze_codebase(
            request.repo_url, 
            api_key=active_api_key
        )
        
        return {"markdown": analysis_result}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        err_str = str(e)
        
        if "git" in err_str.lower() or "clone" in err_str.lower() or "exit code" in err_str.lower() or "no such device" in err_str.lower():
            raise HTTPException(
                status_code=400, 
                detail="Could not clone repository. Please check that the URL is correct and the repository is public."
            )

        if "Please reduce the length" in err_str or "rate_limit_exceeded" in err_str or "413" in err_str:
            raise HTTPException(
                status_code=400, 
                detail="Repository context is too large for the model token limit. Try analyzing a smaller repository or check your API tier limits."
            )
            
        err_type, err_value, err_tb = sys.exc_info()
        formatted_tb = "".join(traceback.format_exception(err_type, err_value, err_tb))
        print("CRASH TRACEBACK:\n", formatted_tb)
        raise HTTPException(status_code=500, detail=str(err_value) + " | Check terminal for full traceback.")
