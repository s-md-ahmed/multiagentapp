import os
import tempfile
from pathlib import Path
from typing import TypedDict, List
from .parser import parse_repo
from .git_handler import clone_repo_to_temp
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 1. Define the Shared State for the Graph
class AnalysisState(TypedDict):
    repo_url: str
    api_key: str
    assembled_context: str
    security_findings: str
    bug_findings: str
    final_review: str

# 2. Define Node Functions

def load_and_parse_node(state: AnalysisState):
    """Clones the repo, parses files, and prepares the context budget."""
    print("--- [GRAPH NODE] Cloning and Parsing Repository ---")
    with tempfile.TemporaryDirectory() as temp_repo_path:
        # Note: In production or async settings, handle tempdir persistence carefully if needed.
        target_files = clone_repo_to_temp(state["repo_url"], temp_repo_path)
        parsed_data = parse_repo(target_files)
        
        MAX_TOTAL_CHARS = 10000
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

        if not assembled_context.strip():
            raise ValueError("No valid code files found or repository is empty.")

        if truncated_flag:
            assembled_context += "\n--- [NOTE: Peripheral files omitted to respect API token budget.] ---\n"

        return {"assembled_context": assembled_context}

def security_node(state: AnalysisState):
    """Agent 1: Security Specialist"""
    print("--- [GRAPH NODE] Security Specialist Scanning ---")
    llm = ChatGroq(
        api_key=state["api_key"], 
        model_name="openai/gpt-oss-20b", 
        temperature=0.1,
        max_tokens=3000
    )
    sec_sys = (
        "You are a cybersecurity expert. Scan the codebase strictly for vulnerabilities, hardcoded secrets, and injection risks. "
        "For every finding, provide a concise, direct 1-sentence explanation for the 'Why'."
    )
    messages = [
        ("system", sec_sys),
        ("user", f"Here is the repository codebase:\n\n{state['assembled_context']}")
    ]
    response = llm.invoke(messages)
    return {"security_findings": response.content}

def bug_hunter_node(state: AnalysisState):
    """Agent 2: Bug Hunter"""
    print("--- [GRAPH NODE] Bug Hunter Scanning Logic ---")
    llm = ChatGroq(
        api_key=state["api_key"], 
        model_name="openai/gpt-oss-20b", 
        temperature=0.1,
        max_tokens=3000
    )
    bug_sys = (
        "You are a senior QA engineer. Scan the codebase strictly for logic bugs, unhandled exceptions, and edge-case failures. "
        "For every bug found, provide a concise, direct 1-sentence explanation for the 'Why'."
    )
    messages = [
        ("system", bug_sys),
        ("user", f"Here is the repository codebase:\n\n{state['assembled_context']}")
    ]
    response = llm.invoke(messages)
    return {"bug_findings": response.content}

def architect_node(state: AnalysisState):
    """Agent 3: Lead Architect Synthesis"""
    print("--- [GRAPH NODE] Lead Architect Synthesizing Review ---")
    llm = ChatGroq(
        api_key=state["api_key"], 
        model_name="openai/gpt-oss-20b", 
        temperature=0.1,
        max_tokens=6000
    )
    synth_sys = (
        "You are a Lead Software Architect. Synthesize the context into a clean, comprehensive Markdown review.\n"
        "STRUCTURE REQUIRED:\n"
        "1. Architecture Overview (1 concise paragraph)\n"
        "2. Positive Aspects & Strengths (3-4 bullet points max)\n"
        "3. Security Findings (Markdown table with columns: Vulnerability | Why it Happens | Severity | Estimated Time | Owner)\n"
        "4. Bug Findings (Markdown table with columns: Bug | Why it Happens | Severity | Estimated Time | Owner)\n"
        "5. Recommendations & Prioritized Action Plan (Markdown table with columns: Priority | Action | Owner | Estimated Time)\n"
        "RULES: Keep all table cell descriptions strictly 1 short sentence. Ensure valid markdown and finish all 5 sections completely."
    )
    synth_user = (
        f"--- CODEBASE CONTEXT ---\n{state['assembled_context']}\n\n"
        f"--- SECURITY REPORT ---\n{state['security_findings']}\n\n"
        f"--- BUG REPORT ---\n{state['bug_findings']}"
    )
    messages = [
        ("system", synth_sys),
        ("user", synth_user)
    ]
    response = llm.invoke(messages)
    return {"final_review": response.content}

# 3. Build and Compile the Workflow Graph
workflow = StateGraph(AnalysisState)

# Add nodes
workflow.add_node("loader", load_and_parse_node)
workflow.add_node("security", security_node)
workflow.add_node("bug_hunter", bug_hunter_node)
workflow.add_node("architect", architect_node)

# Define edges (Sequential execution, or parallel security + bug hunting)
workflow.set_entry_point("loader")
workflow.add_edge("loader", "security")
workflow.add_edge("loader", "bug_hunter")
workflow.add_edge("security", "architect")
workflow.add_edge("bug_hunter", "architect")
workflow.add_edge("architect", END)

# Compile the graph into an executable app
app_graph = workflow.compile()

# 4. Main Entry Point Called by FastAPI
def analyze_codebase(repo_url: str, api_key: str = None):
    active_api_key = api_key or os.getenv("GROQ_API_KEY")
    if not active_api_key:
        raise ValueError("No Groq API key provided. Please pass a valid BYOK key.")

    initial_state = {
        "repo_url": repo_url,
        "api_key": active_api_key,
        "assembled_context": "",
        "security_findings": "",
        "bug_findings": "",
        "final_review": ""
    }

    print("--- [LANGGRAPH] Executing analysis graph workflow ---")
    final_state = app_graph.invoke(initial_state)
    print("--- [COMPLETE] Graph analysis finished successfully! ---")
    
    return final_state["final_review"]
