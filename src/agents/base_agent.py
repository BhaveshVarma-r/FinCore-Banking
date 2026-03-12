from datetime import datetime
from typing import Any, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
import structlog

logger = structlog.get_logger(__name__)


class BaseAgent:
    """
    Base class for all FinCore specialist agents.
    Not abstract - subclasses override run() as needed.
    """

    def __init__(self, llm: ChatGoogleGenerativeAI, agent_name: str):
        self.llm = llm
        self.agent_name = agent_name

    def log_mcp_call(
        self,
        tool: str,
        server: str,
        params: dict,
        result: dict,
    ) -> dict:
        return {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "server": server,
            "tool": tool,
            "params": params,
            "success": result.get("success", False),
            "error": result.get("error") if not result.get("success") else None,
        }

    def log_kg_query(self, query_name: str, params: dict) -> str:
        return (
            f"[{self.agent_name}] {query_name}"
            f"({params}) @ {datetime.now().isoformat()}"
        )

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default run — subclasses override with their logic.
        """
        return {
            "output": {},
            "mcp_calls": [],
            "kg_queries": [],
        }