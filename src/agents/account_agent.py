import json
from typing import Any, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langsmith import traceable

from src.agents.base_agent import BaseAgent
from src.mcp_client import core_banking_client
from src.knowledge_graph.kg_queries import BankingKGQueries
from prompts.loader import load_prompt
import structlog

logger = structlog.get_logger(__name__)


class AccountAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(llm, "account_agent")
        self.kg = BankingKGQueries()
        self.prompt = ChatPromptTemplate.from_template(load_prompt("account_agent"))
        self.chain = self.prompt | self.llm | StrOutputParser()

    @traceable(name="account_agent.run")
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        customer_id = state["customer_id"]
        query = state["query"]
        mcp_calls = []
        kg_queries = []

        # MCP Call 1: Account Summary
        account_result = core_banking_client.get_account_summary(customer_id)
        logger.info("account_agent.accounts_fetched",
                   success=account_result.get("success"),
                   count=account_result.get("total_accounts", 0),
                   total_balance=account_result.get("total_balance", 0))
        mcp_calls.append(self.log_mcp_call(
            "get_account_summary", "core_banking",
            {"customer_id": customer_id}, account_result,
        ))

        # MCP Call 2: Transactions for first active account
        txn_result = {}
        if account_result.get("success") and account_result.get("accounts"):
            active = [
                a for a in account_result["accounts"]
                if a.get("status") == "active"
            ]
            target = active[0] if active else account_result["accounts"][0]
            acc_id = target["account_id"]
            txn_result = core_banking_client.get_transactions(acc_id, limit=5)
            logger.info("account_agent.transactions_fetched",
                       account_id=acc_id,
                       count=len(txn_result.get("transactions", [])))
            mcp_calls.append(self.log_mcp_call(
                "get_transactions", "core_banking",
                {"account_id": acc_id, "limit": 5}, txn_result,
            ))

        # MCP Call 3: Inactive Accounts
        inactive_result = core_banking_client.get_inactive_accounts(
            customer_id, 6
        )
        mcp_calls.append(self.log_mcp_call(
            "get_inactive_accounts", "core_banking",
            {"customer_id": customer_id, "inactive_months": 6},
            inactive_result,
        ))

        # KG Query
        kg_queries.append(self.log_kg_query(
            "get_customer_financial_profile",
            {"customer_id": customer_id},
        ))
        try:
            kg_profile = self.kg.get_customer_financial_profile(customer_id)
        except Exception as e:
            logger.warning("account_agent.kg_failed", error=str(e))
            kg_profile = {}

        # Generate LLM Response
        try:
            response = self.chain.invoke({
                "account_data": json.dumps(account_result, indent=2, default=str),
                "transaction_data": json.dumps(txn_result, indent=2, default=str),
                "inactive_data": json.dumps(inactive_result, indent=2, default=str),
                "kg_insights": json.dumps(kg_profile, indent=2, default=str),
                "query": query,
            })
            logger.info("account_agent.llm_success",
                       response_length=len(response))
        except Exception as e:
            logger.error("account_agent.llm_failed", error=str(e))
            response = self._build_detailed_fallback(
                account_result, txn_result, inactive_result
            )

        return {
            "output": {
                "agent": "account_agent",
                "response": response,
                "raw": account_result,
            },
            "mcp_calls": mcp_calls,
            "kg_queries": kg_queries,
        }

    def _build_detailed_fallback(
        self,
        account_data: dict,
        txn_data: dict,
        inactive_data: dict,
    ) -> str:
        if not account_data.get("success"):
            return (
                "I could not retrieve your account information. "
                "Please try again or call 1800-123-4567."
            )

        lines = [
            f"## Account Summary for "
            f"{account_data.get('customer_name', 'Customer')}\n"
        ]
        total = account_data.get("total_balance", 0)
        lines.append(
            f"**Total Balance (Active Accounts): Rs.{total:,.2f}**\n"
        )
        for acc in account_data.get("accounts", []):
            emoji = (
                "✅" if acc["status"] == "active"
                else "⚠️" if acc["status"] == "dormant"
                else "❌"
            )
            lines.append(
                f"{emoji} **{acc['account_type']}** ({acc['account_id']})"
            )
            lines.append(f"   Balance: Rs.{acc['balance']:,.2f}")
            lines.append(f"   Status: {acc['status'].title()}")
            lines.append(
                f"   Last Transaction: {acc['last_transaction_date']}\n"
            )

        txns = txn_data.get("transactions", [])
        if txns:
            lines.append("### Recent Transactions\n")
            for t in txns[:5]:
                arrow = "+" if t["type"] == "credit" else "-"
                lines.append(
                    f"- {t['timestamp'][:10]} | "
                    f"{arrow}Rs.{t['amount']:,.2f} | "
                    f"{t['description']}"
                )

        inactive = inactive_data.get("inactive_accounts", [])
        if inactive:
            lines.append(
                f"\n### Inactive Accounts ({len(inactive)} found)\n"
            )
            for acc in inactive:
                lines.append(
                    f"- {acc['account_id']} ({acc['account_type']}): "
                    f"Inactive for "
                    f"{acc['months_since_last_transaction']} months"
                )
        return "\n".join(lines)