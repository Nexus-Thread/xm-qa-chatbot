# Project Navigation: xm-qa-chatbot

**Package name:** `qa_chatbot`
**Last updated:** 2026-02-19

## Source Structure
- `src/qa_chatbot/domain/` - Domain entities, value objects, registries, and business rules
  - `src/qa_chatbot/domain/entities/business_stream.py` - Business stream entity
  - `src/qa_chatbot/domain/entities/project.py` - Project entity
  - `src/qa_chatbot/domain/entities/reporting_period.py` - Reporting period entity
  - `src/qa_chatbot/domain/entities/submission.py` - Submission entity
  - `src/qa_chatbot/domain/registries/stream_project_registry/builder.py` - Registry construction helpers
  - `src/qa_chatbot/domain/registries/stream_project_registry/registry.py` - Stream/project registry implementation
  - `src/qa_chatbot/domain/value_objects/extraction_confidence.py` - Extraction confidence value object
  - `src/qa_chatbot/domain/value_objects/metrics.py` - QA metrics value object
  - `src/qa_chatbot/domain/value_objects/portfolio_aggregates.py` - Portfolio-level aggregates value object
  - `src/qa_chatbot/domain/value_objects/project_id.py` - Project identifier value object
  - `src/qa_chatbot/domain/value_objects/stream_id.py` - Stream identifier value object
  - `src/qa_chatbot/domain/value_objects/submission_metrics.py` - Submission metrics value object
  - `src/qa_chatbot/domain/value_objects/time_window.py` - Reporting window value object
  - `src/qa_chatbot/domain/exceptions.py` - Domain-specific errors

- `src/qa_chatbot/application/` - Use cases, DTOs, ports, and app-level services
  - `src/qa_chatbot/application/use_cases/extract_structured_data.py` - LLM extraction workflow
  - `src/qa_chatbot/application/use_cases/generate_monthly_report.py` - Monthly report generation workflow
  - `src/qa_chatbot/application/use_cases/get_dashboard_data.py` - Dashboard data retrieval workflow
  - `src/qa_chatbot/application/use_cases/submit_project_data.py` - Submission processing workflow
  - `src/qa_chatbot/application/dtos/app_settings.py` - Runtime settings DTOs
  - `src/qa_chatbot/application/dtos/dashboard_data.py` - Dashboard DTOs
  - `src/qa_chatbot/application/dtos/extraction_result.py` - Structured extraction result DTOs
  - `src/qa_chatbot/application/dtos/report_data.py` - Monthly report DTOs
  - `src/qa_chatbot/application/dtos/submission_command.py` - Submission command DTOs
  - `src/qa_chatbot/application/ports/output/dashboard_port.py` - Dashboard output port
  - `src/qa_chatbot/application/ports/output/jira_port.py` - Jira output port
  - `src/qa_chatbot/application/ports/output/metrics_port.py` - Metrics output port
  - `src/qa_chatbot/application/ports/output/storage_port.py` - Persistence output port
  - `src/qa_chatbot/application/ports/output/structured_extraction_port.py` - Structured extraction output port
  - `src/qa_chatbot/application/services/reporting_calculations.py` - Reporting calculation helpers

