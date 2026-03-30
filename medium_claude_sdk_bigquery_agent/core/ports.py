from abc import ABC, abstractmethod
from typing import Any


class BigQueryPort(ABC):
    """
    Outbound port defining the BigQuery execution contract providing sync/async BigQuery execution
    """

    @abstractmethod
    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        """
        Executes a SQL query synchronously against BigQuery

        :param sql: the SQL query to execute
        :returns list of result rows as dictionaries
        """
        pass

    @abstractmethod
    async def execute_query_async(self, args: dict[str, Any]) -> list:
        """
        Executes a SQL query asynchronously, using the tool-compatible args schema

        :param args: dictionary containing key 'sql' with the query string
        :returns list of result rows
        """
        pass


class AgentServicePort(ABC):
    """
    Inbound port defining the agent orchestration contract utilizing the Claude SDK agent
    """

    @abstractmethod
    async def run(
        self,
        question: str,
        schema: str,
        session_id: str | None = None,
        resume_session: str | None = None,
        checkpoint_dir: str | None = None,
    ) -> tuple[str, str]:
        """
        Runs the agent with the given question

        :param question: the user question to answer
        :param schema: pre-fetched formatted table schema string
        :param session_id: optional session ID; generated if not provided
        :param resume_session: optional session ID to resume a prior conversation
        :param checkpoint_dir: optional directory for checkpoint files
        :returns tuple of (result_text, session_id)
        """
        pass
