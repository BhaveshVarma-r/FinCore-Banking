from typing import Any, Dict, List, Optional, TypedDict


class BankingAssistantState(TypedDict):
    # Input
    query: str
    customer_id: str
    session_id: str
    conversation_history: List[Dict]

    # Planner output
    planner_plan: Dict[str, Any]
    query_complexity: str

    # Routing
    intent: List[str]
    agents_to_invoke: List[str]
    routing_confidence: Dict[str, float]

    # Agent outputs
    agent_outputs: Dict[str, Any]

    # Data layer logs
    mcp_calls_log: List[Dict]
    kg_queries_log: List[str]

    # Risk
    risk_level: str
    requires_human: bool

    # Critique
    critique_result: Dict[str, Any]
    critique_passed: bool
    retry_count: int

    # Output
    final_response: str
    response_metadata: Dict[str, Any]

    # Errors
    errors: List[str]


def create_initial_state(
    query: str,
    customer_id: str,
    session_id: str,
    conversation_history: List[Dict] = None,
) -> BankingAssistantState:
    return BankingAssistantState(
        query=query,
        customer_id=customer_id,
        session_id=session_id,
        conversation_history=conversation_history or [],
        planner_plan={},
        query_complexity="simple",
        intent=[],
        agents_to_invoke=[],
        routing_confidence={},
        agent_outputs={},
        mcp_calls_log=[],
        kg_queries_log=[],
        risk_level="low",
        requires_human=False,
        critique_result={},
        critique_passed=False,
        retry_count=0,
        final_response="",
        response_metadata={},
        errors=[],
    )