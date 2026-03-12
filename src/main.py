import os
import time
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "fincore-banking-assistant")

from src.database.database import init_db
from src.database.audit_service import audit_service
from src.graph.banking_graph import run_query
from src.knowledge_graph.kg_queries import BankingKGQueries
import structlog

logger = structlog.get_logger(__name__)

init_db()

app = FastAPI(
    title="FinCore Banking Assistant API",
    description="Multi-Agent AI Banking Assistant",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    customer_id: str
    session_id: Optional[str] = None
    conversation_history: Optional[list] = []


class TestScenarioRequest(BaseModel):
    scenario_id: int
    customer_id: str = "CUST1001"


TEST_SCENARIOS = {
    1: {"name": "Account Balance and Transactions",
        "query": "What is my current account balance and my last 5 transactions?",
        "expected_agents": ["account"]},
    2: {"name": "Home Loan Eligibility",
        "query": "Am I eligible for a Rs.20 lakh home loan given my current EMIs?",
        "expected_agents": ["loan", "account"]},
    3: {"name": "Fraud Transaction Dispute",
        "query": "I see a transaction I didn't make, Rs.45,000 to an unknown account. Please help!",
        "expected_agents": ["fraud"]},
    4: {"name": "MSME Loan Documents and RBI Rules",
        "query": "What documents do I need for an MSME loan and what are the RBI rules?",
        "expected_agents": ["compliance", "loan"]},
    5: {"name": "Account Upgrade",
        "query": "I want to upgrade my savings account to a premium account. What are the benefits and am I eligible?",
        "expected_agents": ["account", "compliance"]},
    6: {"name": "Missing Transfer and Wrong Balance",
        "query": "My friend transferred money to me but it has not reflected. My balance also looks wrong.",
        "expected_agents": ["account", "fraud"]},
    7: {"name": "Personal Loan with Existing Car Loan",
        "query": "Can I get a personal loan? I already have a car loan.",
        "expected_agents": ["loan", "compliance"]},
    8: {"name": "Inactive Accounts",
        "query": "Show me all accounts I own and tell me which ones have been inactive for over 6 months.",
        "expected_agents": ["account"]},
}


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0", "timestamp": time.time()}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    if not request.customer_id.strip():
        raise HTTPException(status_code=400, detail="Customer ID is required")

    session_id = request.session_id or str(uuid.uuid4())
    result = run_query(
        query=request.query,
        customer_id=request.customer_id,
        session_id=session_id,
        conversation_history=request.conversation_history or [],
    )
    return result


@app.get("/api/test-scenarios")
async def get_scenarios():
    return {
        "scenarios": [
            {"id": k, "name": v["name"], "query": v["query"],
             "expected_agents": v["expected_agents"]}
            for k, v in TEST_SCENARIOS.items()
        ]
    }


@app.post("/api/test-scenarios/run")
async def run_scenario(request: TestScenarioRequest):
    if request.scenario_id not in TEST_SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
    scenario = TEST_SCENARIOS[request.scenario_id]
    session_id = f"test-{request.scenario_id}-{str(uuid.uuid4())[:8]}"
    start = time.time()
    result = run_query(
        query=scenario["query"],
        customer_id=request.customer_id,
        session_id=session_id,
    )
    latency = round((time.time() - start) * 1000)
    return {
        "scenario_id": request.scenario_id,
        "scenario_name": scenario["name"],
        "query": scenario["query"],
        "expected_agents": scenario["expected_agents"],
        "actual_agents": result.get("agents_invoked", []),
        "latency_ms": latency,
        "within_sla": latency < 4000,
        "result": result,
    }


@app.post("/api/test-scenarios/run-all")
async def run_all(customer_id: str = "CUST1001"):
    results = []
    total_start = time.time()
    for sid in range(1, 9):
        scenario = TEST_SCENARIOS[sid]
        session_id = f"test-all-{sid}-{str(uuid.uuid4())[:8]}"
        start = time.time()
        try:
            result = run_query(
                query=scenario["query"],
                customer_id=customer_id,
                session_id=session_id,
            )
            latency = round((time.time() - start) * 1000)
            results.append({
                "scenario_id": sid,
                "name": scenario["name"],
                "status": "passed" if result.get("success") else "failed",
                "latency_ms": latency,
                "within_sla": latency < 4000,
                "agents_invoked": result.get("agents_invoked", []),
                "expected_agents": scenario["expected_agents"],
                "response_preview": result.get("response", "")[:150] + "...",
                "critique_score": result.get("critique_result", {}).get("overall_score"),
            })
        except Exception as e:
            results.append({
                "scenario_id": sid,
                "name": scenario["name"],
                "status": "error",
                "error": str(e),
                "latency_ms": round((time.time() - start) * 1000),
            })

    total = round((time.time() - total_start) * 1000)
    passed = sum(1 for r in results if r["status"] == "passed")
    return {
        "total_scenarios": 8,
        "passed": passed,
        "failed": 8 - passed,
        "within_sla_count": sum(1 for r in results if r.get("within_sla")),
        "total_time_ms": total,
        "results": results,
    }


@app.get("/api/audit/session/{session_id}")
async def get_session_audit(session_id: str):
    result = audit_service.get_session_audit(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@app.get("/api/audit/customer/{customer_id}")
async def get_customer_audit(customer_id: str, limit: int = 20):
    return {"history": audit_service.get_customer_audit_history(customer_id, limit)}


@app.get("/api/audit/escalations")
async def get_escalations(resolved: Optional[bool] = None):
    return {"escalations": audit_service.get_all_escalations(resolved)}


@app.get("/api/audit/stats")
async def get_audit_stats():
    return audit_service.get_stats()


@app.get("/api/customers/{customer_id}")
async def get_customer(customer_id: str):
    try:
        kg = BankingKGQueries()
        profile = kg.get_customer_financial_profile(customer_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"success": True, "customer": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/kg/fraud-network")
async def fraud_network():
    try:
        kg = BankingKGQueries()
        return {"success": True, "network": kg.detect_fraud_ring()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=int(os.getenv("APP_PORT", 8000)),
        reload=True,
    )