# XM QA Chatbot - Implementation Plan

## Executive Summary

An LLM-powered conversational data collection system where teams submit QA metrics, project tracking data, and daily updates through natural language chat. The system extracts structured data, stores it by team and month, and generates a multi-view HTML dashboard.

**Core Architecture**: Hexagonal (ports & adapters)  
**Primary Technologies**: Python 3.11+, Gradio, OpenAI SDK (Ollama/OpenAI), SQLite, Jinja2  
**Deployment**: Docker containerized

---

## Progress Overview

**Current Phase**: Phase 1 - Core Domain & Storage Foundation  
**Overall Completion**: 0/5 phases (0%)

### Implementation Phases Status
- [ ] **Phase 1**: Core Domain & Storage Foundation (Week 1)
- [ ] **Phase 2**: LLM Integration & Extraction (Week 2)
- [ ] **Phase 3**: Gradio Chatbot Interface (Week 3)
- [ ] **Phase 4**: Dashboard Generation (Week 4)
- [ ] **Phase 5**: Polish & Production Readiness (Week 5)

### Next Immediate Tasks
1. Define storage port
2. Implement SQLite adapter
3. Add tests for storage + domain

**Blockers**: None

---

## System Overview

### Key Features

1. **Conversational Data Collection**
   - Teams chat with Gradio-based interface
   - LLM extracts structured data from natural language
   - Smart month selection with defaults (current month + grace period)
   - Team identification during conversation

2. **Data Categories**
   - **QA Metrics**: test results, bug counts, coverage, deployment readiness
   - **Project Tracking**: sprint progress, blockers, milestones, risks
   - **Daily Updates**: completed tasks, planned work, capacity, issues

3. **Dashboard Views**
   - Overview: all teams' current month summary
   - Per-Team: historical data and trends for individual teams
   - Trends: cross-team analytics and time-based patterns

4. **Flexible Architecture**
   - Swappable storage backends (SQLite → PostgreSQL)
   - Swappable LLM providers (Ollama → OpenAI)
   - Event-driven dashboard regeneration

---

## Architecture Design

### Hexagonal Architecture Layers

```
src/qa_chatbot/
├── domain/                           # Core business logic
│   ├── entities/
│   │   ├── team_data.py             # TeamData aggregate
│   │   └── submission.py            # Submission entity
│   ├── value_objects/
│   │   ├── time_window.py           # Month selection logic
│   │   ├── team_id.py               # Team identifier
│   │   ├── qa_metrics.py            # QA-specific metrics
│   │   ├── project_status.py        # Project tracking data
│   │   └── daily_update.py          # Daily standup data
│   ├── services/
│   │   └── validation_service.py    # Cross-entity validation
│   └── exceptions.py                # Domain-specific errors
│
├── application/                      # Use cases & orchestration
│   ├── use_cases/
│   │   ├── submit_team_data.py      # Main submission workflow
│   │   ├── extract_structured_data.py # LLM extraction orchestration
│   │   ├── get_dashboard_data.py    # Query for dashboard views
│   │   └── list_teams.py            # Team management
│   ├── ports/
│   │   ├── input/
│   │   │   └── conversation_port.py # Chat interface contract
│   │   └── output/
│   │       ├── storage_port.py      # Persistence interface
│   │       ├── llm_port.py          # LLM extraction interface
│   │       └── dashboard_port.py    # Dashboard generation interface
│   └── dtos/
│       ├── submission_command.py    # Input DTOs
│       └── dashboard_query.py       # Query DTOs
│
└── adapters/
    ├── input/
    │   └── gradio/
    │       ├── __init__.py
    │       ├── adapter.py           # Gradio chat interface
    │       ├── conversation_manager.py # State management
    │       └── formatters.py        # Response formatting
    │
    └── output/
        ├── persistence/
        │   ├── sqlite/
        │   │   ├── __init__.py
        │   │   ├── adapter.py       # SQLite implementation
        │   │   ├── models.py        # SQLAlchemy models
        │   │   ├── mappers.py       # Domain ↔ ORM mapping
        │   │   └── migrations/      # Schema migrations
        │   └── __init__.py
        │
        ├── llm/
        │   ├── openai/
        │   │   ├── __init__.py
        │   │   ├── adapter.py       # OpenAI SDK adapter
        │   │   ├── prompts.py       # Extraction prompts
        │   │   ├── function_schemas.py # Structured output schemas
        │   │   └── retry_logic.py   # Error handling
        │   └── __init__.py
        │
        └── dashboard/
            ├── html/
            │   ├── __init__.py
            │   ├── adapter.py       # HTML generator
            │   ├── templates/       # Jinja2 templates
            │   │   ├── overview.html
            │   │   ├── team_detail.html
            │   │   └── trends.html
            │   └── static/          # CSS/JS assets
            └── __init__.py
```