- `src/qa_chatbot/adapters/` - Input and output adapters
  - `src/qa_chatbot/adapters/input/env/` - Environment/configuration input adapter
    - `src/qa_chatbot/adapters/input/env/adapter.py` - Environment loader adapter
    - `src/qa_chatbot/adapters/input/env/settings.py` - Settings model and validation
  - `src/qa_chatbot/adapters/input/gradio/` - Gradio input adapter
    - `src/qa_chatbot/adapters/input/gradio/adapter.py` - Gradio UI wiring
    - `src/qa_chatbot/adapters/input/gradio/conversation_manager.py` - Conversation/session handling
    - `src/qa_chatbot/adapters/input/gradio/formatters.py` - UI formatting helpers
    - `src/qa_chatbot/adapters/input/gradio/rate_limiter.py` - Per-session message throttling
    - `src/qa_chatbot/adapters/input/gradio/settings.py` - Gradio adapter settings
    - `src/qa_chatbot/adapters/input/gradio/utils.py` - UI helper utilities
  - `src/qa_chatbot/adapters/output/dashboard/` - Dashboard rendering adapters
    - `src/qa_chatbot/adapters/output/dashboard/composite/adapter.py` - Fan-out adapter for multiple dashboard targets
    - `src/qa_chatbot/adapters/output/dashboard/confluence/adapter.py` - Confluence-ready HTML renderer
    - `src/qa_chatbot/adapters/output/dashboard/html/adapter.py` - Browser dashboard HTML renderer
    - `src/qa_chatbot/adapters/output/dashboard/html/templates/` - Jinja templates for dashboard pages
    - `src/qa_chatbot/adapters/output/dashboard/exceptions.py` - Dashboard adapter-specific errors
  - `src/qa_chatbot/adapters/output/jira_mock/adapter.py` - Jira mock output adapter
  - `src/qa_chatbot/adapters/output/llm/openai/` - OpenAI-compatible transport and response handling
    - `src/qa_chatbot/adapters/output/llm/openai/constants.py` - Transport and retry defaults
    - `src/qa_chatbot/adapters/output/llm/openai/factory.py` - OpenAI client construction
    - `src/qa_chatbot/adapters/output/llm/openai/protocols.py` - Transport/client protocol contracts
    - `src/qa_chatbot/adapters/output/llm/openai/response.py` - OpenAI response normalization helpers
    - `src/qa_chatbot/adapters/output/llm/openai/transport.py` - HTTP transport wrapper with retries
  - `src/qa_chatbot/adapters/output/llm/structured_extraction/` - Structured extraction output adapter
    - `src/qa_chatbot/adapters/output/llm/structured_extraction/adapter.py` - Structured extraction adapter implementation
    - `src/qa_chatbot/adapters/output/llm/structured_extraction/exceptions.py` - Extraction adapter-specific errors
    - `src/qa_chatbot/adapters/output/llm/structured_extraction/history.py` - Prompt/response history helpers
    - `src/qa_chatbot/adapters/output/llm/structured_extraction/json_response.py` - JSON response extraction helpers
    - `src/qa_chatbot/adapters/output/llm/structured_extraction/mappers.py` - Adapter-to-DTO mapping helpers
    - `src/qa_chatbot/adapters/output/llm/structured_extraction/parsers.py` - Response parsing helpers
    - `src/qa_chatbot/adapters/output/llm/structured_extraction/prompts.py` - Prompt templates
    - `src/qa_chatbot/adapters/output/llm/structured_extraction/schemas.py` - Structured response schemas
    - `src/qa_chatbot/adapters/output/llm/structured_extraction/settings.py` - Structured extraction adapter settings
  - `src/qa_chatbot/adapters/output/metrics/adapter.py` - In-memory metrics adapter
  - `src/qa_chatbot/adapters/output/persistence/sqlite/` - SQLite persistence adapter
    - `src/qa_chatbot/adapters/output/persistence/sqlite/adapter.py` - SQLAlchemy-backed storage adapter
    - `src/qa_chatbot/adapters/output/persistence/sqlite/mappers.py` - Domain/database mapping helpers
    - `src/qa_chatbot/adapters/output/persistence/sqlite/models.py` - SQLAlchemy persistence models

- `src/qa_chatbot/config/` - Shared runtime configuration
  - `src/qa_chatbot/config/logging_config.py` - Central logging configuration

## Entry Points
- `src/qa_chatbot/main.py` - Main Gradio application bootstrap

## Operational Scripts
- `scripts/submit_data_direct.py` - Submit sample data directly through application wiring
- `scripts/submit_via_api.py` - Submit sample data via HTTP API path
- `scripts/generate_dashboard.py` - Rebuild dashboard pages from stored submissions
- `scripts/serve_dashboard.py` - Serve generated dashboard HTML locally
- `scripts/seed_database.py` - Seed local persistence for development

## Test Structure
- `tests/unit/domain/` - Domain entity/value-object/registry tests
- `tests/unit/application/` - Use case and application-service tests
- `tests/unit/adapters/` - Adapter unit tests (includes HTML snapshots)
- `tests/unit/config/` - Settings and logging configuration tests
- `tests/integration/adapters/` - Adapter integration tests with real integrations
- `tests/e2e/` - End-to-end chatbot conversation coverage
