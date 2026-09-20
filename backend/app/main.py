import os
import sys
import traceback
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://multiagentapp-7zwv.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class RepoRequest(BaseModel):
    repo_url: str
    groq_api_key: Optional[str] = None

@app.post("/analyze")
def analyze_repo(request: RepoRequest):
    try:
        print(f"--- [DEBUG] Received request for repo: {request.repo_url} ---")
        
        # Use provided key or fallback to environment variable
        active_api_key = request.groq_api_key or os.getenv("GROQ_API_KEY")
        
        if not active_api_key:
            raise HTTPException(status_code=400, detail="No Groq API key provided and server default is not set.")

        from .agent_crew import analyze_codebase
        
        # Clean execution pass with zero segregation variables
        analysis_result = analyze_codebase(
            request.repo_url, 
            api_key=active_api_key
        )
        
        return {"markdown": analysis_result}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        err_str = str(e)
        
        # Catch Groq's token length or rate limit errors and output a clean message
        if "Please reduce the length" in err_str or "rate_limit_exceeded" in err_str or "413" in err_str:
            print(f"--- [ERROR] Request too large for model token limit: {err_str} ---")
            raise HTTPException(
                status_code=400, 
                detail="Repository context is too large for the model token limit. Try analyzing a smaller repository or check your API tier limits."
            )
            
        err_type, err_value, err_tb = sys.exc_info()
        formatted_tb = "".join(traceback.format_exception(err_type, err_value, err_tb))
        print("CRASH TRACEBACK:\n", formatted_tb)
        raise HTTPException(status_code=500, detail=str(err_value) + " | Check terminal for full traceback.")
