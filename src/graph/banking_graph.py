import os
import time
import uuid
from typing import Literal
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.graph.state import BankingAssistantState, create_initial_state
from src.agents.planner_agent import PlannerAgent
from src.agents.router_agent import RouterAgent
from src.agents.account_agent import AccountAgent
from src.agents.loan_agent import LoanAgent
from src.agents.fraud_agent import FraudAgent
from src.agents.compliance_agent import ComplianceAgent
from src.agents.aggregator_agent import AggregatorAgent
from src.agents.critique_agent import CritiqueAgent
from src.database.audit_service import audit_service
import structlog

load_dotenv()
logger = structlog.get_logger(__name__)

MAX_RETRIES = 1


def get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.1,
        max_tokens=2048,
    )



def planner_node(state: BankingAssistantState) -> BankingAssistantState:
    logger.info("graph.planner.start", query=state["query"][:80])
    try:
        planner = PlannerAgent(get_llm())
        plan = planner.plan(state["query"], state["customer_id"])
        state["planner_plan"] = plan
        state["query_complexity"] = plan.get("query_complexity", "simple")

        audit_service.log_agent_decision(
            session_id=state["session_id"],
            agent_name="planner_agent",
            decision_type="query_planning",
            input_summary=state["query"][:200],
            output_summary=(
                f"Complexity: {plan.get('query_complexity')}, "
                f"Steps: {len(plan.get('execution_plan', []))}"
            ),
            reasoning=plan.get("reasoning", ""),
        )
    except Exception as e:
        logger.error("graph.planner.failed", error=str(e))
        state["planner_plan"] = {
            "query_complexity": "simple",
            "execution_plan": [],
            "reasoning": "Planner failed, using defaults",
        }
        state["query_complexity"] = "simple"

    logger.info("graph.planner.complete",
               complexity=state["query_complexity"])
    return state


def router_node(state: BankingAssistantState) -> BankingAssistantState:
    logger.info("graph.router.start")
    try:
        router = RouterAgent(get_llm())
        result = router.route(
            query=state["query"],
            customer_id=state["customer_id"],
            plan=state["planner_plan"],
            conversation_history=state["conversation_history"],
        )
        state["intent"] = result["intents"]
        state["agents_to_invoke"] = result["agents"]
        state["routing_confidence"] = result.get("confidence", {})

        audit_service.log_agent_decision(
            session_id=state["session_id"],
            agent_name="router_agent",
            decision_type="agent_routing",
            input_summary=state["query"][:200],
            output_summary=f"Agents: {result['agents']}",
            reasoning=result.get("reasoning", ""),
        )
    except Exception as e:
        logger.error("graph.router.failed", error=str(e))
        # Fallback routing
        state["intent"] = ["general"]
        state["agents_to_invoke"] = ["account"]
        state["routing_confidence"] = {}

    logger.info("graph.router.complete",
               agents=state["agents_to_invoke"])
    return state


def account_agent_node(state: BankingAssistantState) -> BankingAssistantState:
    if "account" not in state["agents_to_invoke"]:
        return state
    logger.info("graph.account_agent.start")
    try:
        agent = AccountAgent(get_llm())
        result = agent.run(state)
        state["agent_outputs"]["account"] = result["output"]
        state["mcp_calls_log"].extend(result.get("mcp_calls", []))
        state["kg_queries_log"].extend(result.get("kg_queries", []))
        for call in result.get("mcp_calls", []):
            audit_service.log_mcp_call(
                session_id=state["session_id"],
                agent_name="account_agent",
                server_name=call.get("server", ""),
                tool_name=call.get("tool", ""),
                input_params=call.get("params", {}),
                output_result={},
                success=call.get("success", False),
                latency_ms=0,
                error_message=call.get("error"),
            )
    except Exception as e:
        logger.error("graph.account_agent.failed", error=str(e))
        state["agent_outputs"]["account"] = {
            "agent": "account_agent",
            "response": f"Account information temporarily unavailable: {str(e)}",
        }
    return state


