"""
Credit MCP Server - credit scores, EMI schedules, loan eligibility
"""
import json
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

DATA_DIR = Path(__file__).parent.parent.parent / "data"

def _load(filename: str) -> list:
    with open(DATA_DIR / filename) as f:
        return json.load(f)

_customers = {c["id"]: c for c in _load("mock_customers.json")}
_loans_raw = _load("mock_loans.json")
_loans_all = {l["id"]: l for l in _loans_raw}
_loans_by_customer: dict[str, list] = {}
for _l in _loans_raw:
    _loans_by_customer.setdefault(_l["customer_id"], []).append(_l)

mcp = FastMCP("credit_mcp")


@mcp.tool()
def get_credit_profile(customer_id: str) -> dict[str, Any]:
    """
    Fetch complete credit profile: score, band, active EMIs, FOIR, outstanding.
    FOIR = Fixed Obligation to Income Ratio (should be <= 0.5 per RBI).
    """
    if customer_id not in _customers:
        return {"success": False, "error": "customer_not_found",
                "message": f"No customer found with ID {customer_id}"}

    c = _customers[customer_id]
    active_loans = [l for l in _loans_by_customer.get(customer_id, [])
                    if l["status"] == "active"]
    total_emi = sum(l["emi"] for l in active_loans)
    total_outstanding = sum(l["outstanding"] for l in active_loans)
    monthly_income = c["annual_income"] / 12
    foir = (total_emi / monthly_income) if monthly_income > 0 else 0
    score = c["credit_score"]

    score_band = (
        "Excellent (750-850)" if score >= 750 else
        "Good (700-749)" if score >= 700 else
        "Fair (650-699)" if score >= 650 else
        "Poor (550-649)" if score >= 550 else
        "Very Poor (<550)"
    )

    return {
        "success": True,
        "customer_id": customer_id,
        "credit_score": score,
        "score_band": score_band,
        "active_loans_count": len(active_loans),
        "total_monthly_emi": round(total_emi, 2),
        "total_outstanding": round(total_outstanding, 2),
        "monthly_income": round(monthly_income, 2),
        "annual_income": c["annual_income"],
        "foir": round(foir, 3),
        "foir_percentage": f"{round(foir * 100, 1)}%",
        "kyc_status": c["kyc_status"],
        "active_loan_details": [
            {
                "loan_id": l["id"],
                "type": l["type"],
                "emi": l["emi"],
                "outstanding": l["outstanding"],
                "interest_rate": l["interest_rate"],
            }
            for l in active_loans
        ],
    }


@mcp.tool()
def check_loan_eligibility(
    customer_id: str,
    amount: float,
    loan_type: str,
) -> dict[str, Any]:
    """
    Determine loan eligibility using RBI FOIR rules and credit score thresholds.
    loan_type: home | personal | car | education | msme | gold
    Returns eligible (bool), max_eligible_amount, reasons, and FOIR details.
    """
    if customer_id not in _customers:
        return {"success": False, "error": "customer_not_found",
                "message": f"No customer found with ID {customer_id}"}

    c = _customers[customer_id]
    active_loans = [l for l in _loans_by_customer.get(customer_id, [])
                    if l["status"] == "active"]
    total_emi = sum(l["emi"] for l in active_loans)
    monthly_income = c["annual_income"] / 12
    credit_score = c["credit_score"]

    reasons = []
    eligible = True

    if c["kyc_status"] != "verified":
        eligible = False
        reasons.append(f"KYC status is '{c['kyc_status']}'. Must be verified.")

    min_score_map = {
        "home": 650, "personal": 680, "car": 650,
        "education": 600, "msme": 620, "gold": 580,
    }
    min_score = min_score_map.get(loan_type.lower(), 650)
    if credit_score < min_score:
        eligible = False
        reasons.append(
            f"Credit score {credit_score} is below minimum {min_score} for {loan_type} loan."
        )

    estimated_new_emi = amount * 0.015
    projected_foir = (total_emi + estimated_new_emi) / monthly_income if monthly_income > 0 else 1
    if projected_foir > 0.5:
        eligible = False
        reasons.append(
            f"Projected FOIR {round(projected_foir * 100, 1)}% exceeds RBI limit of 50%. "
            f"Current EMIs: Rs.{round(total_emi, 0)}/month, Income: Rs.{round(monthly_income, 0)}/month."
        )

    available_capacity = max(0, (monthly_income * 0.5) - total_emi)
    max_eligible = min(available_capacity / 0.015, amount)
    if loan_type.lower() == "home":
        max_eligible = min(max_eligible, monthly_income * 60)

    return {
        "success": True,
        "customer_id": customer_id,
        "loan_type": loan_type,
        "requested_amount": amount,
        "eligible": eligible,
        "max_eligible_amount": round(max(0, max_eligible), 2),
        "reasons": reasons if reasons else ["All eligibility criteria met."],
        "credit_score": credit_score,
        "current_foir": round((total_emi / monthly_income) if monthly_income > 0 else 0, 3),
        "projected_foir": round(projected_foir, 3),
        "monthly_income": round(monthly_income, 2),
        "existing_emis": round(total_emi, 2),
        "kyc_status": c["kyc_status"],
    }


@mcp.tool()
def get_emi_schedule(loan_id: str) -> dict[str, Any]:
    """
    Return EMI schedule and repayment details for a specific loan.
    Returns emi_amount, outstanding, tenure, emis_paid, emis_remaining.
    """
    if loan_id not in _loans_all:
        return {"success": False, "error": "loan_not_found",
                "message": f"No loan found with ID {loan_id}"}

    l = _loans_all[loan_id]
    emis_paid = int((l["amount"] - l["outstanding"]) / l["emi"]) if l["emi"] > 0 else 0
    return {
        "success": True,
        "loan_id": loan_id,
        "loan_type": l["type"],
        "principal": l["amount"],
        "outstanding": l["outstanding"],
        "emi_amount": l["emi"],
        "interest_rate": l["interest_rate"],
        "tenure_months": l["tenure_months"],
        "emis_paid": emis_paid,
        "emis_remaining": max(0, l["tenure_months"] - emis_paid),
        "next_emi_date": l["next_emi_date"],
        "status": l["status"],
        "disbursed_date": l["disbursed_date"],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")