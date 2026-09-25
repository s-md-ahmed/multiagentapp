# AI Repo Analyzer (Multi-Agent Code Reviewer)

A full-stack, production-ready multi-agent engineering code review system powered by the Groq LPU inference engine. It deploys a specialized digital pod—consisting of a Security Specialist, a QA Bug Hunter, and a Lead Software Architect—to analyze public GitHub repositories and generate comprehensive structured markdown reviews.

**Live Demo:** [https://multiagentapp-7zwv.onrender.com/](https://multiagentapp-7zwv.onrender.com/)  
*(Note: Hosted on a free-tier instance, so please allow a few seconds for the server to spin up on an initial request.)*

---

## The Engineering Challenge (Why Multi-Agent Code Review?)
Traditional automated linters look for rigid syntax matching, and single-prompt LLM code reviews often suffer from "attention dilution," missing deep security vulnerabilities or edge-case runtime bugs when forced to evaluate everything at once. This project solves that by enforcing a **multi-agent separation of concerns**: dividing the review pipeline into isolated expert personas, passing structured telemetry between them, and synthesizing a prioritized executive action plan.

---

## System Architecture & Workflow
The application follows an isolated sandbox pipeline: cloning repositories securely, filtering out peripheral assets to prevent token bloat, executing parallelized agent scans, and synthesizing clean markdown reports.
<img width="4015" height="7968" alt="diagram (2)" src="https://github.com/user-attachments/assets/aec622c4-9b67-4d8a-a30b-cf38d622315e" />


### Why This Architecture? (Design Decisions & Trade-offs)
* **Why Multi-Agent Specialization over a Single Prompt?**
  * *The Problem:* Forcing a single LLM prompt to simultaneously find cybersecurity exploits, logic bugs, and structural architecture improvements causes context degradation and superficial outputs.
  * *The Solution:* Decoupling the pipeline into specialized sequential steps—Agent 1 (Security Expert) and Agent 2 (QA Bug Hunter)—feeds clean, domain-specific insights directly into Agent 3 (Lead Architect) for final executive synthesis.

* **Why Isolated Temporary Sandboxes (`tempfile.TemporaryDirectory`)?**
  * *The Problem:* Cloning external GitHub repositories directly into persistent server storage introduces race conditions, disk bloat, and severe cross-tenant security vulnerabilities.
  * *The Solution:* Every analysis request initializes a strictly isolated, ephemeral temporary directory that is automatically purged via custom exception-safe cleanup handles upon completion.

* **Why Strict Token Safety Budgets and File Filtering?**
  * *The Problem:* Repositories often contain massive build artifacts, documentation, or binary files that blow past LLM context limits and incur unnecessary token costs.
  * *The Solution:* The git handler ignores non-code directories (`.git`, `node_modules`, `build`, etc.), explicitly excludes `.ipynb` files to prevent JSON bloat, and enforces strict line-count/character budgets per file.

* **Why Client-Side BYOK (Bring Your Own Key) via JSON Payload?**
  * *The Problem:* Hardcoding global API keys or routing all public traffic through a single server key quickly triggers rate limits (`429`) and creates infrastructure cost liabilities.
  * *The Solution:* Users provide their own Groq API key (`gsk_...`), passed securely over POST JSON payloads for runtime isolation without hitting persistent databases.

---

## Core Features
* **Multi-Agent Engineering Pod:** Sequential execution loop utilizing isolated system instructions for cybersecurity scanning, QA bug hunting, and architectural synthesis.
* **Smart Repository Filtering:** Automatically strips out dependency directories and heavy notebooks (`.ipynb`), focusing strictly on high-value code (`.py`, `.js`, `.ts`, `.cpp`, `.java`, etc.).
* **Bring Your Own Key (BYOK) Security:** Allows users to supply their personal Groq API key with client-side format validation (`gsk_...`).
* **Strict Token Guardrails:** Enforces a 200-line cap per file and total character length caps to respect model limits safely.
* **Resilient Error Handling:** Intercepts git clone failures, invalid URLs, and context length overages, returning clean HTTP status codes (`400`) and sanitized UI feedback.

---

## Tech Stack
* **Backend:** FastAPI, Uvicorn, GitPython, Python-Dotenv, Pydantic
* **AI / ML:** Groq SDK (`groq`), Custom System Prompts
* **Frontend:** Vanilla HTML5, CSS3, Modern JavaScript (Fetch API), Marked.js (Markdown Parsing)
* **Infrastructure:** Docker (`python:3.12-slim`), Render

---

## Project Structure
```text
├── backend/
│   ├── main.py             # FastAPI entrypoint, routing, static mounting, and error middleware
│   └── services/
│       ├── agent_crew.py   # Multi-agent orchestration (Security, QA, Lead Architect pipelines)
│       ├── git_handler.py  # Secure temporary cloning, file extension filtering, and cleanup hooks
│       └── parser.py       # Line-by-line file parser with truncation and token safety budgets
├── frontend/
│   ├── index.html          # UI shell containing BYOK input, repo URL bar, and loading states
│   ├── style.css           # Modern dark-mode styling with pulse animations and responsive cards
│   └── app.js              # Client-side validation, fetch routing, and Markdown rendering logic
├── requirements.txt        # Python package dependencies
└── Dockerfile              # Container configuration file
