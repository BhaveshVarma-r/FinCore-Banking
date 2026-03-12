"""
Core Banking MCP Client
"""
import time
from typing import Any
from src.mcp_client.client_manager import call_tool_sync
import structlog

logger = structlog.get_logger(__name__)

SERVER = "core_banking"


def get_account_summary(customer_id: str) -> dict[str, Any]:
    start = time.time()
    result = call_tool_sync(
        SERVER,
        "get_account_summary",
        {"customer_id": customer_id},
    )
    logger.info(
        "mcp.core_banking.get_account_summary",
        customer_id=customer_id,
        success=result.get("success"),
        latency_ms=round((time.time() - start) * 1000),
    )
    return result


def get_transactions(account_id: str, limit: int = 5) -> dict[str, Any]:
    start = time.time()
    result = call_tool_sync(
        SERVER,
        "get_transactions",
        {"account_id": account_id, "limit": limit},
    )
    logger.info(
        "mcp.core_banking.get_transactions",
        account_id=account_id,
        latency_ms=round((time.time() - start) * 1000),
    )
    return result


def get_inactive_accounts(
    customer_id: str, inactive_months: int = 6
) -> dict[str, Any]:
    start = time.time()
    result = call_tool_sync(
        SERVER,
        "get_inactive_accounts",
        {"customer_id": customer_id, "inactive_months": inactive_months},
    )
    logger.info(
        "mcp.core_banking.get_inactive_accounts",
        customer_id=customer_id,
        latency_ms=round((time.time() - start) * 1000),
    )
    return result


def check_transfer_status(transaction_id: str) -> dict[str, Any]:
    start = time.time()
    result = call_tool_sync(
        SERVER,
        "check_transfer_status",
        {"transaction_id": transaction_id},
    )
    logger.info(
        "mcp.core_banking.check_transfer_status",
        transaction_id=transaction_id,
        latency_ms=round((time.time() - start) * 1000),
    )
    return result