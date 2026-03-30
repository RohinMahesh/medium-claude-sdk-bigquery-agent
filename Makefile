create-env:
	conda create medium_claude_sdk_bigquery_agent

activate-env:
	conda activate medium_claude_sdk_bigquery_agent

install-dependencies:
	pip install -r requirement.txt
	pre-commit install

lint-code:
	isort .
	black .
	ruff check .

api:
	uvicorn medium_claude_sdk_bigquery_agent.app:app --reload

initialize-gcp:
	~/google-cloud-sdk/bin/gcloud init

login-gcp:
	~/google-cloud-sdk/bin/gcloud auth application-default login