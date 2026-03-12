"""
Router Agent - classifies intent and selects agents
"""
import json
from typing import Dict, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable
from prompts.loader import load_prompt
import structlog

logger = structlog.get_logger(__name__)


class RouterAgent:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.parser = JsonOutputParser()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", load_prompt("router")),
            ("human", "Query: {query}\n\nRoute to appropriate agents:"),
        ])
        self.chain = self.prompt | self.llm | self.parser

    @traceable(name="router_agent.route")
    def route(
        self,
        query: str,
        customer_id: str,
        plan: dict = None,
        conversation_history: list = None,
    ) -> dict:
        try:
            result = self.chain.invoke({
                "query": query,
                "plan": json.dumps(plan or {}, indent=2),
            })
            valid = ["account", "loan", "fraud", "compliance"]
            agents = [a for a in result.get("agents", []) if a in valid]
            if not agents:
                agents = self._fallback_route(query)

            logger.info(
                "router.decision",
                agents=agents,
                intents=result.get("intents", []),
            )
            return {
                "intents": result.get("intents", []),
                "agents": agents,
                "confidence": result.get("confidence", {}),
                "reasoning": result.get("reasoning", ""),
            }
        except Exception as e:
            logger.error("router.failed", error=str(e))
            return {
                "intents": ["general"],
                "agents": self._fallback_route(query),
                "confidence": {},
                "reasoning": f"Fallback routing: {e}",
            }

    def _fallback_route(self, query: str) -> list:
        q = query.lower()
        agents = []
        if any(w in q for w in [
            "balance", "account", "transaction", "transfer", "inactive"
        ]):
            agents.append("account")
        if any(w in q for w in [
            "loan", "emi", "eligible", "home", "personal", "msme"
        ]):
            agents.append("loan")
        if any(w in q for w in [
            "fraud", "unauthorized", "dispute", "didn't make", "suspicious"
        ]):
            agents.append("fraud")
        if any(w in q for w in [
            "document", "rbi", "regulation", "rule", "upgrade", "compliance"
        ]):
            agents.append("compliance")
        return agents or ["account"]