"""
Fraud MCP Client
"""
import time
from typing import Any
from src.mcp_client.client_manager import call_tool_sync
import structlog

logger = structlog.get_logger(__name__)

SERVER = "fraud"


def score_transaction_risk(
    transaction_id: str,
    amount: float,
    payee_id: str,
    customer_id: str = "",
) -> dict[str, Any]:
    start = time.time()
    result = call_tool_sync(
        SERVER,
        "score_transaction_risk",
        {
            "transaction_id": transaction_id,
            "amount": amount,
            "payee_id": payee_id,
            "customer_id": customer_id,
        },
    )
    logger.info(
        "mcp.fraud.score_transaction_risk",
        transaction_id=transaction_id,
        latency_ms=round((time.time() - start) * 1000),
    )
    return result


def get_fraud_alerts(customer_id: str) -> dict[str, Any]:
    start = time.time()
    result = call_tool_sync(
        SERVER,
        "get_fraud_alerts",
        {"customer_id": customer_id},
    )
    logger.info(
        "mcp.fraud.get_fraud_alerts",
        customer_id=customer_id,
        latency_ms=round((time.time() - start) * 1000),
    )
    return result


def flag_transaction(
    transaction_id: str,
    reason: str,
    flagged_by: str = "system",
) -> dict[str, Any]:
    start = time.time()
    result = call_tool_sync(
        SERVER,
        "flag_transaction",
        {
            "transaction_id": transaction_id,
            "reason": reason,
            "flagged_by": flagged_by,
        },
    )
    logger.info(
        "mcp.fraud.flag_transaction",
        transaction_id=transaction_id,
        latency_ms=round((time.time() - start) * 1000),
    )
    return result