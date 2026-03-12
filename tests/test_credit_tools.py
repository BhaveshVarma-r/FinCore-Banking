import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.mcp_servers.credit_server import (
    get_credit_profile, check_loan_eligibility, get_emi_schedule,
)


class TestGetCreditProfile:
    def test_valid_customer(self):
        result = get_credit_profile("CUST1001")
        assert result["success"] is True
        assert 300 <= result["credit_score"] <= 900
        assert 0 <= result["foir"] <= 2

    def test_invalid_customer(self):
        result = get_credit_profile("CUST9999")
        assert result["success"] is False
        assert result["error"] == "customer_not_found"

    def test_score_band_present(self):
        result = get_credit_profile("CUST1001")
        if result["success"]:
            assert "score_band" in result
            assert len(result["score_band"]) > 0


class TestCheckLoanEligibility:
    def test_returns_boolean_eligible(self):
        result = check_loan_eligibility("CUST1001", 2000000, "home")
        assert result["success"] is True
        assert isinstance(result["eligible"], bool)
        assert "reasons" in result
        assert result["max_eligible_amount"] >= 0

    def test_invalid_customer(self):
        result = check_loan_eligibility("CUST9999", 1000000, "personal")
        assert result["success"] is False

    def test_all_loan_types_accepted(self):
        for lt in ["home", "personal", "car", "education", "msme", "gold"]:
            result = check_loan_eligibility("CUST1001", 500000, lt)
            assert result["success"] is True


class TestGetEmiSchedule:
    def test_invalid_loan_returns_error(self):
        result = get_emi_schedule("LOAN9999")
        assert result["success"] is False
        assert result["error"] == "loan_not_found"