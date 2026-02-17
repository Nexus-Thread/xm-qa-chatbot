# Project Navigation: xm-qa-chatbot

**Package name:** `qa_chatbot`
**Last updated:** 2026-02-04

## Source Structure
- `src/qa_chatbot/domain/` - Domain entities, value objects, and business rules
  - `entities/business_stream.py` - Business stream entity
  - `entities/project.py` - Project entity
  - `entities/reporting_period.py` - Reporting period entity
  - `entities/submission.py` - Submission domain entity
  - `registries/stream_project_registry/` - Stream and project registry
    - `builder.py` - Default registry construction
    - `registry.py` - Registry implementation
  - `value_objects/metrics.py` - QA metrics value object
  - `value_objects/portfolio_aggregates.py` - Portfolio aggregates value object
  - `value_objects/extraction_confidence.py` - Extraction confidence value object
  - `value_objects/project_id.py` - Project identifier value object
  - `value_objects/stream_id.py` - Stream identifier value object
  - `value_objects/submission_metrics.py` - Submission metrics value object
  - `value_objects/time_window.py` - Reporting window value object
  - `exceptions.py` - Domain-specific errors

- `src/qa_chatbot/application/` - Use cases, DTOs, and ports
  - `use_cases/extract_structured_data.py` - LLM extraction workflow
  - `use_cases/generate_monthly_report.py` - Monthly report workflow
  - `use_cases/get_dashboard_data.py` - Dashboard data retrieval workflow
  - `use_cases/submit_project_data.py` - Submission processing workflow
  - `dtos/dashboard_data.py` - Dashboard DTOs
  - `dtos/extraction_result.py` - Extraction result DTOs
  - `dtos/report_data.py` - Report DTOs
  - `dtos/submission_command.py` - Submission command DTOs
  - `ports/output/dashboard_port.py` - Dashboard output port
  - `ports/output/jira_port.py` - Jira output port
  - `ports/output/structured_extraction_port.py` - Structured extraction output port
  - `ports/output/metrics_port.py` - Metrics output port
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
  - `output/llm/openai/` - OpenAI transport and client utilities
    - `factory.py` - OpenAI client factory
    - `protocols.py` - Client protocol contracts
    - `transport.py` - Transport wrapper with retries
  - `output/llm/structured_extraction/` - Structured extraction adapter
    - `adapter.py` - OpenAI structured extraction adapter
    - `prompts.py` - Extraction prompt templates
    - `schemas.py` - Extraction response schemas
  - `output/metrics/` - In-memory metrics adapter
    - `adapter.py` - Metrics adapter implementation
  - `output/persistence/sqlite/` - SQLite persistence adapter
    - `adapter.py` - Storage adapter implementation
    - `mappers.py` - ORM/domain mapping
    - `models.py` - SQLAlchemy models
- `src/qa_chatbot/config/` - Configuration and logging
  - `logging_config.py` - Logging setup

## Entry Points
- `src/qa_chatbot/main.py` - Gradio UI bootstrap
- `scripts/serve_dashboard.py` - Serve generated HTML dashboards

## Test Structure
- `tests/unit/domain/` - Domain logic tests
- `tests/unit/application/` - Use case tests
- `tests/unit/adapters/` - Adapter unit tests (includes HTML snapshots)
- `tests/unit/config/` - Config/logging tests
- `tests/integration/adapters/` - Adapter integration tests
- `tests/e2e/` - End-to-end chatbot conversation tests
