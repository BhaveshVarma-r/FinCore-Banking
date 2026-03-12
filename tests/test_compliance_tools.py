import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.mcp_servers.compliance_server import (
    get_regulations, get_document_requirements, check_product_eligibility_rules,
)


class TestGetRegulations:
    def test_returns_all_without_filter(self):
        result = get_regulations()
        assert result["success"] is True
        assert result["total"] > 0

    def test_filter_by_rbi(self):
        result = get_regulations(source="RBI")
        assert result["success"] is True
        for reg in result["regulations"]:
            assert reg["source"] == "RBI"

    def test_dpdp_regulations_exist(self):
        result = get_regulations(source="DPDP")
        assert result["total"] >= 1


class TestGetDocumentRequirements:
    def test_home_loan_docs(self):
        result = get_document_requirements("home")
        assert result["success"] is True
        assert result["total_documents"] > 0

    def test_msme_loan_docs(self):
        result = get_document_requirements("msme")
        assert result["success"] is True
        assert result["total_documents"] > 0

    def test_invalid_loan_type(self):
        result = get_document_requirements("alien_loan")
        assert result["success"] is False
        assert result["error"] == "loan_type_not_found"

    def test_documents_have_required_fields(self):
        result = get_document_requirements("personal")
        if result["success"]:
            for doc in result["document_checklist"]:
                assert "document" in doc
                assert "category" in doc
                assert "mandatory" in doc


class TestCheckProductEligibilityRules:
    def test_valid_product(self):
        result = check_product_eligibility_rules("PROD002", "retail", 720)
        assert result["success"] is True
        assert isinstance(result["compliance_passes"], bool)

    def test_invalid_product(self):
        result = check_product_eligibility_rules("PROD999", "retail", 700)
        assert result["success"] is False
        assert result["error"] == "product_not_found"