### Data Flow

```
User → Gradio → ConversationPort → SubmitTeamDataUseCase
                                          ↓
                                    ExtractStructuredDataUseCase
                                          ↓
                                    LLMPort (OpenAI Adapter)
                                          ↓
                                    Domain validation
                                          ↓
                                    StoragePort (SQLite Adapter)
                                          ↓
                                    DashboardPort (HTML Adapter)
```

---

## Implementation Phases

### Phase 1: Core Domain & Storage Foundation (Week 1)

**Goal**: Establish domain models and persistence without UI

#### Tasks

**1. Project Setup**
- [x] Initialize Python project with `pyproject.toml`
- [x] Configure dev tools (ruff, mypy, pytest)
- [x] Set up directory structure
- [x] Create initial ADR for hexagonal architecture choice

**2. Domain Layer**
- [x] Create `TeamId` value object with validation
- [x] Create `TimeWindow` value object with smart defaults
- [x] Create `QAMetrics` value object
- [x] Create `ProjectStatus` value object
- [x] Create `DailyUpdate` value object
- [x] Create `Submission` entity
- [x] Create `TeamData` aggregate (collection of submissions)
- [x] Define domain exceptions: `InvalidTeamIdError`, `InvalidTimeWindowError`, etc.

**3. Storage Port Definition**
- [ ] Define `StoragePort` protocol interface
- [ ] Document port methods and contracts
   ```python
   class StoragePort(Protocol):
       def save_submission(self, submission: Submission) -> None: ...
       def get_submissions_by_team(self, team_id: TeamId, month: TimeWindow) -> list[Submission]: ...
       def get_all_teams(self) -> list[TeamId]: ...
       def get_submissions_by_month(self, month: TimeWindow) -> list[Submission]: ...
   ```

**4. SQLite Adapter**
- [ ] Create SQLAlchemy models with JSON fields for flexible schema
- [ ] Implement mapper classes (domain ↔ ORM)
- [ ] Set up Alembic for migrations
- [ ] Create initial migration scripts
- [ ] Implement connection management

**5. Testing**
- [ ] Write unit tests for domain logic
- [ ] Write integration tests for SQLite adapter
- [ ] Create test fixtures for sample data
- [ ] Verify 90%+ test coverage on domain layer

**Deliverable**: Functioning persistence layer with tests

---

### Phase 2: LLM Integration & Extraction (Week 2)

**Goal**: Extract structured data from natural language conversations

#### Tasks

**1. LLM Port Definition**
- [ ] Define `LLMPort` protocol interface
- [ ] Document extraction methods and contracts
   ```python
   class LLMPort(Protocol):
       def extract_team_id(self, conversation: str) -> TeamId: ...
       def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow: ...
       def extract_qa_metrics(self, conversation: str) -> QAMetrics: ...
       def extract_project_status(self, conversation: str) -> ProjectStatus: ...
       def extract_daily_update(self, conversation: str) -> DailyUpdate: ...
   ```

