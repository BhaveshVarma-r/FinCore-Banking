import json
from typing import Any, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langsmith import traceable

from src.agents.base_agent import BaseAgent
from prompts.loader import load_prompt
import structlog

logger = structlog.get_logger(__name__)


class AggregatorAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(llm, "aggregator_agent")
        self.prompt = ChatPromptTemplate.from_template(
            load_prompt("aggregator_agent")
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        result = self.synthesize(state)
        return {
            "output": {
                "agent": "aggregator_agent",
                "response": result["response"],
            },
            "mcp_calls": [],
            "kg_queries": [],
        }

    @traceable(name="aggregator.synthesize")
    def synthesize(self, state: Dict[str, Any]) -> Dict[str, Any]:
        agent_outputs = state.get("agent_outputs", {})
        requires_human = state.get("requires_human", False)
        risk_level = state.get("risk_level", "low")
        query = state.get("query", "")
        plan = state.get("planner_plan", {})

        if not agent_outputs:
            return {
                "response": (
                    "I apologize, I could not process your request. "
                    "Please contact 1800-123-4567."
                )
            }

        formatted = {
            name: (
                out.get("response", str(out))
                if isinstance(out, dict) else str(out)
            )
            for name, out in agent_outputs.items()
        }

        try:
            response = self.chain.invoke({
                "agent_outputs": json.dumps(
                    formatted, indent=2, default=str
                ),
                "requires_human": str(requires_human),
                "risk_level": risk_level,
                "plan": json.dumps(plan, indent=2, default=str),
                "query": query,
            })
            logger.info("aggregator.success",
                       response_length=len(response))
        except Exception as e:
            logger.error("aggregator.failed", error=str(e))
            response = "\n\n".join(formatted.values())

        return {"response": response}