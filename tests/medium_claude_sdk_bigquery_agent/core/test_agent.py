from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from medium_claude_sdk_bigquery_agent.core.agent import AgentService


@pytest.fixture
def mock_agent_service_instance():
    mock_bq_port = MagicMock()
    mock_bq_tool = MagicMock()
    mock_mcp_server = MagicMock()

    env_patch = {"ANTHROPIC_VERTEX_PROJECT_ID": "test-project-1"}

    with (
        patch(
            "medium_claude_sdk_bigquery_agent.core.agent.create_bq_tool",
            return_value=mock_bq_tool,
        ),
        patch(
            "medium_claude_sdk_bigquery_agent.core.agent.create_sdk_mcp_server",
            return_value=mock_mcp_server,
        ),
        patch.dict("os.environ", env_patch),
    ):
        service = AgentService(bq_port=mock_bq_port)
        return service


@pytest.mark.parametrize(
    "project_id_env",
    [
        "test-project-1",
        "test-project-2",
        None,
    ],
)
def test_agent_service_init(project_id_env):
    mock_bq_port = MagicMock()
    mock_bq_tool = MagicMock()
    mock_mcp_server = MagicMock()

    env_patch = (
        {"ANTHROPIC_VERTEX_PROJECT_ID": project_id_env} if project_id_env else {}
    )

    with (
        patch(
            "medium_claude_sdk_bigquery_agent.core.agent.create_bq_tool",
            return_value=mock_bq_tool,
        ) as mock_create_tool,
        patch(
            "medium_claude_sdk_bigquery_agent.core.agent.create_sdk_mcp_server",
            return_value=mock_mcp_server,
        ) as mock_create_server,
        patch.dict("os.environ", env_patch),
    ):
        service = AgentService(bq_port=mock_bq_port)

    assert service.bq_port is mock_bq_port
    assert service._mcp_server is mock_mcp_server
    mock_create_tool.assert_called_once_with(mock_bq_port)
    mock_create_server.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "question, schema, session_id, expected_result",
    [
        ("What are total sales?", "schema_str", "session-1", "Total sales: $50,000"),
        ("Top products?", "schema_str", None, "Top product: Widget A"),
        ("Simple query", "", "session-2", "Answer"),
    ],
)
async def test_agent_service_run(
    mock_agent_service_instance, question, schema, session_id, expected_result
):

    # Mock claude agent sdk
    async def _message_gen():
        msg = MagicMock()
        msg.result = expected_result
        yield msg

    mock_client_instance = MagicMock()
    mock_client_instance.connect = AsyncMock()
    mock_client_instance.query = AsyncMock()
    mock_client_instance.disconnect = AsyncMock()
    mock_client_instance.receive_messages.return_value = _message_gen()

    with (
        patch(
            "medium_claude_sdk_bigquery_agent.core.agent.get_session_messages",
            return_value=[],
        ),
        patch("medium_claude_sdk_bigquery_agent.core.agent.AgentDefinition"),
        patch("medium_claude_sdk_bigquery_agent.core.agent.ClaudeAgentOptions"),
        patch(
            "medium_claude_sdk_bigquery_agent.core.agent.ClaudeSDKClient",
            return_value=mock_client_instance,
        ),
    ):
        result, returned_session_id = await mock_agent_service_instance.run(
            question=question, schema=schema, session_id=session_id
        )

    assert result == expected_result
    if session_id is not None:
        assert returned_session_id == session_id
    else:
        assert isinstance(returned_session_id, str) and len(returned_session_id) > 0
    mock_client_instance.connect.assert_called_once()
    mock_client_instance.query.assert_called_once_with(
        prompt=question, session_id=returned_session_id
    )
    mock_client_instance.disconnect.assert_called_once()
