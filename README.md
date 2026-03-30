# Claude Agent SDK Data Agent

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Running the API](#running-the-api)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Code Quality](#code-quality)

---

## Overview

This project utilizes Claude Agent SDK to create a BigQuery based data agent:

- **Claude Agent SDK** — orchestrates a Claude model (`claude-sonnet-4-6`) with tool-calling capabilities
- **Model Context Protocol (MCP)** — exposes BigQuery execution as a tool the agent can invoke
- **Google BigQuery** — executes generated SQL and returns results
- **FastAPI** — serves the agent as a REST API with session management and conversation history

The agent follows a structured prompting strategy:
1. Determines if the question requires a database lookup
2. Generates SQL from a dynamically injected table schema
3. Executes the SQL via the MCP BigQuery tool
4. Returns a user-friendly natural language answer

---

## Architecture

The project follows **Hexagonal Architecture (Ports & Adapters)** to cleanly separate domain logic from infrastructure:

```
┌────────────────────────────────────────────────────────────┐
│                         HTTP Layer                         │
│              FastAPI app.py + api/router.py                │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│                       Domain Layer                         │
│            core/agent.py (AgentService)                    │
│            core/ports.py (BigQueryPort, AgentServicePort)  │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│                    Infrastructure Layer                    │
│          adapters/bigquery_adapter.py (BigQueryAdapter)    │
│          Google BigQuery via google-cloud-bigquery SDK     │
└────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
medium-claude-code-sdk-skills/
├── medium_claude_sdk_bigquery_agent/
│   ├── app.py                       # FastAPI app + lifespan startup
│   ├── core/
│   │   ├── agent.py                 # AgentService — Claude SDK orchestration
│   │   └── ports.py                 # Abstract interfaces (BigQueryPort, AgentServicePort)
│   ├── adapters/
│   │   └── bigquery_adapter.py      # Google BigQuery adapter
│   ├── api/
│   │   └── router.py                # API endpoint definitions
│   └── utils/
│       ├── constants.py             # App-wide constants (version, model)
│       ├── file_paths.py            # Dataset/table name defaults
│       ├── helpers.py               # Logging, schema fetching, job polling
│       ├── objects.py               # Pydantic request/response models
│       └── prompts.py               # Claude system prompt
├── tests/
│   └── medium_claude_sdk_bigquery_agent/
│       ├── test_agent.py
│       ├── test_bigquery_adapter.py
│       ├── test_router.py
│       ├── test_helpers.py
│       ├── test_ports.py
│       └── test_app.py
├── .env.example                     # Environment variable template
├── .github/workflows/ci.yaml        # GitHub Actions CI pipeline
├── .pre-commit-config.yaml          # isort, black, ruff hooks
├── Makefile                         # Developer convenience commands
├── pyproject.toml                   # Ruff linter configuration
├── requirements.txt                 # Python dependencies
└── .python-version                  # Pinned Python version (3.12.13)
```

---

## Setup

### Prerequisites

- Python 3.12.13 (managed via `conda` or `.python-version`)
- A Google Cloud project with BigQuery enabled
- GCP credentials with BigQuery read permissions
- An Anthropic API key (via Vertex AI or direct)

### 1. Clone and configure environment

```bash
git clone <repo-url>
cd medium-claude-code-sdk-skills
```

### 2. Create and activate the conda environment

```bash
make create-env
make activate-env
```

### 3. Install dependencies

```bash
make install-dependencies
```

### 4. Authenticate with Google Cloud

```bash
make initialize-gcp     # gcloud init
make login-gcp          # gcloud auth application-default login
```

### 5. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```dotenv
# .env
ANTHROPIC_VERTEX_PROJECT_ID=your-gcp-project-id # GCP project ID for BigQuery and Vertex AI Claude
CLOUD_ML_REGION=us-central1 # optional, defaults to us-central1
```

### 6. (Optional) Install pre-commit hooks

```bash
pre-commit install
```

---

## Running the API

```bash
make api
```

This starts `uvicorn` on `http://localhost:8000`. The server fetches the BigQuery table schema at startup and injects it into the agent's system prompt.

**Default dataset configuration** (in `utils/file_paths.py`):
- Dataset: `tableau_sample_datasets`
- Table: `superstore_sales`
- Location: `us-central1`

---

## API Reference

All endpoints are prefixed with `/api/v0`.

### `GET /api/v0/health`

Health check.

```json
// Response 200
{ "status": "healthy" }
```

---

### `POST /api/v0/chat`

Submit a natural language question to the agent.

**Request body:**

```json
{
  "question": "What are the total sales by region?",
  "session_id": "optional-uuid-for-session-continuation",
  "checkpoint_dir": "optional-path-to-checkpoint-directory"
}
```
- `question`: the natural language question
- `session_id`: the UUID to continue an existing session
- `checkpoint_dir`: the path for storing conversation checkpoints

**Response:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "result": "Total sales by region:\n- West: $725,457\n- East: $678,781\n..."
}
```

---

### `GET /api/v0/conversation-history`

Retrieve all messages in a session.

**Query params:** `session_id=<uuid>`

**Response:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "messages": [
    {
      "type": "human",
      "uuid": "...",
      "session_id": "...",
      "message": { "role": "user", "content": "What are total sales?" }
    }
  ]
}
```

---

### `DELETE /api/v0/clean-up`

Delete checkpoint files for the current session.

```json
// Response 200
{ "status": "cleaned" }

// Response 200 (nothing to delete)
{ "status": "nothing to clean" }
```

---

## Testing

```bash
python -m pytest
```

Test files mirror the source structure under `tests/medium_claude_sdk_bigquery_agent/`. The CI pipeline (`.github/workflows/ci.yaml`) runs the full test suite on every push and pull request.

---

## Code Quality

```bash
make lint-code    # runs isort + black + ruff
```

Pre-commit hooks enforce formatting and linting on every commit. Configuration lives in `.pre-commit-config.yaml` and `pyproject.toml`.
