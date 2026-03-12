import json
import re
from typing import Any, Dict, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langsmith import traceable

from src.agents.base_agent import BaseAgent
from src.mcp_client import credit_client, compliance_client
from src.knowledge_graph.kg_queries import BankingKGQueries
from prompts.loader import load_prompt
import structlog

logger = structlog.get_logger(__name__)


class LoanAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(llm, "loan_agent")
        self.kg = BankingKGQueries()
        self.prompt = ChatPromptTemplate.from_template(load_prompt("loan_agent"))
        self.chain = self.prompt | self.llm | StrOutputParser()

    @traceable(name="loan_agent.run")
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        customer_id = state["customer_id"]
        query = state["query"]
        mcp_calls = []
        kg_queries = []

        loan_type, loan_amount = self._extract_loan_details(query)
        logger.info("loan_agent.extracted",
                   loan_type=loan_type, loan_amount=loan_amount)

        credit_result = credit_client.get_credit_profile(customer_id)
        logger.info("loan_agent.credit_fetched",
                   score=credit_result.get("credit_score"))
        mcp_calls.append(self.log_mcp_call(
            "get_credit_profile", "credit",
            {"customer_id": customer_id}, credit_result,
        ))

        eligibility_result = credit_client.check_loan_eligibility(
            customer_id, loan_amount, loan_type
        )
        logger.info("loan_agent.eligibility",
                   eligible=eligibility_result.get("eligible"),
                   max=eligibility_result.get("max_eligible_amount"))
        mcp_calls.append(self.log_mcp_call(
            "check_loan_eligibility", "credit",
            {"customer_id": customer_id,
             "amount": loan_amount,
             "loan_type": loan_type},
            eligibility_result,
        ))

        reg_result = compliance_client.get_regulations(
            applies_to=f"{loan_type}_loan"
        )
        mcp_calls.append(self.log_mcp_call(
            "get_regulations", "compliance",
            {"applies_to": f"{loan_type}_loan"}, reg_result,
        ))

        kg_queries.append(self.log_kg_query(
            "get_customer_emi_load_and_regulations",
            {"customer_id": customer_id, "loan_type": loan_type},
        ))
        try:
            kg_emi = self.kg.get_customer_emi_load_and_regulations(
                customer_id, loan_type
            )
        except Exception as e:
            logger.warning("loan_agent.kg_failed", error=str(e))
            kg_emi = {}

        try:
            response = self.chain.invoke({
                "credit_profile": json.dumps(
                    credit_result, indent=2, default=str
                ),
                "eligibility_data": json.dumps(
                    eligibility_result, indent=2, default=str
                ),
                "kg_emi_data": json.dumps(kg_emi, indent=2, default=str),
                "regulations": json.dumps(reg_result, indent=2, default=str),
                "query": query,
            })
            logger.info("loan_agent.llm_success",
                       response_length=len(response))
        except Exception as e:
            logger.error("loan_agent.llm_failed", error=str(e))
            response = self._build_detailed_fallback(
                credit_result, eligibility_result, loan_type, loan_amount
            )

        return {
            "output": {
                "agent": "loan_agent",
                "response": response,
                "eligible": eligibility_result.get("eligible"),
                "loan_type": loan_type,
                "loan_amount": loan_amount,
                "credit_score": credit_result.get("credit_score"),
                "max_eligible_amount": eligibility_result.get(
                    "max_eligible_amount"
                ),
            },
            "mcp_calls": mcp_calls,
            "kg_queries": kg_queries,
        }

    def _extract_loan_details(self, query: str) -> Tuple[str, float]:
        q = query.lower()
        if any(w in q for w in ["home", "house", "property", "flat"]):
            loan_type = "home"
        elif any(w in q for w in ["personal", "cash"]):
            loan_type = "personal"
        elif any(w in q for w in ["car", "vehicle", "auto", "bike"]):
            loan_type = "car"
        elif any(w in q for w in ["msme", "business", "enterprise"]):
            loan_type = "msme"
        elif any(w in q for w in ["education", "study", "college"]):
            loan_type = "education"
        elif "gold" in q:
            loan_type = "gold"
        else:
            loan_type = "personal"

        amount = 2000000.0
        lakh = re.search(r"(\d+(?:\.\d+)?)\s*(?:l\b|lakh|lakhs|lac\b)", q)
        if lakh:
            return loan_type, float(lakh.group(1)) * 100000
        crore = re.search(r"(\d+(?:\.\d+)?)\s*(?:cr\b|crore|crores)", q)
        if crore:
            return loan_type, float(crore.group(1)) * 10000000
        rupee = re.search(r"rs\.?\s*([\d,]+)", q)
        if rupee:
            return loan_type, float(rupee.group(1).replace(",", ""))
        return loan_type, amount

    def _build_detailed_fallback(
        self,
        credit: dict,
        eligibility: dict,
        loan_type: str,
        loan_amount: float,
    ) -> str:
        eligible = eligibility.get("eligible", False)
        credit_score = credit.get("credit_score", "N/A")
        monthly_income = credit.get("monthly_income", 0)
        existing_emis = credit.get("total_monthly_emi", 0)
        foir = credit.get("foir", 0)
        max_amount = eligibility.get("max_eligible_amount", 0)
        reasons = eligibility.get("reasons", [])

        status = "YES - ELIGIBLE" if eligible else "NO - NOT ELIGIBLE"

        lines = [
            f"## {loan_type.title()} Loan Eligibility",
            f"",
            f"**Decision: {status}**",
            f"",
            f"**Your Financial Profile:**",
            f"- Credit Score: {credit_score}",
            f"- Monthly Income: Rs.{monthly_income:,.0f}",
            f"- Existing Monthly EMIs: Rs.{existing_emis:,.0f}",
            f"- Current FOIR: {round(foir * 100, 1)}%",
            f"",
            f"**Loan Details:**",
            f"- Requested: Rs.{loan_amount:,.0f}",
            f"- Maximum Eligible: Rs.{max_amount:,.0f}",
            f"",
            f"**Assessment:**",
        ]
        for r in reasons:
            lines.append(f"- {r}")

        if not eligible:
            lines.extend([
                f"",
                f"**How to Improve:**",
                f"- Reduce existing EMI obligations",
                f"- Improve credit score above 750",
                f"- Apply with a co-applicant",
                f"- Consider a lower loan amount",
            ])

        lines.append(
            f"\nFor assistance call 1800-123-4567 or visit your nearest branch."
        )
        return "\n".join(lines)