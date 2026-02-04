# Project Navigation: xm-qa-chatbot

**Package name:** `qa_chatbot`
**Last updated:** 2026-02-04

## Source Structure
- `src/qa_chatbot/domain/` - Domain entities, value objects, and business rules
  - `entities/business_stream.py` - Business stream entity
  - `entities/project.py` - Project entity
  - `entities/reporting_period.py` - Reporting period entity
  - `entities/submission.py` - Submission domain entity
  - `entities/team_data.py` - Team data entity
  - `registries/stream_registry.py` - Business stream registry
  - `services/validation_service.py` - Domain validation rules
  - `value_objects/metrics.py` - QA metrics value object
  - `value_objects/portfolio_aggregates.py` - Portfolio aggregates value object
  - `value_objects/priority_bucket.py` - Priority bucket value object
  - `value_objects/project_id.py` - Project identifier value object
  - `value_objects/time_window.py` - Reporting window value object
  - `exceptions.py` - Domain-specific errors

- `src/qa_chatbot/application/` - Use cases, DTOs, and ports
  - `use_cases/extract_structured_data.py` - LLM extraction workflow
  - `use_cases/generate_monthly_report.py` - Monthly report workflow
  - `use_cases/get_dashboard_data.py` - Dashboard data retrieval workflow
  - `use_cases/submit_team_data.py` - Submission processing workflow
  - `dtos/dashboard_data.py` - Dashboard DTOs
  - `dtos/extraction_result.py` - Extraction result DTOs
  - `dtos/report_data.py` - Report DTOs
  - `dtos/submission_command.py` - Submission command DTOs
  - `ports/output/dashboard_port.py` - Dashboard output port
  - `ports/output/jira_port.py` - Jira output port
  - `ports/output/llm_port.py` - LLM output port
  - `ports/output/metrics_port.py` - Metrics output port
  - `ports/output/release_port.py` - Release output port
  - `ports/output/storage_port.py` - Storage output port

- `src/qa_chatbot/adapters/` - External integrations
  - `input/gradio/` - Gradio UI adapter
    - `adapter.py` - Gradio entrypoint wiring
    - `conversation_manager.py` - Conversation/session handling
    - `formatters.py` - UI formatting helpers
  - `output/dashboard/html/` - Static HTML dashboard renderer
    - `adapter.py` - HTML dashboard adapter
    - `templates/` - Jinja templates
  - `output/jira_mock/` - Jira mock adapter
    - `adapter.py` - Jira mock implementation
  - `output/llm/openai/` - OpenAI-compatible LLM adapter
    - `adapter.py` - LLM adapter implementation
    - `client.py` - OpenAI client wrapper
    - `prompts.py` - Prompt templates
    - `retry_logic.py` - Retry/backoff policy
    - `schemas.py` - LLM response schemas
  - `output/metrics/` - In-memory metrics adapter
    - `adapter.py` - Metrics adapter implementation
  - `output/persistence/sqlite/` - SQLite persistence adapter
    - `adapter.py` - Storage adapter implementation
    - `mappers.py` - ORM/domain mapping
    - `models.py` - SQLAlchemy models
  - `output/releases_mock/` - Release mock adapter
    - `adapter.py` - Release mock implementation

- `src/qa_chatbot/config/` - Configuration and logging
  - `logging_config.py` - Logging setup
  - `reporting_config.py` - Reporting configuration loader
  - `settings.py` - Environment configuration

## Entry Points
- `src/qa_chatbot/main.py` - Gradio UI bootstrap
- `python -m qa_chatbot.main` - Gradio UI bootstrap (module entry)
- `scripts/serve_dashboard.py` - Serve generated HTML dashboards

## Test Structure
- `tests/unit/domain/` - Domain logic tests
- `tests/unit/application/` - Use case tests
- `tests/unit/adapters/` - Adapter unit tests (includes HTML snapshots)
- `tests/unit/config/` - Config/logging tests
- `tests/integration/adapters/` - Adapter integration tests
- `tests/e2e/` - End-to-end chatbot conversation tests