def loan_agent_node(state: BankingAssistantState) -> BankingAssistantState:
    if "loan" not in state["agents_to_invoke"]:
        return state
    logger.info("graph.loan_agent.start")
    try:
        agent = LoanAgent(get_llm())
        result = agent.run(state)
        state["agent_outputs"]["loan"] = result["output"]
        state["mcp_calls_log"].extend(result.get("mcp_calls", []))
        state["kg_queries_log"].extend(result.get("kg_queries", []))
        for call in result.get("mcp_calls", []):
            audit_service.log_mcp_call(
                session_id=state["session_id"],
                agent_name="loan_agent",
                server_name=call.get("server", ""),
                tool_name=call.get("tool", ""),
                input_params=call.get("params", {}),
                output_result={},
                success=call.get("success", False),
                latency_ms=0,
                error_message=call.get("error"),
            )
    except Exception as e:
        logger.error("graph.loan_agent.failed", error=str(e))
        state["agent_outputs"]["loan"] = {
            "agent": "loan_agent",
            "response": f"Loan information temporarily unavailable: {str(e)}",
        }
    return state


def fraud_agent_node(state: BankingAssistantState) -> BankingAssistantState:
    if "fraud" not in state["agents_to_invoke"]:
        return state
    logger.info("graph.fraud_agent.start")
    try:
        agent = FraudAgent(get_llm())
        result = agent.run(state)
        state["agent_outputs"]["fraud"] = result["output"]
        state["mcp_calls_log"].extend(result.get("mcp_calls", []))
        state["kg_queries_log"].extend(result.get("kg_queries", []))

        fraud_risk = result.get("risk_level", "low")
        priority = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        if priority.get(fraud_risk, 0) > priority.get(state["risk_level"], 0):
            state["risk_level"] = fraud_risk

        if fraud_risk in ["high", "critical"]:
            state["requires_human"] = True
            audit_service.log_escalation(
                session_id=state["session_id"],
                customer_id=state["customer_id"],
                risk_level=fraud_risk,
                reason="High fraud risk detected by fraud agent",
                case_id=result["output"].get("case_id"),
            )

        for call in result.get("mcp_calls", []):
            audit_service.log_mcp_call(
                session_id=state["session_id"],
                agent_name="fraud_agent",
                server_name=call.get("server", ""),
                tool_name=call.get("tool", ""),
                input_params=call.get("params", {}),
                output_result={},
                success=call.get("success", False),
                latency_ms=0,
                error_message=call.get("error"),
            )
    except Exception as e:
        logger.error("graph.fraud_agent.failed", error=str(e))
        state["agent_outputs"]["fraud"] = {
            "agent": "fraud_agent",
            "response": f"Fraud check temporarily unavailable: {str(e)}",
        }
    return state


def compliance_agent_node(state: BankingAssistantState) -> BankingAssistantState:
    if "compliance" not in state["agents_to_invoke"]:
        return state
    logger.info("graph.compliance_agent.start")
    try:
        agent = ComplianceAgent(get_llm())
        result = agent.run(state)
        state["agent_outputs"]["compliance"] = result["output"]
        state["mcp_calls_log"].extend(result.get("mcp_calls", []))
        state["kg_queries_log"].extend(result.get("kg_queries", []))
        for call in result.get("mcp_calls", []):
            audit_service.log_mcp_call(
                session_id=state["session_id"],
                agent_name="compliance_agent",
                server_name=call.get("server", ""),
                tool_name=call.get("tool", ""),
                input_params=call.get("params", {}),
                output_result={},
                success=call.get("success", False),
                latency_ms=0,
                error_message=call.get("error"),
            )
    except Exception as e:
        logger.error("graph.compliance_agent.failed", error=str(e))
        state["agent_outputs"]["compliance"] = {
            "agent": "compliance_agent",
            "response": f"Compliance information temporarily unavailable: {str(e)}",
        }
    return state