**2. OpenAI Adapter**
- [ ] Implement configuration for `base_url` (Ollama/OpenAI) and `api_key`
- [ ] Create client initialization and connection testing
- [ ] Implement error handling and retry logic
- [ ] Add token usage tracking

**3. Structured Extraction**
- [ ] Define Pydantic schemas for function calling
- [ ] Create prompt templates for each data category
- [ ] Design system prompt for chatbot personality
- [ ] Implement context management for multi-turn conversations

**4. Extraction Prompts Design**
- [ ] Create team identification prompts
- [ ] Create month selection prompts with smart defaults
- [ ] Create QA metrics extraction prompts
- [ ] Create project tracking extraction prompts
- [ ] Create daily updates extraction prompts

**5. Use Cases**
- [ ] Implement `ExtractStructuredDataUseCase` to orchestrate LLM calls
- [ ] Implement `SubmitTeamDataUseCase` (validate → persist → trigger dashboard)
- [ ] Add error handling for ambiguous inputs

**6. Testing**
- [ ] Write unit tests with mock LLM responses
- [ ] Write integration tests with Ollama (if available)
- [ ] Test conversation flows with edge cases

**Deliverable**: Working LLM extraction pipeline with tests

---

### Phase 3: Gradio Chatbot Interface (Week 3)

**Goal**: Build conversational UI for data submission

#### Tasks

**1. Conversation State Management**
- [ ] Implement session state tracking (team identified? month selected? data collected?)
- [ ] Add conversation history persistence
- [ ] Create multi-step flow orchestration

**2. Gradio Input Adapter**
- [ ] Set up Gradio chat interface
- [ ] Implement message handling and routing
- [ ] Integrate with `SubmitTeamDataUseCase`
- [ ] Add error message formatting

**3. Conversation Flow Implementation**
- [ ] Implement welcome message
- [ ] Implement team identification (extract from first message or prompt)
- [ ] Implement month selection with grace period logic
- [ ] Implement QA metrics data collection
- [ ] Implement project status data collection
- [ ] Implement daily updates data collection
- [ ] Implement confirmation and storage step
- [ ] Implement success message

**4. User Experience**
- [ ] Design clear prompts and guidance
- [ ] Implement error messages in natural language
- [ ] Create confirmation summaries before saving
- [ ] Add option to edit/retry

**5. Configuration**
- [ ] Set up environment variables for LLM settings
- [ ] Configure Gradio server settings
- [ ] Set up logging

**6. Testing**
- [ ] Perform manual testing with various conversation styles
- [ ] Write E2E tests with Gradio test client
- [ ] Test error scenarios (invalid team, wrong month format, etc.)

**Deliverable**: Functional chatbot for data submission

---

### Phase 4: Dashboard Generation (Week 4)

**Goal**: Multi-view HTML dashboard with team data

#### Tasks

**1. Dashboard Port Definition**
- [ ] Define `DashboardPort` protocol interface
- [ ] Document dashboard generation methods
   ```python
   class DashboardPort(Protocol):
       def generate_overview(self, month: TimeWindow) -> Path: ...
       def generate_team_detail(self, team_id: TeamId, months: list[TimeWindow]) -> Path: ...
       def generate_trends(self, teams: list[TeamId], months: list[TimeWindow]) -> Path: ...
   ```

**2. HTML Templates (Jinja2)**
- [ ] Create overview template with cards for each team's latest submission
- [ ] Create team detail template with historical data and charts
- [ ] Create trends template with cross-team comparison and time-series analysis
- [ ] Set up Jinja2 template engine

**3. Data Aggregation**
- [ ] Implement `GetDashboardDataQuery` use case
- [ ] Create aggregation logic for metrics
- [ ] Implement trend calculation (week-over-week, month-over-month)

**4. Static Assets**
- [ ] Integrate CSS framework (Tailwind or Bootstrap)
- [ ] Add JavaScript for interactivity (Chart.js for visualizations)
- [ ] Implement responsive design

