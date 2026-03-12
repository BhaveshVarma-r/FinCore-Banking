import json
from typing import Any, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langsmith import traceable

from src.agents.base_agent import BaseAgent
from src.mcp_client import compliance_client
from src.knowledge_graph.kg_queries import BankingKGQueries
from prompts.loader import load_prompt
import structlog

logger = structlog.get_logger(__name__)


class ComplianceAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(llm, "compliance_agent")
        self.kg = BankingKGQueries()
        self.prompt = ChatPromptTemplate.from_template(
            load_prompt("compliance_agent")
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    @traceable(name="compliance_agent.run")
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        customer_id = state["customer_id"]
        query = state["query"]
        mcp_calls = []
        kg_queries = []

        domain = self._detect_domain(query)
        loan_type = self._detect_loan_type(query)
        product_name = self._detect_product(query)

        reg_result = compliance_client.get_regulations(applies_to=domain)
        logger.info("compliance_agent.regs_fetched",
                   count=reg_result.get("total", 0))
        mcp_calls.append(self.log_mcp_call(
            "get_regulations", "compliance",
            {"applies_to": domain}, reg_result,
        ))

        doc_result = {}
        if loan_type:
            doc_result = compliance_client.get_document_requirements(loan_type)
            logger.info("compliance_agent.docs_fetched",
                       loan_type=loan_type,
                       count=doc_result.get("total_documents", 0))
            mcp_calls.append(self.log_mcp_call(
                "get_document_requirements", "compliance",
                {"loan_type": loan_type}, doc_result,
            ))

        product_rules = {}
        if any(w in query.lower() for w in ["upgrade", "premium", "switch"]):
            product_rules = compliance_client.check_product_eligibility_rules(
                "PROD002", "retail", 700
            )
            mcp_calls.append(self.log_mcp_call(
                "check_product_eligibility_rules", "compliance",
                {"product_id": "PROD002"}, product_rules,
            ))

        search_term = product_name or loan_type or domain
        kg_queries.append(self.log_kg_query(
            "get_product_regulations", {"product_name": search_term}
        ))
        try:
            kg_regs = self.kg.get_product_regulations(
                search_term or "savings"
            )
        except Exception as e:
            logger.warning("compliance_agent.kg_failed", error=str(e))
            kg_regs = []

        try:
            response = self.chain.invoke({
                "regulations": json.dumps(reg_result, indent=2, default=str),
                "documents": json.dumps(doc_result, indent=2, default=str),
                "product_rules": json.dumps(
                    product_rules, indent=2, default=str
                ),
                "kg_regs": json.dumps(kg_regs, indent=2, default=str),
                "query": query,
            })
            logger.info("compliance_agent.llm_success",
                       response_length=len(response))
        except Exception as e:
            logger.error("compliance_agent.llm_failed", error=str(e))
            response = self._build_detailed_fallback(
                reg_result, doc_result, loan_type
            )

        return {
            "output": {
                "agent": "compliance_agent",
                "response": response,
                "regulations": reg_result,
                "documents": doc_result,
            },
            "mcp_calls": mcp_calls,
            "kg_queries": kg_queries,
        }

    def _detect_domain(self, q: str) -> str:
        q = q.lower()
        if "home" in q: return "home_loan"
        if "personal" in q: return "personal_loan"
        if "msme" in q or "business" in q: return "msme_loan"
        if "fraud" in q: return "fraud_transactions"
        if "credit card" in q: return "credit_card"
        if "dormant" in q: return "dormant_accounts"
        return "all_accounts"

    def _detect_loan_type(self, q: str) -> str:
        q = q.lower()
        for t in ["home", "personal", "msme", "education", "car", "gold"]:
            if t in q:
                return t
        if "business" in q:
            return "msme"
        return ""

    def _detect_product(self, q: str) -> str:
        q = q.lower()
        if "premium" in q: return "premium savings"
        if "savings" in q: return "savings"
        if "current" in q: return "current"
        return ""

    def _build_detailed_fallback(
        self,
        reg_result: dict,
        doc_result: dict,
        loan_type: str,
    ) -> str:
        lines = []
        if doc_result.get("success") and doc_result.get("categorized"):
            lines.append(
                f"## Documents Required for "
                f"{loan_type.title()} Loan\n"
            )
            for category, docs in doc_result["categorized"].items():
                lines.append(f"**{category} Documents:**")
                for i, doc in enumerate(docs, 1):
                    lines.append(f"{i}. {doc}")
                lines.append("")
        if reg_result.get("regulations"):
            lines.append("## Applicable Regulations\n")
            for reg in reg_result["regulations"][:3]:
                lines.append(f"**{reg.get('title')}** ({reg.get('source')})")
                lines.append(f"{reg.get('description')}\n")
        if not lines:
            lines.append(
                "Please visit your nearest FinCore branch or "
                "call 1800-123-4567."
            )
        return "\n".join(lines)