import json
import re
import uuid
from typing import Any, Dict, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langsmith import traceable

from src.agents.base_agent import BaseAgent
from src.mcp_client import fraud_client
from src.knowledge_graph.kg_queries import BankingKGQueries
from prompts.loader import load_prompt
import structlog

logger = structlog.get_logger(__name__)


class FraudAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(llm, "fraud_agent")
        self.kg = BankingKGQueries()
        self.prompt = ChatPromptTemplate.from_template(load_prompt("fraud_agent"))
        self.chain = self.prompt | self.llm | StrOutputParser()

    @traceable(name="fraud_agent.run")
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        customer_id = state["customer_id"]
        query = state["query"]
        mcp_calls = []
        kg_queries = []

        amount, payee_id = self._extract_details(query)
        transaction_id = self._extract_txn_id(query)

        risk_result = fraud_client.score_transaction_risk(
            transaction_id, amount, payee_id, customer_id
        )
        logger.info("fraud_agent.risk_scored",
                   risk_score=risk_result.get("risk_score"),
                   risk_level=risk_result.get("risk_level"))
        mcp_calls.append(self.log_mcp_call(
            "score_transaction_risk", "fraud",
            {"transaction_id": transaction_id,
             "amount": amount,
             "payee_id": payee_id},
            risk_result,
        ))

        alerts_result = fraud_client.get_fraud_alerts(customer_id)
        mcp_calls.append(self.log_mcp_call(
            "get_fraud_alerts", "fraud",
            {"customer_id": customer_id}, alerts_result,
        ))

        flag_result = {}
        q = query.lower()
        is_dispute = any(w in q for w in [
            "didn't make", "didnt make", "unauthorized",
            "dispute", "not mine", "fraud", "unknown",
            "suspicious", "i did not",
        ])
        if is_dispute:
            flag_result = fraud_client.flag_transaction(
                transaction_id,
                "Customer reported unauthorized transaction",
                "customer_dispute",
            )
            logger.info("fraud_agent.flagged",
                       case_id=flag_result.get("case_id"))
            mcp_calls.append(self.log_mcp_call(
                "flag_transaction", "fraud",
                {"transaction_id": transaction_id}, flag_result,
            ))

        kg_queries.append(self.log_kg_query(
            "detect_fraud_network", {"payee_id": payee_id}
        ))
        try:
            kg_fraud = self.kg.detect_fraud_network(payee_id)
        except Exception as e:
            logger.warning("fraud_agent.kg_failed", error=str(e))
            kg_fraud = {"is_known_fraud_payee": False}

        risk_score = risk_result.get("risk_score", 0.0)
        risk_level = (
            "critical" if risk_score >= 0.9 else
            "high" if risk_score >= 0.7 else
            "medium" if risk_score >= 0.4 else
            "low"
        )
        if kg_fraud.get("is_known_fraud_payee") and risk_level == "low":
            risk_level = "high"

        try:
            response = self.chain.invoke({
                "risk_assessment": json.dumps(
                    risk_result, indent=2, default=str
                ),
                "fraud_alerts": json.dumps(
                    alerts_result, indent=2, default=str
                ),
                "kg_fraud": json.dumps(kg_fraud, indent=2, default=str),
                "query": query,
            })
            logger.info("fraud_agent.llm_success",
                       response_length=len(response))
        except Exception as e:
            logger.error("fraud_agent.llm_failed", error=str(e))
            response = self._build_detailed_fallback(
                risk_result, flag_result, risk_level, amount
            )

        return {
            "output": {
                "agent": "fraud_agent",
                "response": response,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "case_id": flag_result.get("case_id"),
                "kg_network": kg_fraud,
            },
            "risk_level": risk_level,
            "mcp_calls": mcp_calls,
            "kg_queries": kg_queries,
        }

    def _extract_details(self, query: str) -> Tuple[float, str]:
        q = query.lower()
        amount = 45000.0
        lakh = re.search(r"(\d+(?:\.\d+)?)\s*(?:l\b|lakh|lakhs)", q)
        if lakh:
            amount = float(lakh.group(1)) * 100000
        raw = re.search(r"rs\.?\s*([\d,]+)", q)
        if raw and amount == 45000.0:
            amount = float(raw.group(1).replace(",", ""))
        payee_id = f"PAY{abs(hash(query)) % 9000 + 1000}"
        return amount, payee_id

    def _extract_txn_id(self, query: str) -> str:
        match = re.search(r"\b(TXN[A-Z0-9]{6,10})\b", query.upper())
        return (
            match.group(1) if match
            else f"TXN{str(uuid.uuid4())[:8].upper()}"
        )

    def _build_detailed_fallback(
        self,
        risk_result: dict,
        flag_result: dict,
        risk_level: str,
        amount: float,
    ) -> str:
        risk_score = risk_result.get("risk_score", 0)
        flags = risk_result.get("flags", [])
        case_id = flag_result.get("case_id", "N/A")
        emoji = {
            "low": "", "medium": "",
            "high": "", "critical": ""
        }.get(risk_level, "")

        lines = [
            f"## Fraud Risk Assessment",
            f"",
            f"{emoji} **Risk Level: {risk_level.upper()}** "
            f"(Score: {risk_score:.2f})",
            f"",
            f"Transaction Amount: Rs.{amount:,.2f}",
        ]
        if flags:
            lines.append("\n**Risk Factors:**")
            for f in flags:
                lines.append(f"- {f.replace('_', ' ').title()}")
        if case_id != "N/A":
            lines.append(f"\n**Case ID: {case_id}**")
        lines.extend([
            "",
            "**Immediate Steps:**",
            "1. Call 1800-123-4567 immediately",
            "2. Do not share OTP or PIN with anyone",
            "3. Block card via FinCore Mobile App if needed",
            "",
            "**Emergency:** 1800-123-FRAUD (24x7)",
        ])
        return "\n".join(lines)