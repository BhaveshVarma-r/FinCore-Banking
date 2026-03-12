"""
Compliance MCP Client
"""
import time
from typing import Any
from src.mcp_client.client_manager import call_tool_sync
import structlog

logger = structlog.get_logger(__name__)

SERVER = "compliance"


def get_regulations(
    applies_to: str = "",
    source: str = "",
) -> dict[str, Any]:
    start = time.time()
    result = call_tool_sync(
        SERVER,
        "get_regulations",
        {"applies_to": applies_to, "source": source},
    )
    logger.info(
        "mcp.compliance.get_regulations",
        applies_to=applies_to,
        latency_ms=round((time.time() - start) * 1000),
    )
    return result


def get_document_requirements(loan_type: str) -> dict[str, Any]:
    start = time.time()
    result = call_tool_sync(
        SERVER,
        "get_document_requirements",
        {"loan_type": loan_type},
    )
    logger.info(
        "mcp.compliance.get_document_requirements",
        loan_type=loan_type,
        latency_ms=round((time.time() - start) * 1000),
    )
    return result


def check_product_eligibility_rules(
    product_id: str,
    customer_segment: str,
    credit_score: int,
) -> dict[str, Any]:
    start = time.time()
    result = call_tool_sync(
        SERVER,
        "check_product_eligibility_rules",
        {
            "product_id": product_id,
            "customer_segment": customer_segment,
            "credit_score": credit_score,
        },
    )
    logger.info(
        "mcp.compliance.check_product_eligibility_rules",
        product_id=product_id,
        latency_ms=round((time.time() - start) * 1000),
    )
    return result