def human_review_node(state: BankingAssistantState) -> BankingAssistantState:
    logger.warning(
        "graph.human_review.triggered",
        customer_id=state["customer_id"],
        risk_level=state["risk_level"],
    )
    state["agent_outputs"]["human_review"] = {
        "agent": "human_review",
        "response": (
            "URGENT ESCALATION: This case has been escalated to our "
            "Fraud Investigation Team. A fraud specialist will contact "
            "you within 30 minutes on your registered mobile number. "
            "Your account is now in protected mode. "
            "Emergency helpline: 1800-123-FRAUD (24x7). "
            "A case ID will be sent to you via SMS shortly."
        ),
        "status": "escalated",
    }
    return state


def aggregator_node(state: BankingAssistantState) -> BankingAssistantState:
    logger.info("graph.aggregator.start",
               agents=list(state["agent_outputs"].keys()),
               retry=state["retry_count"])
    try:
        aggregator = AggregatorAgent(get_llm())
        result = aggregator.synthesize(state)
        state["final_response"] = result["response"]
    except Exception as e:
        logger.error("graph.aggregator.failed", error=str(e))
        # Build response directly from agent outputs
        parts = []
        for name, output in state["agent_outputs"].items():
            if isinstance(output, dict):
                resp = output.get("response", "")
                if resp:
                    parts.append(resp)
        state["final_response"] = (
            "\n\n".join(parts) if parts
            else "I apologize, I could not process your request. "
                 "Please call 1800-123-4567."
        )
    return state


def critique_node(state: BankingAssistantState) -> BankingAssistantState:
    logger.info("graph.critique.start",
               retry=state["retry_count"],
               max_retries=MAX_RETRIES)

    # If already retried enough, force pass and move on
    if state["retry_count"] >= MAX_RETRIES:
        logger.warning("graph.critique.max_retries_reached",
                      retry=state["retry_count"])
        state["critique_passed"] = True
        state["critique_result"] = {
            "passes": True,
            "overall_score": 70,
            "scores": {},
            "issues": ["Max retries reached, passing through"],
            "hallucinations_detected": [],
            "compliance_violations": [],
            "missing_info": [],
            "feedback": "",
        }
        return state

    try:
        critique = CritiqueAgent(get_llm())
        result = critique.critique(
            query=state["query"],
            response=state["final_response"],
            agent_outputs=state["agent_outputs"],
            mcp_calls_log=state["mcp_calls_log"],
        )
        state["critique_result"] = result
        state["critique_passed"] = result.get("passes", True)

        # ── INCREMENT RETRY COUNT HERE inside the node ──────────────
        # This is the only place where state mutation persists in LangGraph
        if not state["critique_passed"]:
            state["retry_count"] = state["retry_count"] + 1
            logger.info("graph.critique.incremented_retry",
                       new_retry=state["retry_count"])
        # ─────────────────────────────────────────────────────────────

        audit_service.log_agent_decision(
            session_id=state["session_id"],
            agent_name="critique_agent",
            decision_type="response_validation",
            input_summary=state["final_response"][:200],
            output_summary=(
                f"Passed: {result.get('passes')}, "
                f"Score: {result.get('overall_score')}"
            ),
            reasoning=result.get("feedback", ""),
        )

        logger.info("graph.critique.complete",
                   passed=result.get("passes"),
                   score=result.get("overall_score"),
                   retry=state["retry_count"])

    except Exception as e:
        logger.error("graph.critique.failed", error=str(e))
        state["critique_passed"] = True
        state["critique_result"] = {
            "passes": True,
            "overall_score": 70,
            "scores": {},
            "issues": [f"Critique error: {str(e)}"],
            "hallucinations_detected": [],
            "compliance_violations": [],
            "missing_info": [],
            "feedback": "",
        }

    return state

