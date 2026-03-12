import os
from typing import Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv
import structlog

load_dotenv()
logger = structlog.get_logger(__name__)


class KnowledgeGraphClient:
    _instance: Optional["KnowledgeGraphClient"] = None

    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")

        if not all([self.uri, self.password]):
            raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be set")

        self.driver = GraphDatabase.driver(
            self.uri, auth=(self.username, self.password)
        )
        logger.info("kg.connected", uri=self.uri)

    @classmethod
    def get_instance(cls) -> "KnowledgeGraphClient":
        if cls._instance is None:
            cls._instance = KnowledgeGraphClient()
        return cls._instance

    def close(self):
        self.driver.close()

    def run_query(self, cypher: str, params: dict = None) -> list[dict]:
        params = params or {}
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, params)
            return [record.data() for record in result]

    def run_write_query(self, cypher: str, params: dict = None) -> Any:
        params = params or {}
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, params)
            summary = result.consume()
            return {
                "nodes_created": summary.counters.nodes_created,
                "relationships_created": summary.counters.relationships_created,
                "properties_set": summary.counters.properties_set,
            }

    def health_check(self) -> bool:
        try:
            result = self.run_query("RETURN 1 AS health")
            return result[0]["health"] == 1
        except Exception as e:
            logger.error("kg.health_check_failed", error=str(e))
            return False