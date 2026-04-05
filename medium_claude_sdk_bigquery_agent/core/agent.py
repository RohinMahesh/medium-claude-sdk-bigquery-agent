import os
import uuid
from dataclasses import dataclass, field

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from claude_agent_sdk import (
    AgentDefinition,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    create_sdk_mcp_server,
    get_session_messages,
)

from medium_claude_sdk_bigquery_agent.adapters.bigquery_adapter import create_bq_tool
from medium_claude_sdk_bigquery_agent.core.ports import AgentServicePort, BigQueryPort
from medium_claude_sdk_bigquery_agent.utils.constants import (
    AGENT_DESCRIPTION,
    AGENT_NAME,
    DEFAULT_MODEL,
    MCP_SERVER_NAME,
    MCP_SERVER_VERSION,
    TOOL_NAME,
)
from medium_claude_sdk_bigquery_agent.utils.file_paths import DATASET_ID, TABLE_ID
from medium_claude_sdk_bigquery_agent.utils.helpers import create_logger
from medium_claude_sdk_bigquery_agent.utils.prompts import BIGQUERY_AGENT_PROMPT


@dataclass
class AgentService(AgentServicePort):
    """
    Core agent service that orchestrates the Claude Agent SDK
    """

    bq_port: BigQueryPort
    _mcp_server: object = field(init=False, repr=False)
    _agent: AgentDefinition = field(init=False, repr=False)

    def __post_init__(self):
        """
        Initializes the MCP server and agent definition using the injected BigQuery port
        """
        # Define logger
        self.logger = create_logger(name="AgentService")

        # Define IDs for table
        self.project_id = os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID")
        self.dataset_id = DATASET_ID

        # Create BQ tool and in-memory MCP server
        bq_tool = create_bq_tool(self.bq_port)
        self._mcp_server = create_sdk_mcp_server(
            name=MCP_SERVER_NAME,
            version=MCP_SERVER_VERSION,
            tools=[bq_tool],
        )

    async def run(
        self,
        question: str,
        schema: str,
        session_id: str | None = None,
        checkpoint_dir: str | None = None,
    ) -> tuple[str, str]:
        """
        Runs the BigQuery agent with the given question

        :param question: the user question to answer
        :param schema: pre-fetched formatted table schema string
        :param session_id: optional session ID; generated if not provided; resumes
            existing session automatically if the ID matches a stored session
        :param checkpoint_dir: optional directory for checkpoint files
        :returns tuple of (result_text, session_id)
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        if checkpoint_dir is None:
            checkpoint_dir = os.getcwd()

        client = None
        try:
            # Define agent
            _agent = AgentDefinition(
                description=AGENT_DESCRIPTION,
                prompt=BIGQUERY_AGENT_PROMPT.replace("{QUESTION}", question)
                .replace("{TABLE_SCHEMA}", schema)
                .replace("{DATASET_ID}", DATASET_ID)
                .replace("{TABLE_ID}", TABLE_ID),
                tools=[f"mcp__{MCP_SERVER_NAME}__{TOOL_NAME}"],
                model=DEFAULT_MODEL,
            )

            vertex_env = {}
            if project_id := os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID"):
                vertex_env["ANTHROPIC_VERTEX_PROJECT_ID"] = project_id
            if region := os.environ.get("CLOUD_ML_REGION"):
                vertex_env["CLOUD_ML_REGION"] = region

            # Identify new session
            _resume_id = session_id
            _session_exists = bool(
                get_session_messages(session_id=_resume_id, directory=checkpoint_dir)
            )

            client = ClaudeSDKClient(
                options=ClaudeAgentOptions(
                    allowed_tools=[f"mcp__{MCP_SERVER_NAME}__{TOOL_NAME}"],
                    mcp_servers={MCP_SERVER_NAME: self._mcp_server},
                    agents={AGENT_NAME: _agent},
                    enable_file_checkpointing=True,
                    session_id=session_id if not _session_exists else None,
                    continue_conversation=_session_exists,
                    resume=_resume_id if _session_exists else None,
                    cwd=checkpoint_dir,
                    env=vertex_env if vertex_env else None,
                )
            )

            await client.connect()
            self.logger.info(f"Session {session_id} executing question: {question}")
            await client.query(prompt=question, session_id=session_id)

            result = ""
            async for message in client.receive_messages():
                if hasattr(message, "result"):
                    result = str(message.result)
                    break
            else:
                self.logger.warning(f"Session {session_id} received no result message")

            self.logger.info(f"Session {session_id} successful response: {result}")
            return result, session_id
        except Exception as e:
            self.logger.error(f"Request failed with error: {e}")
            return "", session_id
        finally:
            if client is not None:
                await client.disconnect()
