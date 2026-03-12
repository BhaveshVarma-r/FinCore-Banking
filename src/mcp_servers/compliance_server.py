"""
Compliance MCP Server - RBI/DPDP regulations, document requirements, product rules
"""
import json
from pathlib import Path
from typing import Any, Optional

from fastmcp import FastMCP

DATA_DIR = Path(__file__).parent.parent.parent / "data"

def _load(filename: str) -> list:
    with open(DATA_DIR / filename) as f:
        return json.load(f)

_regulations = _load("mock_regulation_rules.json")
_products = {p["id"]: p for p in _load("mock_products.json")}

DOCUMENT_REQUIREMENTS = {
    "home": {
        "Personal": ["Aadhaar Card", "PAN Card", "2 Passport Photos"],
        "Income": ["Last 3 years ITR", "Last 3 months salary slips", "Form 16"],
        "Property": ["Sale agreement", "NOC from builder", "Approved building plan",
                     "Title deed", "Encumbrance certificate"],
    },
    "msme": {
        "Personal": ["Aadhaar Card", "PAN Card of business and promoter"],
        "Business": ["GST registration", "Udyam Registration", "Business vintage proof (2+ years)"],
        "Financial": ["Last 2 years audited financials", "Last 6 months bank statements",
                      "GST returns (12 months)", "ITR last 2 years"],
    },
    "personal": {
        "Personal": ["Aadhaar Card", "PAN Card"],
        "Income": ["Last 3 months salary slips", "Last 6 months bank statements", "Form 16"],
    },
    "car": {
        "Personal": ["Aadhaar Card", "PAN Card", "Driving License"],
        "Income": ["Last 3 months salary slips", "Last 3 months bank statements"],
        "Vehicle": ["Proforma invoice from dealer"],
    },
    "education": {
        "Personal": ["Aadhaar Card", "PAN Card", "Birth Certificate"],
        "Academic": ["Admission letter", "Fee structure", "Last exam mark sheets"],
        "Co-Applicant": ["Parent KYC", "Co-applicant income proof"],
    },
    "gold": {
        "Personal": ["Aadhaar Card", "PAN Card"],
        "Collateral": ["Gold valuation certificate", "Original gold items for pledge"],
    },
}

mcp = FastMCP("compliance_mcp")


@mcp.tool()
def get_regulations(
    applies_to: str = "",
    source: str = "",
) -> dict[str, Any]:
    """
    Fetch RBI or DPDP regulations, optionally filtered.
    applies_to: home_loan | personal_loan | msme_loan | all_accounts | fraud_transactions | credit_card | dormant_accounts
    source: RBI | DPDP
    """
    filtered = _regulations
    if applies_to:
        filtered = [r for r in filtered if applies_to.lower() in r.get("applies_to", "").lower()]
    if source:
        filtered = [r for r in filtered if r.get("source", "").upper() == source.upper()]
    return {
        "success": True,
        "total": len(filtered),
        "regulations": filtered,
    }


@mcp.tool()
def get_document_requirements(loan_type: str) -> dict[str, Any]:
    """
    Return complete document checklist for a loan application.
    loan_type: home | personal | msme | car | education | gold
    Returns categorized mandatory document list.
    """
    key = loan_type.lower().replace(" loan", "").replace(" ", "_")
    docs = DOCUMENT_REQUIREMENTS.get(key)

    if not docs:
        for k in DOCUMENT_REQUIREMENTS:
            if k in key or key in k:
                docs = DOCUMENT_REQUIREMENTS[k]
                key = k
                break

    if not docs:
        return {
            "success": False,
            "error": "loan_type_not_found",
            "available_types": list(DOCUMENT_REQUIREMENTS.keys()),
        }

    all_docs = []
    for category, doc_list in docs.items():
        for doc in doc_list:
            all_docs.append({"document": doc, "category": category, "mandatory": True})

    return {
        "success": True,
        "loan_type": key,
        "total_documents": len(all_docs),
        "document_checklist": all_docs,
        "categorized": docs,
        "note": (
            "All documents must be self-attested. "
            "Originals required at branch for verification."
        ),
    }


@mcp.tool()
def check_product_eligibility_rules(
    product_id: str,
    customer_segment: str,
    credit_score: int,
) -> dict[str, Any]:
    """
    Verify compliance rules for a product upgrade or new application.
    Returns compliance_passes (bool), issues, and applicable regulations.
    """
    if product_id not in _products:
        return {"success": False, "error": "product_not_found",
                "message": f"Product {product_id} not found"}

    product = _products[product_id]
    criteria = product.get("eligibility_criteria", "")
    issues = []
    passes = True

    if "credit_score >=" in criteria:
        try:
            min_score = int(criteria.split("credit_score >=")[1].split(",")[0].strip())
            if credit_score < min_score:
                passes = False
                issues.append(f"Credit score {credit_score} below required {min_score}.")
        except ValueError:
            pass

    if "kyc_verified" in criteria and customer_segment == "new":
        issues.append("KYC must be verified before product eligibility.")

    relevant_regs = [
        r for r in _regulations
        if product.get("category", "") in r.get("applies_to", "")
        or "all_data" in r.get("applies_to", "")
    ][:3]

    return {
        "success": True,
        "product_id": product_id,
        "product_name": product["name"],
        "product_category": product["category"],
        "compliance_passes": passes,
        "eligibility_criteria": criteria,
        "compliance_issues": issues,
        "applicable_regulations": relevant_regs,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")