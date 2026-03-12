# FinCore Banking Assistant Architecture Documentation

## 1. System Overview
FinCore Banking Assistant is an agentic AI system designed for modern banking operations. It leverages multi-agent orchestration to handle account management, loans, fraud detection, and regulatory compliance with high reliability and observability.

## 2. Agentic Workflow (LangGraph)
The system uses **LangGraph** to manage complex, multi-step banking workflows.

- **Router Agent**: Analyzes the initial query to determine the required specialized agents.
- **Planner Agent**: Generates a detailed execution plan based on the identified intents.
- **Specialized Agents**: Account, Loan, Fraud, and Compliance agents execute domain-specific tasks.
- **Aggregator Agent**: Synthesizes the results from multiple agents into a coherent response.
- **Critique Agent**: Validates the final response for accuracy, safety, and compliance before it reaches the user.

## 3. Data Layers
FinCore utilizes a multi-layered data strategy:
- **SQLite (Audit DB)**: Persists all agent decisions, MCP calls, and session logs for forensic auditability.
- **Neo4j (Knowledge Graph)**: Used for complex relationship mapping, such as fraud network detection and customer financial profiling.
- **Domain Data**: Uses JSON-based mock data or SQLite for core banking records (Accounts, Transactions, Loans).

## 4. MCP Infrastructure
The **Model Context Protocol (MCP)** provides a modular interface for banking services:
- **Core Banking Server**: Handles balance inquiries and transfers.
- **Credit Server**: Manages loan applications and credit scoring.
- **Fraud Server**: Analyzes transaction risk and manages fraud cases.
- **Compliance Server**: Executes KYC/AML checks.

## 5. Technical Stack & Observability
- **Frontend**: Next.js 14 with Tailwind CSS, providing a responsive agent dashboard.
- **Backend**: FastAPI (Python) integrated with LangChain and LangGraph.
- **LLM**: Google Gemini 2.0 Flash for low-latency, high-reasoning performance.
- **Observability**: **LangSmith** integration for real-time tracing and evaluation of agentic paths.
- **Logging**: Structured logging via `structlog` for system-level monitoring.

## 6. Security & Compliance
- **Human-in-the-Loop**: High-risk fraud cases trigger mandatory human intervention.
- **Audit Trails**: Every AI decision is logged with reasoning and confidence scores.
- **Regulatory Guardrails**: The Compliance Agent and Critique loop ensure RBI/regulatory adherence.
