import os
import shutil

from claude_agent_sdk._internal.sessions import (
    _canonicalize_path,
    _find_project_dir,
    get_session_messages,
)
from fastapi import APIRouter, HTTPException, Request

from medium_claude_sdk_bigquery_agent.utils.file_paths import BASE_DIR
from medium_claude_sdk_bigquery_agent.utils.objects import (
    AgentRequest,
    AgentResponse,
    ConversationHistoryResponse,
    ConversationMessage,
)

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.delete("/clean-up")
async def clean_up():
    """
    Deletes all session files for this project from ~/.claude/projects/

    :returns status message indicating how many sessions were removed
    """
    project_dir = _find_project_dir(_canonicalize_path(os.path.dirname(BASE_DIR)))
    if project_dir is None or not project_dir.exists():
        return {"status": "nothing to clean"}
    shutil.rmtree(project_dir)
    project_dir.mkdir()
    return {"status": "cleaned"}


@router.get("/conversation-history", response_model=ConversationHistoryResponse)
async def conversation_history(session_id: str) -> ConversationHistoryResponse:
    """
    Retrieves the full conversation history for a given session

    :param session_id: the session ID to retrieve history for
    :returns conversation history response containing all messages for the session
    """
    messages = get_session_messages(session_id=session_id, directory=BASE_DIR)
    if not messages:
        raise HTTPException(
            status_code=404,
            detail=f"No conversation found for session_id: {session_id}",
        )
    return ConversationHistoryResponse(
        session_id=session_id,
        messages=[
            ConversationMessage(
                type=m.type,
                uuid=m.uuid,
                session_id=m.session_id,
                message=m.message,
            )
            for m in messages
        ],
    )


@router.post("/chat", response_model=AgentResponse)
async def chat(request: AgentRequest, app_request: Request) -> AgentResponse:
    """
    Submits a natural-language question to the BigQuery agent

    :param request: the agent request containing the question and session metadata
    :param app_request: FastAPI request used to access shared app state
    :returns agent response containing the result and session ID
    """
    try:
        result, session_id = await app_request.app.state.agent_service.run(
            question=request.question,
            schema=app_request.app.state.schema,
            session_id=request.session_id,
            checkpoint_dir=request.checkpoint_dir,
        )
        return AgentResponse(session_id=session_id, result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