**5. Dashboard Update Strategy**
- [ ] Implement event-driven regeneration on new submission
- [ ] Add optional scheduled periodic updates (cron job)
- [ ] Implement atomic file replacement for zero-downtime updates

**6. File Output**
- [ ] Configure output directory
- [ ] Set up static file server (optional: simple HTTP server)
- [ ] Add cloud storage integration (optional: S3, GCS)

**7. Testing**
- [ ] Write snapshot tests for HTML output
- [ ] Add visual regression tests (optional: Playwright)
- [ ] Test data aggregation logic

**Deliverable**: Multi-view dashboard with auto-updates

---

### Phase 5: Polish & Production Readiness (Week 5)

**Goal**: Production-grade deployment and documentation

#### Tasks

**1. Configuration Management**
- [ ] Implement environment variable validation
- [ ] Create `.env.example` template
- [ ] Write configuration documentation

**2. Error Handling & Observability**
- [ ] Implement structured logging (JSON format)
- [ ] Set up error tracking and alerting
- [ ] Add metrics collection (submission counts, LLM latency)
- [ ] Create health check endpoint

**3. Docker Deployment**
- [ ] Create multi-stage Dockerfile
- [ ] Set up Docker Compose for local development
- [ ] Configure volume mounting for persistence
- [ ] Document environment configuration

**4. Documentation**
- [ ] Write comprehensive `README.md` (setup, usage, configuration)
- [ ] Create `CONTRIBUTING.md` with development guidelines
- [ ] Document ADRs for key decisions
- [ ] Create API documentation for ports

**5. Security**
- [ ] Implement API key management (environment variables, secrets)
- [ ] Add input sanitization
- [ ] Configure rate limiting for Gradio

**6. Performance**
- [ ] Add database indexing
- [ ] Implement LLM response caching (optional)
- [ ] Create dashboard caching strategy

**7. Testing & Quality Gate**
- [ ] Run full test suite execution
- [ ] Generate coverage report (aim for >80%)
- [ ] Execute linting and type checking
- [ ] Run integration smoke tests

**Deliverable**: Production-ready system with documentation

---

## Data Schema Design

### SQLite Schema

```sql
CREATE TABLE submissions (
    id TEXT PRIMARY KEY,
    team_id TEXT NOT NULL,
    month TEXT NOT NULL,  -- ISO format: YYYY-MM
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    qa_metrics JSON,      -- Flexible schema
    project_status JSON,
    daily_update JSON,
    raw_conversation TEXT, -- For auditing
    UNIQUE(team_id, month)
);

CREATE INDEX idx_team_month ON submissions(team_id, month);
CREATE INDEX idx_month ON submissions(month);
```

### Domain Models

```python
@dataclass(frozen=True)
class QAMetrics:
    tests_passed: int
    tests_failed: int
    test_coverage_percent: float
    bug_count: int
    critical_bugs: int
    deployment_ready: bool

@dataclass(frozen=True)
class ProjectStatus:
    sprint_progress_percent: float
    blockers: list[str]
    milestones_completed: list[str]
    risks: list[str]

@dataclass(frozen=True)
class DailyUpdate:
    completed_tasks: list[str]
    planned_tasks: list[str]
    capacity_hours: float
    issues: list[str]

@dataclass
class Submission:
    id: str
    team_id: TeamId
    month: TimeWindow
    qa_metrics: QAMetrics | None
    project_status: ProjectStatus | None
    daily_update: DailyUpdate | None
    created_at: datetime
```

---

## LLM Prompt Engineering Strategy

### System Prompt

```
You are a helpful data collection assistant for software development teams.
Your role is to extract structured information from natural conversations about:
1. QA metrics (test results, bugs, coverage)
2. Project tracking (progress, blockers, milestones)
3. Daily updates (tasks, capacity, issues)

Be conversational, ask clarifying questions, and confirm understanding before saving data.
Always identify the team and the reporting month first.
```

