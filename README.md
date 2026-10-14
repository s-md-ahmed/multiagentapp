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

### Agent Graph Architecture Diagram
*<img width="420" height="692" alt="Screenshot 2026-10-14 141841" src="https://github.com/user-attachments/assets/b737d026-e0e0-4030-9010-b0626ca86257" />
*

---

## LangSmith Observability & Tracing

LangSmith is integrated to provide deep debugging, execution tracing, and telemetry for non-deterministic LLM workflows. In this multi-agent architecture, it tracks state transitions across nodes (`loader` -> `bug_hunter` -> `security` -> `architect`), monitors token consumption budgets per model call, and logs exact execution latency. Furthermore, the telemetry data empirically proves asynchronous parallel node execution: the `security` agent ($2.77\text{s}$) finishes inside the execution window of the heavier `bug_hunter` agent ($4.57\text{s}$), demonstrating that LangGraph runs both analysis pods concurrently before passing aggregated state to the `architect` ($31.79\text{s}$).

*<img width="862" height="908" alt="Screenshot 2026-10-14 143152" src="https://github.com/user-attachments/assets/a54443c9-9e53-4b77-98ba-c4b63cd4be65" />
*

---

## Sentry Exception & Performance Monitoring

Sentry is integrated directly into the FastAPI backend service to capture unhandled runtime exceptions, Git cloning timeouts, network failures, and external API rate limits (HTTP 429) in real time. This ensures production system stability and provides immediate actionable stack traces for debugging server-side faults.

---

## Key Design Decisions & Architectural Trade-offs

- Why Multi-Agent Specialization (LangGraph) over a Single Prompt?
  - The Problem: Forcing a single LLM prompt to simultaneously find cybersecurity exploits, logic bugs, and structural architecture improvements causes context degradation and superficial outputs.
  - The Solution: Decoupling the pipeline into specialized sequential nodes—Agent 1 (Security Expert) and Agent 2 (QA Bug Hunter)—feeds clean, domain-specific insights directly into Agent 3 (Lead Architect) for final executive synthesis.

- Why LangSmith & Sentry for Observability?
  - LangSmith: Provides full visibility into non-deterministic LLM execution paths, tracking token consumption, prompt latency, and agent node routing.
  - Sentry: Monitors production runtime exceptions, catching unhandled backend crashes, Git network errors, and API timeout failures instantly.

- Why Isolated Temporary Sandboxes (tempfile.TemporaryDirectory)?
  - The Problem: Cloning external GitHub repositories directly into persistent server storage introduces race conditions, disk bloat, and cross-tenant security vulnerabilities.
  - The Solution: Every analysis request initializes a strictly isolated, ephemeral temporary directory that is automatically purged via custom exception-safe cleanup handles upon completion.

- Why Strict Token Safety Budgets & Filtering?
  - The Problem: Repositories often contain massive build artifacts, documentation, or binary files that blow past LLM context limits and incur unnecessary token costs.
  - The Solution: The git handler ignores non-code directories (.git, node_modules, build), explicitly excludes .ipynb files to prevent JSON bloat, and enforces strict line-count/character budgets per file.

- Why Client-Side BYOK (Bring Your Own Key) via JSON Payload?
  - The Problem: Hardcoding global API keys or routing all public traffic through a single server key triggers rate limits (HTTP 429) and creates infrastructure liabilities.
  - The Solution: Users provide their own Groq API key (gsk_...), passed securely over POST JSON payloads for runtime isolation without persistent database storage.

---

## Core Features

- Multi-Agent Engineering Pod: Parallel-branching execution loop using LangGraph for cybersecurity scanning, QA bug hunting, and architectural synthesis.
- Full Stack Observability: Integrated LangSmith for agent execution tracing and Sentry for real-time error tracking and exception monitoring.
- Smart Repository Filtering: Automatically strips out dependency directories and heavy notebooks (.ipynb), focusing strictly on high-value code (.py, .js, .ts, .cpp, .java).
- Bring Your Own Key (BYOK) Security: Allows users to supply their personal Groq API key with client-side format validation.
- Strict Token Guardrails: Enforces a 200-line cap per file and total character length caps to respect model context limits safely.
- Containerized CI/CD Deployment: Fully containerized with Docker and auto-deployed via GitHub Actions CI/CD pipeline on Render.

---

## Project Structure

```text
├── backend/
│   ├── main.py             # FastAPI entrypoint, Sentry initialization, static mounting, & error middleware
│   └── services/
│       ├── agent_crew.py   # LangGraph orchestration (Security, QA, Lead Architect state nodes)
│       ├── git_handler.py  # Secure temporary cloning, file extension filtering, & cleanup hooks
│       └── parser.py       # Line-by-line file parser with truncation & token safety budgets
├── frontend/
│   ├── index.html          # UI shell containing BYOK input, repo URL bar, & loading states
│   ├── style.css           # Modern dark-mode styling with pulse animations & responsive cards
│   └── app.js              # Client-side validation, fetch routing, & Marked.js rendering logic
├── requirements.txt        # Python package dependencies (FastAPI, LangGraph, LangSmith, Sentry-SDK)
└── Dockerfile              # Container configuration file
