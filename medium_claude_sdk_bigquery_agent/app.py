import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from medium_claude_sdk_bigquery_agent.adapters.bigquery_adapter import BigQueryAdapter
from medium_claude_sdk_bigquery_agent.api.router import router
from medium_claude_sdk_bigquery_agent.core.agent import AgentService
from medium_claude_sdk_bigquery_agent.utils.file_paths import (
    BQ_LOCATION,
    DATASET_ID,
    TABLE_ID,
)
from medium_claude_sdk_bigquery_agent.utils.helpers import get_schema
from version import MAJOR, __version__

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifespan by making resources available for the duration of the application's life

    :param app: the FastAPI application instance used to store shared state
    """
    bq_adapter = BigQueryAdapter(
        project_id=os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID"),
        location=BQ_LOCATION,
    )
    app.state.agent_service = AgentService(bq_port=bq_adapter)
    app.state.schema = await get_schema(
        project_id=os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID"),
        dataset_id=DATASET_ID,
        table_id=TABLE_ID,
    )
    yield


app = FastAPI(title="BigQuery Agent API", version=__version__, lifespan=lifespan)
app.include_router(router=router, prefix=f"/api/v{MAJOR}")