### Extraction Functions (OpenAI Function Calling)

```python
EXTRACT_QA_METRICS = {
    "name": "extract_qa_metrics",
    "description": "Extract QA testing metrics from conversation",
    "parameters": {
        "type": "object",
        "properties": {
            "tests_passed": {"type": "integer"},
            "tests_failed": {"type": "integer"},
            "test_coverage_percent": {"type": "number"},
            "bug_count": {"type": "integer"},
            "critical_bugs": {"type": "integer"},
            "deployment_ready": {"type": "boolean"}
        },
        "required": ["tests_passed", "tests_failed"]
    }
}
```

### Conversation Flow Prompts

1. **Team Identification**
   - "Hi! Which team are you from?"
   - Fallback: Extract from message like "I'm from the Frontend team"

2. **Month Selection**
   - "Which month is this data for? (default: January 2026)"
   - Logic: Current month until 2nd of next month, then prompt for previous

3. **Data Collection**
   - "Tell me about your QA status this month - test results, bugs found, coverage percentage..."
   - "What's your project progress? Any blockers or completed milestones?"
   - "What did you work on today? Any issues or upcoming plans?"

4. **Confirmation**
   - "Let me confirm: [summary of extracted data]. Is this correct?"
   - Options: "Yes, save it" / "No, let me correct..."

---

## Testing Strategy

### Test Pyramid

```
     E2E Tests (5%)
    ───────────────
   Integration (20%)
  ─────────────────────
 Unit Tests (75%)
─────────────────────────
```

### Test Organization

```
tests/
├── unit/
│   ├── domain/
│   │   ├── test_team_data.py
│   │   ├── test_time_window.py
│   │   └── test_value_objects.py
│   ├── application/
│   │   ├── test_submit_team_data.py
│   │   └── test_extract_structured_data.py
│   └── adapters/
│       └── test_prompt_formatting.py
│
├── integration/
│   ├── adapters/
│   │   ├── test_sqlite_adapter.py
│   │   ├── test_openai_adapter.py  # With Ollama if available
│   │   └── test_dashboard_adapter.py
│   └── test_full_submission_flow.py
│
└── e2e/
    └── test_chatbot_conversation.py
```

### Key Test Scenarios

- **Domain**: Time window defaults, validation rules
- **Application**: Use case orchestration, error handling
- **Adapters**: Database CRUD, LLM extraction, HTML generation
- **Integration**: Full conversation → extraction → storage → dashboard
- **E2E**: Gradio chat session with assertions on stored data

---

## Configuration & Environment Variables

```bash
# LLM Configuration
OPENAI_BASE_URL=http://localhost:11434/v1  # Ollama endpoint
OPENAI_API_KEY=ollama                       # Not required for Ollama
OPENAI_MODEL=llama2                         # Model name

# Storage Configuration
DATABASE_URL=sqlite:///./qa_chatbot.db
DATABASE_ECHO=false                         # SQLAlchemy logging

# Dashboard Configuration
DASHBOARD_OUTPUT_DIR=./dashboard_html
DASHBOARD_AUTO_REGENERATE=true

# Gradio Configuration
GRADIO_SERVER_PORT=7860
GRADIO_SHARE=false                          # Public link

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json                             # json or text
```

---

## Deployment Architecture

### Local Development

```bash
# Start Ollama (separate terminal)
ollama serve

# Pull model
ollama pull llama2

# Start chatbot
python -m qa_chatbot.main

# Access: http://localhost:7860
```

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  chatbot:
    build: .
    ports:
      - "7860:7860"
    environment:
      - OPENAI_BASE_URL=http://ollama:11434/v1
      - DATABASE_URL=sqlite:////data/qa_chatbot.db
      - DASHBOARD_OUTPUT_DIR=/output
    volumes:
      - chatbot-data:/data
      - dashboard-output:/output
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama

  dashboard-server:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - dashboard-output:/usr/share/nginx/html:ro

