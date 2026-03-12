import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable
from prompts.loader import load_prompt
import structlog

logger = structlog.get_logger(__name__)


class CritiqueAgent:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.parser = JsonOutputParser()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", load_prompt("critique_agent")),
            ("human", "Review this response and return JSON evaluation:"),
        ])
        self.chain = self.prompt | self.llm | self.parser

    @traceable(name="critique_agent.critique")
    def critique(
        self,
        query: str,
        response: str,
        agent_outputs: Dict[str, Any],
        mcp_calls_log: list,
    ) -> dict:
        retrieved_data = self._summarize_retrieved_data(
            agent_outputs, mcp_calls_log
        )
        try:
            result = self.chain.invoke({
                "query": query,
                "retrieved_data": retrieved_data,
                "response": response,
            })

            passes = result.get("passes", True)
            if result.get("compliance_violations") and any(
                result["compliance_violations"]
            ):
                passes = False
            if result.get("hallucinations_detected") and any(
                result["hallucinations_detected"]
            ):
                passes = False

            logger.info("critique.result",
                       passes=passes,
                       score=result.get("overall_score"))
            return {
                "passes": passes,
                "overall_score": result.get("overall_score", 75),
                "scores": result.get("scores", {}),
                "issues": result.get("issues", []),
                "hallucinations_detected": result.get(
                    "hallucinations_detected", []
                ),
                "compliance_violations": result.get(
                    "compliance_violations", []
                ),
                "missing_info": result.get("missing_info", []),
                "feedback": result.get("feedback", ""),
            }
        except Exception as e:
            logger.error("critique.failed", error=str(e))
            return {
                "passes": True,
                "overall_score": 70,
                "scores": {},
                "issues": [f"Critique agent error: {str(e)}"],
                "hallucinations_detected": [],
                "compliance_violations": [],
                "missing_info": [],
                "feedback": "",
            }

    def _summarize_retrieved_data(
        self, agent_outputs: dict, mcp_calls_log: list
    ) -> str:
        parts = []
        for call in mcp_calls_log[:10]:
            if call.get("success"):
                parts.append(
                    f"[{call['server']}.{call['tool']}] "
                    f"params={call.get('params')} -> success"
                )
        for name, output in agent_outputs.items():
            if isinstance(output, dict):
                keys = [k for k in output.keys() if k != "response"]
                if keys:
                    parts.append(f"[{name}] data: {keys}")
        return "\n".join(parts) if parts else "No retrieved data"