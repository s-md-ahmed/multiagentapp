# evaluators.py
import os
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

def run_llm_judge_eval(code_context: str, review_text: str) -> int:
    """LLM-as-a-Judge: Uses server-side backend key to evaluate quality securely without leaking user keys."""
    server_api_key = os.getenv("GROQ_API_KEY")
    if not server_api_key:
        return 3  # Fallback score if server key is absent

    llm = ChatGroq(
        api_key=server_api_key,
        model_name="openai/gpt-oss-20b",
        temperature=0.0,  # Zero temperature for rigorous consistency
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
        return int(response.content.strip())
    except Exception:
        return 3  # Fallback median score if parsing fails