def finalize_node(state: BankingAssistantState) -> BankingAssistantState:
    state["response_metadata"] = {
        "agents_invoked": state["agents_to_invoke"],
        "mcp_calls_count": len(state["mcp_calls_log"]),
        "kg_queries_count": len(state["kg_queries_log"]),
        "risk_level": state["risk_level"],
        "required_human": state["requires_human"],
        "critique_score": state.get("critique_result", {}).get("overall_score"),
        "critique_passed": state.get("critique_passed"),
        "retry_count": state["retry_count"],
        "query_complexity": state.get("query_complexity"),
        "planner_plan": state.get("planner_plan"),
    }

    audit_service.log_query(
        session_id=state["session_id"],
        query=state["query"],
        intents=state["intent"],
        agents_invoked=state["agents_to_invoke"],
        final_response=state["final_response"],
        planner_plan=state.get("planner_plan"),
        critique_passed=state.get("critique_passed"),
        critique_feedback=state.get(
            "critique_result", {}
        ).get("feedback"),
        retry_count=state["retry_count"],
    )

    logger.info("graph.finalize.complete",
               session_id=state["session_id"],
               response_length=len(state["final_response"]))
    return state



def route_after_fraud(
    state: BankingAssistantState,
) -> Literal["human_review", "aggregator"]:
    if state.get("requires_human", False):
        return "human_review"
    return "aggregator"


def route_after_critique(
    state: BankingAssistantState,
) -> Literal["aggregator", "finalize"]:
    critique_passed = state.get("critique_passed", True)
    retry_count = state.get("retry_count", 0)

    logger.info(
        "graph.route_after_critique",
        passed=critique_passed,
        retry=retry_count,
        max=MAX_RETRIES,
    )

    # Always finalize if:
    # 1. Critique passed
    # 2. Already retried MAX_RETRIES times
    # 3. retry_count is at or above limit
    if critique_passed or retry_count >= MAX_RETRIES:
        return "finalize"

    # Only retry once
    state["retry_count"] = retry_count + 1
    logger.info("graph.critique.retrying", retry=state["retry_count"])
    return "aggregator"


def route_account(
    state: BankingAssistantState,
) -> Literal["account_agent", "loan_agent"]:
    if "account" in state.get("agents_to_invoke", []):
        return "account_agent"
    return "loan_agent"


def route_loan(
    state: BankingAssistantState,
) -> Literal["loan_agent", "compliance_agent"]:
    if "loan" in state.get("agents_to_invoke", []):
        return "loan_agent"
    return "compliance_agent"


def route_compliance(
    state: BankingAssistantState,
) -> Literal["compliance_agent", "fraud_agent"]:
    if "compliance" in state.get("agents_to_invoke", []):
        return "compliance_agent"
    return "fraud_agent"



