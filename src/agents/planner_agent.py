"""
Planner Agent - breaks complex queries into structured execution plans
"""
import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable
from prompts.loader import load_prompt
import structlog

logger = structlog.get_logger(__name__)


class PlannerAgent:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.parser = JsonOutputParser()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", load_prompt("planner")),
            ("human",
             "Customer Query: {query}\n\n"
             "Customer ID: {customer_id}\n\n"
             "Create execution plan:"),
        ])
        self.chain = self.prompt | self.llm | self.parser

    @traceable(name="planner_agent.plan")
    def plan(self, query: str, customer_id: str) -> dict:
        try:
            result = self.chain.invoke({
                "query": query,
                "customer_id": customer_id,
            })
            logger.info(
                "planner.plan_created",
                complexity=result.get("query_complexity"),
                steps=len(result.get("execution_plan", [])),
            )
            return {
                "success": True,
                "query_complexity": result.get("query_complexity", "simple"),
                "primary_intent": result.get("primary_intent", ""),
                "sub_intents": result.get("sub_intents", []),
                "execution_plan": result.get("execution_plan", []),
                "requires_multiple_agents": result.get(
                    "requires_multiple_agents", False
                ),
                "reasoning": result.get("reasoning", ""),
            }
        except Exception as e:
            logger.error("planner.failed", error=str(e))
            return {
                "success": False,
                "query_complexity": "simple",
                "primary_intent": query[:80],
                "sub_intents": [],
                "execution_plan": [],
                "requires_multiple_agents": False,
                "reasoning": f"Planner fallback: {str(e)}",
            }