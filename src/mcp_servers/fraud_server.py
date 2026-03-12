"""
Fraud MCP Server - transaction risk scoring, alerts, flagging
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

DATA_DIR = Path(__file__).parent.parent.parent / "data"

def _load(filename: str) -> list:
    with open(DATA_DIR / filename) as f:
        return json.load(f)

_customers = {c["id"]: c for c in _load("mock_customers.json")}
_accounts_raw = _load("mock_accounts.json")
_accounts = {a["id"]: a for a in _accounts_raw}
_transactions_raw = _load("mock_transactions.json")
_transactions_all = {t["id"]: t for t in _transactions_raw}
_known_payees = {t["payee_id"] for t in _transactions_raw}
_accounts_by_customer: dict[str, list] = {}
for _a in _accounts_raw:
    _accounts_by_customer.setdefault(_a["customer_id"], []).append(_a)

mcp = FastMCP("fraud_mcp")


@mcp.tool()
def score_transaction_risk(
    transaction_id: str,
    amount: float,
    payee_id: str,
    customer_id: str = "",
) -> dict[str, Any]:
    """
    Score a transaction for fraud risk using rule-based heuristics.
    Returns risk_score (0-1), risk_level, flags, and recommended_action.
    risk_score >= 0.7 triggers human escalation.
    """
    flags = []
    risk_score = 0.0

    existing = _transactions_all.get(transaction_id)
    if existing:
        risk_score = existing.get("risk_score", 0.0)
        if existing.get("is_flagged"):
            flags.append("previously_flagged")
    else:
        if amount > 200000:
            risk_score += 0.25
            flags.append("high_amount")
        if amount > 500000:
            risk_score += 0.15
            flags.append("very_high_amount")
        if payee_id not in _known_payees:
            risk_score += 0.30
            flags.append("unknown_payee")
        if customer_id and customer_id in _customers:
            cust_accounts = {a["id"] for a in _accounts_by_customer.get(customer_id, [])}
            prior_flags = [
                t for t in _transactions_raw
                if t.get("account_id") in cust_accounts and t.get("is_flagged")
            ]
            if len(prior_flags) > 2:
                risk_score += 0.20
                flags.append("customer_has_fraud_history")
        risk_score = min(1.0, risk_score)

    risk_level = (
        "critical" if risk_score >= 0.9 else
        "high" if risk_score >= 0.7 else
        "medium" if risk_score >= 0.4 else
        "low"
    )
    recommended_action = (
        "BLOCK_AND_ESCALATE" if risk_score >= 0.9 else
        "ESCALATE_TO_HUMAN" if risk_score >= 0.7 else
        "FLAG_FOR_REVIEW" if risk_score >= 0.4 else
        "ALLOW"
    )

    return {
        "success": True,
        "transaction_id": transaction_id,
        "amount": amount,
        "payee_id": payee_id,
        "risk_score": round(risk_score, 3),
        "risk_level": risk_level,
        "flags": flags,
        "recommended_action": recommended_action,
        "requires_human_review": risk_score >= 0.7,
        "scored_at": datetime.now().isoformat(),
    }


@mcp.tool()
def get_fraud_alerts(customer_id: str) -> dict[str, Any]:
    """
    Get all active fraud alerts and flagged transactions for a customer.
    Returns list of flagged transactions with risk scores and payee details.
    """
    if customer_id not in _customers:
        return {"success": False, "error": "customer_not_found",
                "message": f"No customer found with ID {customer_id}"}

    account_ids = {a["id"] for a in _accounts_by_customer.get(customer_id, [])}
    flagged = [
        t for t in _transactions_raw
        if t.get("account_id") in account_ids and t.get("is_flagged")
    ]

    alerts = [
        {
            "transaction_id": t["id"],
            "amount": t["amount"],
            "payee_id": t["payee_id"],
            "payee_name": t["payee_name"],
            "channel": t["channel"],
            "timestamp": t["timestamp"],
            "risk_score": t["risk_score"],
            "account_id": t["account_id"],
        }
        for t in flagged
    ]

    return {
        "success": True,
        "customer_id": customer_id,
        "total_alerts": len(alerts),
        "active_alerts": alerts[:10],
        "high_risk_count": len([a for a in alerts if a["risk_score"] > 0.7]),
    }


@mcp.tool()
def flag_transaction(
    transaction_id: str,
    reason: str,
    flagged_by: str = "system",
) -> dict[str, Any]:
    """
    Flag a transaction for fraud investigation and open a case.
    Returns case_id, next_steps, and provisional credit eligibility.
    """
    case_id = f"CASE{str(uuid.uuid4())[:8].upper()}"
    return {
        "success": True,
        "transaction_id": transaction_id,
        "case_id": case_id,
        "flagged_by": flagged_by,
        "reason": reason,
        "status": "under_investigation",
        "next_steps": [
            "Transaction has been temporarily blocked.",
            f"Fraud investigation case {case_id} opened.",
            "You will receive an SMS/email update within 24 hours.",
            "Contact 1800-123-4567 for immediate assistance.",
            "File dispute within 3 working days if unauthorized.",
        ],
        "provisional_credit": "Eligible for provisional credit within 10 working days.",
        "flagged_at": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")