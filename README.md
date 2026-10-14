# AI Repo Analyzer (Multi-Agent Code Reviewer)

A full-stack, production-ready multi-agent engineering code review system powered by LangGraph and the Groq LPU inference engine. It deploys a specialized digital pod—consisting of a Security Specialist, a QA Bug Hunter, and a Lead Software Architect—to analyze public GitHub repositories and generate comprehensive structured markdown reviews.

Live Demo: https://multiagentapp-7zwv.onrender.com/
(Note: Hosted on a free-tier instance; please allow a few seconds for the server to spin up on an initial request.)

---

## The Engineering Challenge (Why Multi-Agent Code Review?)

Traditional automated linters look for rigid syntax matching, and single-prompt LLM code reviews often suffer from "attention dilution," missing deep security vulnerabilities or edge-case runtime bugs when forced to evaluate everything at once. 

This project solves that by enforcing a multi-agent separation of concerns: dividing the review pipeline into isolated expert personas using LangGraph, passing structured telemetry between nodes, tracking execution traces via LangSmith, and synthesizing a prioritized executive action plan while monitoring system stability with Sentry.

---

## Tech Stack & Observability

- Core Engine & Backend: Python 3.12, FastAPI, Uvicorn, Pydantic, GitPython
- AI Orchestration & LLM: LangGraph, LangSmith (Tracing & Telemetry), Groq SDK (llama-3.3-70b-versatile)
- System Observability & Monitoring: Sentry (Real-time exception tracking and runtime error handling)
- Frontend: Vanilla HTML5, Modern CSS3 (Dark Mode UI), JavaScript (Fetch API), Marked.js
- DevOps & Infrastructure: Docker (python:3.12-slim), GitHub Actions CI/CD, Render

---

## System Architecture & State Workflow

The application follows an isolated sandbox pipeline: cloning repositories securely, filtering out peripheral assets to prevent token bloat, executing parallelized agent scans via LangGraph nodes, and synthesizing clean markdown reports.

### Agent Graph State & Node Workflow
```mermaid
graph TD
    START(["User Repo Request"]) --> INGEST["Clone & Sanitize Codebase<br/><i>git_handler.py</i>"]
    INGEST --> PARSE["Filter & Build Context Budget<br/><i>parser.py</i>"]
    
    PARSE --> AGENT_SEC["Agent 1: Security Specialist<br/><i>OWASP, Hardcoded Keys, Injections</i>"]
    PARSE --> AGENT_QA["Agent 2: QA Bug Hunter<br/><i>Edge Cases, Null Pointers, Logic Errors</i>"]
    
    AGENT_SEC --> STATE["LangGraph State Aggregator<br/><i>Merges Findings & Telemetry</i>"]
    AGENT_QA --> STATE
    
    STATE --> AGENT_ARCH["Agent 3: Lead Architect<br/><i>Synthesizes Priorities & Action Plan</i>"]
    AGENT_ARCH --> OUTPUT(["Formatted Markdown Review"])

    %% Class Definitions
    classDef startStyle fill:#2563eb,color:#fff,stroke:#1d4ed8,stroke-width:2px;
    classDef agentStyle fill:#0f172a,color:#38bdf8,stroke:#0284c7,stroke-width:2px;
    classDef synthStyle fill:#14532d,color:#4ade80,stroke:#16a34a,stroke-width:2px;
    classDef stateStyle fill:#334155,color:#f8fafc,stroke:#475569,stroke-width:1px;

    %% Apply Classes to Nodes
    class START,OUTPUT startStyle;
    class INGEST,PARSE,STATE stateStyle;
    class AGENT_SEC,AGENT_QA agentStyle;
    class AGENT_ARCH synthStyle;```

**## Langsmith Observability**
LangSmith is integrated to provide deep debugging and telemetry for non-deterministic LLM workflows. In this multi-agent architecture, it tracks state transitions across nodes (loader -> bug_hunter -> security -> architect), monitors token consumption budgets per model call, and logs exact execution latency.
![Uploading Screenshot 2026-10-14 143152.png…]()
