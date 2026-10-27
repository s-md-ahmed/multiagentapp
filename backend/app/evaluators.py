# evaluators.py
import os
from typing import Optional
from langchain_groq import ChatGroq

def run_structural_eval(review_markdown: str) -> float:
    """Deterministic check: Verifies all 5 required headers and markdown table presence (Case-insensitive)."""
    required_headers = [
        "Architecture Overview",
        "Positive Aspects",
        "Security Findings",
        "Bug Findings",
        "Recommendations"
    ]
    review_lower = review_markdown.lower()
    headers_pass = all(h.lower() in review_lower for h in required_headers)
    has_tables = "|" in review_markdown
    
    return 1.0 if (headers_pass and has_tables) else 0.0

def run_llm_judge_eval(code_context: str, review_text: str) -> Optional[int]:
    """LLM-as-a-Judge: Evaluates quality securely. Returns None on failure instead of injecting fake metrics."""
    server_api_key = os.getenv("GROQ_API_KEY")
    if not server_api_key:
        print("--- [EVAL ERROR] Server GROQ_API_KEY is missing. Skipping LLM judge. ---")
        return None

    llm = ChatGroq(
        api_key=server_api_key,
        model_name="openai/gpt-oss-20b",
        temperature=0.0,
        max_tokens=10
    )
    
    prompt = f"""
    You are a strict code review auditor. Evaluate the following AI-generated code review based on the provided repository context.
    
    Repository Context:
    {code_context}
    
    AI Code Review to Judge:
    {review_text}
    
    Task: Rate the actionability and factual grounding of the review on a scale of 1 to 5.
    - 5: Clear, actionable findings mapped directly to the code.
    - 1: Vague, generic filler text with unverified references.
    
    Output format: Return ONLY a single integer score (1-5). Do not include any other text.
    """
    
    try:
        response = llm.invoke([("user", prompt)])
        cleaned_score = response.content.strip()
        score = int(cleaned_score)
        if 1 <= score <= 5:
            return score
        print(f"--- [EVAL WARNING] LLM judge returned out-of-range score: {cleaned_score} ---")
        return None
    except Exception as e:
        print(f"--- [EVAL ERROR] LLM judge execution or parsing failed: {e} ---")
        return None
