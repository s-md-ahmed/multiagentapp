import os
import tempfile
from pathlib import Path
from .parser import parse_repo
from groq import Groq
from .git_handler import clone_repo_to_temp
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def analyze_codebase(repo_url: str, api_key: str = None):
    active_api_key = api_key or os.getenv("GROQ_API_KEY")
    
    if not active_api_key:
        raise ValueError("No Groq API key provided. Please pass a valid BYOK key.")

    client = Groq(api_key=active_api_key)
    
    with tempfile.TemporaryDirectory() as temp_repo_path:
        print(f"--- [SESSION SANDBOX] Initialized isolated temp directory: {temp_repo_path} ---")
        
        print("--- [CLONE] Cloning and filtering repository... ---")
        target_files = clone_repo_to_temp(repo_url, temp_repo_path)
        
        print("--- [PARSE] Parsing repository files... ---")
        parsed_data = parse_repo(target_files)
        
        # --- STRICT FILE-AWARE TOKEN SAFETY BUDGET ---
        # We append files whole until we hit our cap. No mid-file slicing!
        MAX_TOTAL_CHARS = 12000
        assembled_context = ""
        current_chars = 0
        truncated_flag = False

        for file_data in parsed_data:
            file_path = file_data["file_path"]
            content = file_data["content"]
            file_block = f"File Path: {file_path}\nContent:\n{content}\n\n"
            
            if current_chars + len(file_block) > MAX_TOTAL_CHARS:
                truncated_flag = True
                break
                
            assembled_context += file_block
            current_chars += len(file_block)

        if truncated_flag:
            print(f"--- [TRUNCATION] Repository exceeded {MAX_TOTAL_CHARS} chars. Omitted remaining files to keep context whole. ---")
            assembled_context += "\n--- [NOTE: Some peripheral files were omitted to respect token budget limits. Analyze the provided files fully.] ---\n"

        # Agent 1: Security Specialist
        print("--- [AGENT 1] Security Specialist scanning... ---")
        sec_sys = (
            "You are a cybersecurity expert. Scan the codebase strictly for vulnerabilities, hardcoded secrets, and injection risks. "
            "For every finding, provide a concise, direct 1-sentence explanation for the 'Why'. "
            "CRITICAL: Perform a single analysis pass. Output findings immediately and stop."
        )
        sec_completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": sec_sys},
                {"role": "user", "content": f"Here is the repository codebase:\n\n{assembled_context}"}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        security_findings = sec_completion.choices[0].message.content

        # Agent 2: Bug Hunter
        print("--- [AGENT 2] Bug Hunter scanning logic... ---")
        bug_sys = (
            "You are a senior QA engineer. Scan the codebase strictly for logic bugs, unhandled exceptions, and edge-case failures. "
            "For every bug found, provide a concise, direct 1-sentence explanation for the 'Why'. "
            "CRITICAL: Perform a single analysis pass. Output findings immediately and stop."
        )
        bug_completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": bug_sys},
                {"role": "user", "content": f"Here is the repository codebase:\n\n{assembled_context}"}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        bug_findings = bug_completion.choices[0].message.content

        # Agent 3: Lead Architect
        print("--- [AGENT 3] Lead Architect compiling final review... ---")
        synth_sys = (
            "You are a Lead Software Architect. Synthesize the context into a clean Markdown review.\n"
            "STRUCTURE REQUIRED:\n"
            "1. Architecture Overview\n"
            "2. Positive Aspects & Strengths\n"
            "3. Security Findings (Markdown table with columns: Vulnerability | Why it Happens | Severity | Estimated Time | Owner)\n"
            "4. Bug Findings (Markdown table with columns: Bug | Why it Happens | Severity | Estimated Time | Owner)\n"
            "5. Recommendations & Prioritized Action Plan (Markdown table with columns: Priority | Action | Owner | Estimated Time)\n"
            "RULES: Keep descriptions brief (1 sentence max). Output valid markdown and finish all tables completely."
        )
        
        synth_user = (
            f"--- CODEBASE CONTEXT ---\n{assembled_context}\n\n"
            f"--- SECURITY REPORT ---\n{security_findings}\n\n"
            f"--- BUG REPORT ---\n{bug_findings}"
        )
        
        final_completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": synth_sys},
                {"role": "user", "content": synth_user}
            ],
            temperature=0.1,
            max_tokens=8000
        )
        
        print("--- [COMPLETE] Analysis finished successfully! ---")
        return final_completion.choices[0].message.content
