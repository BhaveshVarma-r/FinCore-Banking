"""
Core Banking MCP Server - runs as a standalone FastMCP process
Tools: get_account_summary, get_transactions, get_inactive_accounts, check_transfer_status
"""
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

DATA_DIR = Path(__file__).parent.parent.parent / "data"

def _load(filename: str) -> list:
    with open(DATA_DIR / filename) as f:
        return json.load(f)

# Load data at startup
_customers = {c["id"]: c for c in _load("mock_customers.json")}
_accounts_raw = _load("mock_accounts.json")
_accounts = {a["id"]: a for a in _accounts_raw}
_accounts_by_customer: dict[str, list] = {}
for _a in _accounts_raw:
    _accounts_by_customer.setdefault(_a["customer_id"], []).append(_a)
_transactions_raw = _load("mock_transactions.json")
_transactions_by_account: dict[str, list] = {}
_transactions_all = {t["id"]: t for t in _transactions_raw}
for _t in _transactions_raw:
    _transactions_by_account.setdefault(_t["account_id"], []).append(_t)

mcp = FastMCP("core_banking_mcp")


@mcp.tool()
def get_account_summary(customer_id: str) -> dict[str, Any]:
    """
    Fetch all accounts and current balances for a customer.
    Returns list of accounts with balance, type, status, branch.
    """
    if customer_id not in _customers:
        return {"success": False, "error": "customer_not_found",
                "message": f"No customer found with ID {customer_id}"}

    customer = _customers[customer_id]
    accounts = _accounts_by_customer.get(customer_id, [])

    formatted = [
        {
            "account_id": a["id"],
            "account_type": a["type"].replace("_", " ").title(),
            "balance": a["balance"],
            "status": a["status"],
            "last_transaction_date": a["last_txn_date"],
            "branch": a["branch"],
            "ifsc": a["ifsc"],
            "opened_date": a["opened_date"],
        }
        for a in accounts
    ]

    return {
        "success": True,
        "customer_id": customer_id,
        "customer_name": customer["name"],
        "total_accounts": len(formatted),
        "accounts": formatted,
        "total_balance": round(
            sum(a["balance"] for a in formatted if a["status"] == "active"), 2
        ),
    }


@mcp.tool()
def get_transactions(account_id: str, limit: int = 5) -> dict[str, Any]:
    """
    Get recent transaction history for a specific account.
    Returns transactions sorted by date descending.
    limit must be between 1 and 50.
    """
    if limit > 50:
        return {"success": False, "error": "limit_exceeded",
                "message": "Maximum limit is 50 transactions"}
    if account_id not in _accounts:
        return {"success": False, "error": "account_not_found",
                "message": f"No account found with ID {account_id}"}

    txns = sorted(
        _transactions_by_account.get(account_id, []),
        key=lambda x: x["timestamp"],
        reverse=True,
    )[:limit]

    return {
        "success": True,
        "account_id": account_id,
        "account_type": _accounts[account_id]["type"],
        "current_balance": _accounts[account_id]["balance"],
        "transactions": [
            {
                "transaction_id": t["id"],
                "amount": t["amount"],
                "type": t["type"],
                "description": t["description"],
                "payee": t["payee_name"],
                "payee_id": t["payee_id"],
                "channel": t["channel"],
                "timestamp": t["timestamp"],
                "is_flagged": t.get("is_flagged", False),
            }
            for t in txns
        ],
    }


@mcp.tool()
def get_inactive_accounts(customer_id: str, inactive_months: int = 6) -> dict[str, Any]:
    """
    Identify accounts with no activity for the specified number of months.
    Returns all accounts with activity classification and months since last transaction.
    """
    if customer_id not in _customers:
        return {"success": False, "error": "customer_not_found",
                "message": f"No customer found with ID {customer_id}"}

    accounts = _accounts_by_customer.get(customer_id, [])
    now = datetime.now()
    threshold = now - timedelta(days=inactive_months * 30)

    result = []
    for a in accounts:
        last_txn = datetime.strptime(a["last_txn_date"], "%Y-%m-%d")
        months_since = (now - last_txn).days // 30
        result.append({
            "account_id": a["id"],
            "account_type": a["type"],
            "balance": a["balance"],
            "status": a["status"],
            "last_transaction_date": a["last_txn_date"],
            "months_since_last_transaction": months_since,
            "is_inactive": last_txn < threshold,
        })

    inactive = [a for a in result if a["is_inactive"]]
    return {
        "success": True,
        "customer_id": customer_id,
        "total_accounts": len(result),
        "inactive_count": len(inactive),
        "all_accounts": result,
        "inactive_accounts": inactive,
    }


@mcp.tool()
def check_transfer_status(transaction_id: str) -> dict[str, Any]:
    """
    Check the processing status of a specific transaction or transfer.
    Returns status, amount, timestamp, and channel.
    """
    if transaction_id in _transactions_all:
        t = _transactions_all[transaction_id]
        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": "completed",
            "amount": t["amount"],
            "type": t["type"],
            "timestamp": t["timestamp"],
            "channel": t["channel"],
            "is_flagged": t.get("is_flagged", False),
        }
    return {
        "success": True,
        "transaction_id": transaction_id,
        "status": "pending",
        "message": "Transaction is being processed. NEFT may take 2-4 hours.",
        "estimated_credit_time": "2-4 hours",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")