def build_banking_graph() -> StateGraph:
    workflow = StateGraph(BankingAssistantState)

    # Add all nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("router", router_node)
    workflow.add_node("account_agent", account_agent_node)
    workflow.add_node("loan_agent", loan_agent_node)
    workflow.add_node("compliance_agent", compliance_agent_node)
    workflow.add_node("fraud_agent", fraud_agent_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("critique", critique_node)
    workflow.add_node("finalize", finalize_node)

    # Entry point
    workflow.set_entry_point("planner")

    # Planner -> Router
    workflow.add_edge("planner", "router")

    # Router -> first agent
    workflow.add_conditional_edges(
        "router",
        route_account,
        {
            "account_agent": "account_agent",
            "loan_agent": "loan_agent",
        },
    )

    # Account -> Loan or skip
    workflow.add_conditional_edges(
        "account_agent",
        route_loan,
        {
            "loan_agent": "loan_agent",
            "compliance_agent": "compliance_agent",
        },
    )

    # Loan -> Compliance or skip
    workflow.add_conditional_edges(
        "loan_agent",
        route_compliance,
        {
            "compliance_agent": "compliance_agent",
            "fraud_agent": "fraud_agent",
        },
    )

    # Compliance -> Fraud always
    workflow.add_edge("compliance_agent", "fraud_agent")

    # Fraud -> Human Review or Aggregator
    workflow.add_conditional_edges(
        "fraud_agent",
        route_after_fraud,
        {
            "human_review": "human_review",
            "aggregator": "aggregator",
        },
    )

    # Human Review -> Aggregator
    workflow.add_edge("human_review", "aggregator")

    # Aggregator -> Critique
    workflow.add_edge("aggregator", "critique")

    # Critique -> Aggregator (retry) or Finalize
    workflow.add_conditional_edges(
        "critique",
        route_after_critique,
        {
            "aggregator": "aggregator",
            "finalize": "finalize",
        },
    )

    # Finalize -> END
    workflow.add_edge("finalize", END)

    return workflow


#  Compiled Graph 

_checkpointer = MemorySaver()


def get_compiled_graph():
    workflow = build_banking_graph()
    return workflow.compile(
        checkpointer=_checkpointer,
        interrupt_before=["human_review"],
    )



@traceable(name="banking_assistant_query")
def run_query(
    query: str,
    customer_id: str,
    session_id: str = None,
    conversation_history: list = None,
) -> dict:
    session_id = session_id or str(uuid.uuid4())
    start_time = time.time()

    audit_service.create_session(
        session_id=session_id,
        customer_id=customer_id,
    )

    logger.info("graph.query.start",
               session_id=session_id,
               customer_id=customer_id,
               query=query[:100])

    graph = get_compiled_graph()
    initial_state = create_initial_state(
        query=query,
        customer_id=customer_id,
        session_id=session_id,
        conversation_history=conversation_history or [],
    )
    config = {"configurable": {"thread_id": session_id}}

    try:
        final_state = graph.invoke(initial_state, config=config)
        total_latency = round((time.time() - start_time) * 1000)

        audit_service.complete_session(
            session_id=session_id,
            total_latency_ms=total_latency,
            risk_level=final_state.get("risk_level", "low"),
            required_human=final_state.get("requires_human", False),
            agents_invoked=final_state.get("agents_to_invoke", []),
            intents=final_state.get("intent", []),
            status="completed",
        )

        logger.info("graph.query.complete",
                   session_id=session_id,
                   latency_ms=total_latency,
                   retry_count=final_state.get("retry_count", 0))

        return {
            "success": True,
            "session_id": session_id,
            "response": final_state["final_response"],
            "risk_level": final_state["risk_level"],
            "requires_human": final_state["requires_human"],
            "agents_invoked": final_state["agents_to_invoke"],
            "intents": final_state["intent"],
            "mcp_calls_log": final_state["mcp_calls_log"],
            "kg_queries_log": final_state["kg_queries_log"],
            "agent_outputs": final_state["agent_outputs"],
            "planner_plan": final_state.get("planner_plan", {}),
            "critique_result": final_state.get("critique_result", {}),
            "query_complexity": final_state.get("query_complexity"),
            "total_latency_ms": total_latency,
            "metadata": final_state.get("response_metadata", {}),
        }

    except Exception as e:
        total_latency = round((time.time() - start_time) * 1000)
        logger.error("graph.query.failed",
                    session_id=session_id,
                    error=str(e),
                    exc_info=True)
        audit_service.complete_session(
            session_id=session_id,
            total_latency_ms=total_latency,
            risk_level="low",
            required_human=False,
            agents_invoked=[],
            intents=[],
            status="failed",
        )
        return {
            "success": False,
            "session_id": session_id,
            "error": str(e),
            "response": (
                "I apologize, I encountered an error processing your request. "
                "Please try again or call 1800-123-4567."
            ),
            "total_latency_ms": total_latency,
        }