volumes:
  chatbot-data:
  ollama-data:
  dashboard-output:
```

---

## Migration Path: Ollama → OpenAI

**Step 1**: Change environment variables
```bash
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
```

**Step 2**: Adjust prompts if needed (GPT-4 may have different behavior)

**Step 3**: No code changes required (same adapter)

---

## ADR Candidates

Key decisions to document:

1. **ADR-001**: Hexagonal Architecture Choice
   - Context: Need swappable components
   - Decision: Hexagonal with strict port/adapter separation
   - Consequences: More upfront structure, easier to swap backends

2. **ADR-002**: OpenAI SDK for Ollama
   - Context: Need local and cloud LLM support
   - Decision: Use OpenAI SDK with configurable base_url
   - Consequences: Single adapter, easy migration

3. **ADR-003**: SQLite with JSON Fields
   - Context: Flexible schema for evolving data requirements
   - Decision: SQLite + JSON columns, migrateable to PostgreSQL
   - Consequences: Flexible schema, limited query capabilities

4. **ADR-004**: Static HTML Generation
   - Context: Dashboard display strategy
   - Decision: Generate static HTML files, optional server
   - Consequences: Simple deployment, no database queries on view

5. **ADR-005**: Month-Based Data Organization
   - Context: Time window for data collection
   - Decision: Monthly reporting with grace period defaults
   - Consequences: Simple time logic, may need week/day views later

---

## Success Criteria

### Phase 1
- [ ] Domain models with comprehensive tests
- [ ] SQLite adapter with CRUD operations
- [ ] 90%+ unit test coverage on domain layer

### Phase 2
- [ ] LLM adapter extracting structured data
- [ ] Integration tests with Ollama
- [ ] Error handling for ambiguous inputs

### Phase 3
- [ ] Gradio chatbot accepting natural language
- [ ] Multi-turn conversation state management
- [ ] E2E test for full submission flow

### Phase 4
- [ ] Three dashboard views (overview, team, trends)
- [ ] Auto-regeneration on new submissions
- [ ] Responsive design

### Phase 5
- [ ] Docker deployment working
- [ ] Documentation complete
- [ ] Quality gate passing (lint, type, test)
- [ ] Migration path to OpenAI validated

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM extraction quality varies | High | High | Extensive prompt testing, confirmation step |
| Ollama model availability | Medium | Medium | Fallback to smaller models, cloud option |
| SQLite scalability limits | Low | Medium | Migration path to PostgreSQL documented |
| Gradio performance issues | Low | Medium | Rate limiting, async processing |
| Dashboard generation slow | Medium | Low | Background tasks, caching strategy |

---

## Future Enhancements (Post-MVP)

1. **Authentication & Authorization**
   - Team-specific logins
   - Role-based access (read-only viewers)

2. **Advanced Analytics**
   - Predictive trends
   - Anomaly detection
   - Cross-team benchmarking

3. **Notifications**
   - Slack/email reminders for data submission
   - Alert on critical metrics (high bug count)

4. **API Layer**
   - REST API for programmatic access
   - Webhook integrations

5. **Multi-Language Support**
   - i18n for dashboard
   - LLM prompts in multiple languages

6. **Data Export**
   - CSV/Excel export
   - API for external analytics tools

---

## Getting Started (Post-Implementation)

```bash
# Clone repository
git clone git@github.com:Nexus-Thread/xm-qa-chatbot.git
cd xm-qa-chatbot

# Install dependencies
pip install -e ".[dev]"

# Start Ollama
ollama serve
ollama pull llama2

# Run tests
pytest tests/

# Start chatbot
python -m qa_chatbot.main

# Access dashboard
open dashboard_html/overview.html
```

---

## References

- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Ollama Documentation](https://ollama.ai/docs)
- [Gradio Documentation](https://www.gradio.app/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-03  
**Status**: Planning Phase  
**Next Review**: After Phase 1 completion
