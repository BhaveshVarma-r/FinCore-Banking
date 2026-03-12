"""
Credit MCP Client
"""
import time
from typing import Any
from src.mcp_client.client_manager import call_tool_sync
import structlog

logger = structlog.get_logger(__name__)

SERVER = "credit"


def get_credit_profile(customer_id: str) -> dict[str, Any]:
    start = time.time()
    result = call_tool_sync(
        SERVER,
        "get_credit_profile",
        {"customer_id": customer_id},
    )
    logger.info(
        "mcp.credit.get_credit_profile",
        customer_id=customer_id,
        latency_ms=round((time.time() - start) * 1000),
    )
    return result


def check_loan_eligibility(
    customer_id: str,
    amount: float,
    loan_type: str,
) -> dict[str, Any]:
    start = time.time()
    result = call_tool_sync(
        SERVER,
        "check_loan_eligibility",
        {
            "customer_id": customer_id,
            "amount": amount,
            "loan_type": loan_type,
        },
    )
    logger.info(
        "mcp.credit.check_loan_eligibility",
        customer_id=customer_id,
        loan_type=loan_type,
        latency_ms=round((time.time() - start) * 1000),
    )
    return result


def get_emi_schedule(loan_id: str) -> dict[str, Any]:
    start = time.time()
    result = call_tool_sync(
        SERVER,
        "get_emi_schedule",
        {"loan_id": loan_id},
    )
    logger.info(
        "mcp.credit.get_emi_schedule",
        loan_id=loan_id,
        latency_ms=round((time.time() - start) * 1000),
    )
    return result