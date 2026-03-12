import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.mcp_servers.core_banking_server import (
    get_account_summary, get_transactions,
    get_inactive_accounts, check_transfer_status,
)


class TestGetAccountSummary:
    def test_valid_customer_returns_accounts(self):
        result = get_account_summary("CUST1001")
        assert result["success"] is True
        assert "accounts" in result
        assert result["customer_id"] == "CUST1001"

    def test_invalid_customer_returns_error(self):
        result = get_account_summary("CUST9999")
        assert result["success"] is False
        assert result["error"] == "customer_not_found"

    def test_account_has_required_fields(self):
        result = get_account_summary("CUST1001")
        if result["success"] and result["accounts"]:
            acc = result["accounts"][0]
            for field in ["account_id", "balance", "status", "account_type"]:
                assert field in acc

    def test_total_balance_only_active(self):
        result = get_account_summary("CUST1001")
        if result["success"]:
            active_sum = sum(
                a["balance"] for a in result["accounts"] if a["status"] == "active"
            )
            assert abs(result["total_balance"] - active_sum) < 0.01


class TestGetTransactions:
    def test_limit_exceeded_returns_error(self):
        result = get_transactions("ACC2001", limit=51)
        assert result["success"] is False
        assert result["error"] == "limit_exceeded"

    def test_invalid_account_returns_error(self):
        result = get_transactions("ACC9999")
        assert result["success"] is False
        assert result["error"] == "account_not_found"

    def test_transactions_have_required_fields(self):
        result = get_transactions("ACC2001", limit=3)
        if result["success"] and result["transactions"]:
            txn = result["transactions"][0]
            for field in ["transaction_id", "amount", "timestamp", "type"]:
                assert field in txn


class TestGetInactiveAccounts:
    def test_returns_inactive_classification(self):
        result = get_inactive_accounts("CUST1001", inactive_months=6)
        if result["success"]:
            for acc in result["all_accounts"]:
                assert "is_inactive" in acc
                assert "months_since_last_transaction" in acc

    def test_invalid_customer_returns_error(self):
        result = get_inactive_accounts("INVALID123")
        assert result["success"] is False
        assert result["error"] == "customer_not_found"


class TestCheckTransferStatus:
    def test_unknown_transaction_returns_pending(self):
        result = check_transfer_status("TXN_UNKNOWN_999")
        assert result["success"] is True
        assert result["status"] == "pending"