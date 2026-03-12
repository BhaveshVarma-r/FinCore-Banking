import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.mcp_servers.fraud_server import (
    score_transaction_risk, get_fraud_alerts, flag_transaction,
)


class TestScoreTransactionRisk:
    def test_valid_risk_score_range(self):
        result = score_transaction_risk("TXN001", 45000.0, "PAY5001", "CUST1001")
        assert result["success"] is True
        assert 0 <= result["risk_score"] <= 1
        assert result["risk_level"] in ["low", "medium", "high", "critical"]

    def test_recommended_action_present(self):
        result = score_transaction_risk("TXN002", 500000.0, "PAY_UNKNOWN")
        assert "recommended_action" in result
        assert result["recommended_action"] in [
            "ALLOW", "FLAG_FOR_REVIEW", "ESCALATE_TO_HUMAN", "BLOCK_AND_ESCALATE"
        ]

    def test_flags_list_is_list(self):
        result = score_transaction_risk("TXN003", 100.0, "PAY0001")
        assert isinstance(result["flags"], list)


class TestGetFraudAlerts:
    def test_valid_customer(self):
        result = get_fraud_alerts("CUST1001")
        assert result["success"] is True
        assert "total_alerts" in result
        assert isinstance(result["active_alerts"], list)

    def test_invalid_customer(self):
        result = get_fraud_alerts("CUST9999")
        assert result["success"] is False
        assert result["error"] == "customer_not_found"


class TestFlagTransaction:
    def test_creates_case_id(self):
        result = flag_transaction("TXN001", "Customer dispute", "customer")
        assert result["success"] is True
        assert result["case_id"].startswith("CASE")

    def test_case_ids_are_unique(self):
        r1 = flag_transaction("TXN002", "Reason 1")
        r2 = flag_transaction("TXN003", "Reason 2")
        assert r1["case_id"] != r2["case_id"]

    def test_next_steps_provided(self):
        result = flag_transaction("TXN004", "Unauthorized")
        assert len(result["next_steps"]) > 0