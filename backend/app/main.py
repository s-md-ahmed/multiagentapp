import os
import sys
import traceback
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

class RepoRequest(BaseModel):
    repo_url: str
    groq_api_key: Optional[str] = None

@app.post("/analyze")
def analyze_repo(request: RepoRequest):
    except HTTPException as e:
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
        if "Please reduce the length" in err_str or "rate_limit_exceeded" in err_str or "413" in err_str:
            raise HTTPException(
                status_code=400, 
                detail="Repository context is too large for the model token limit. Try analyzing a smaller repository or check your API tier limits."
            )
            
        err_type, err_value, err_tb = sys.exc_info()
        formatted_tb = "".join(traceback.format_exception(err_type, err_value, err_tb))
        print("CRASH TRACEBACK:\n", formatted_tb)
        raise HTTPException(status_code=500, detail=str(err_value) + " | Check terminal for full traceback.")
