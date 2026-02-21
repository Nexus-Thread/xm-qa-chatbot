# xm-qa-chatbot

Project navigation map: [docs/project-navigation.md](docs/project-navigation.md)

## Running the chatbot

1. Install dependencies:
   ```bash
   pip install -e .[dev]
   ```
2. Start the chatbot:
   ```bash
   python -m qa_chatbot.main
   ```
3. Open the UI at `http://localhost:7860`.

## Running with Docker

1. Build the image:
   ```bash
   docker build -t qa-chatbot:latest .
   ```
2. Run the container:
   ```bash
   docker run --rm -p 7860:7860 --env-file .env qa-chatbot:latest
   ```
3. Open the UI at `http://localhost:7860`.

When running in Docker, `OPENAI_BASE_URL=http://localhost:11434/v1` points to the container itself.
If your Ollama/OpenAI-compatible endpoint runs on the host machine, use
`OPENAI_BASE_URL=http://host.docker.internal:11434/v1`.

### Running with Docker Compose

1. Create `.env` (if not present):
   ```bash
   cp .env.example .env
   ```
2. Build and run:
   ```bash
   docker compose up --build
   ```

The Compose setup uses `Dockerfile` for the build and loads variables from `.env` by default.

## Dashboard artifacts

Each submission refreshes static dashboard files under `DASHBOARD_OUTPUT_DIR` (default: `./dashboard_html`).

For offline or self-hosted environments, dashboard JS asset URLs are configurable via
`DASHBOARD_TAILWIND_SCRIPT_SRC` and `DASHBOARD_PLOTLY_SCRIPT_SRC`.

Generated outputs include:
- Browser-ready HTML pages: `overview.html`, `team-*.html`, `trends.html`
- Confluence-ready local artifacts: `overview.confluence.html`, `team-*.confluence.html`, `trends.confluence.html`

### Generate dashboard files from existing data

To regenerate all dashboard files from existing database submissions:

```bash
python scripts/generate_dashboard.py
```

Options:
- `--database-url`: Database connection URL (default: value from `DATABASE_URL`)
- `--output-dir`: Output directory for dashboard files (default: value from `DASHBOARD_OUTPUT_DIR`)
- `--months`: Number of recent months to include (default: 6)
- `--log-level`: Logging level (default: value from `LOG_LEVEL`)

### Serve browser dashboards locally

Serve the generated dashboard HTML locally:

```bash
python scripts/serve_dashboard.py --directory ./dashboard_html --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/overview.html` in your browser.

For Confluence prep, use the generated `*.confluence.html` files from the same directory.

## Configuration

Copy `.env.example` to `.env` and adjust values as needed. Environment variables override `.env` values.
The application loads settings at startup via the environment input adapter and validates configuration,
raising an error if values are missing or invalid.

Configuration precedence is: CLI flags (where available) → environment variables / `.env` → code defaults.

## OpenAI migration notes

The LLM adapter uses an OpenAI-compatible API. To switch from a local provider (e.g. Ollama) to OpenAI:

1. Set `OPENAI_BASE_URL` to `https://api.openai.com/v1`.
2. Set `OPENAI_API_KEY` to your OpenAI API key.
3. Update `OPENAI_MODEL` to an OpenAI chat model (e.g., `gpt-4o-mini`).

Retries use exponential backoff and are configurable via `OPENAI_MAX_RETRIES` and `OPENAI_BACKOFF_SECONDS`.
Transport behavior is configurable via `OPENAI_VERIFY_SSL` and `OPENAI_TIMEOUT_SECONDS`.

## Environment variables

| Variable | Default | Purpose | Example |
| --- | --- | --- | --- |
| `OPENAI_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible API base URL used by the structured extraction adapter. | `https://api.openai.com/v1` |
| `OPENAI_API_KEY` | `ollama` | API key used for provider authentication (ignored by Ollama). | `sk-your-openai-api-key` |
| `OPENAI_MODEL` | `llama2` | Model identifier used for extraction calls. | `gpt-4o-mini` |
| `OPENAI_MAX_RETRIES` | `3` | Maximum retry attempts for transient LLM transport failures. | `5` |
| `OPENAI_BACKOFF_SECONDS` | `1.0` | Base backoff delay used by exponential retry logic. | `2.0` |
| `OPENAI_VERIFY_SSL` | `true` | Enables TLS certificate verification for OpenAI HTTP requests. | `true` |
| `OPENAI_TIMEOUT_SECONDS` | `30.0` | Request timeout for OpenAI HTTP calls. | `60.0` |
| `DATABASE_URL` | `sqlite:///./qa_chatbot.db` | SQLAlchemy connection URL for submission storage. | `sqlite:///./qa_chatbot.db` |
| `DATABASE_ECHO` | `false` | Enables SQLAlchemy SQL echo logging for debugging. | `true` |
| `DATABASE_TIMEOUT_SECONDS` | `5.0` | SQLite lock wait timeout in seconds; also applied as `PRAGMA busy_timeout`. | `10.0` |
| `DASHBOARD_OUTPUT_DIR` | `./dashboard_html` | Output directory where dashboard HTML artifacts are generated. | `./dashboard_html` |
| `DASHBOARD_TAILWIND_SCRIPT_SRC` | `https://cdn.tailwindcss.com` | Script source used to load Tailwind in browser dashboard templates. | `https://cdn.tailwindcss.com` |
| `DASHBOARD_PLOTLY_SCRIPT_SRC` | `https://cdn.plot.ly/plotly-2.27.0.min.js` | Script source used to load Plotly in browser dashboard templates. | `https://cdn.plot.ly/plotly-2.27.0.min.js` |
| `JIRA_BASE_URL` | `https://jira.example.com` | Base Jira URL used when building issue/filter links. | `https://your-company.atlassian.net` |
| `JIRA_USERNAME` | `jira-user@example.com` | Jira username stored in app settings for adapter wiring. | `qa-bot@your-company.com` |
| `JIRA_API_TOKEN` | `replace-with-jira-api-token` | Jira API token stored in app settings for adapter wiring. | `replace-with-jira-api-token` |
| `GRADIO_SERVER_PORT` | `7860` | Local port used by the Gradio UI server. | `7860` |
| `GRADIO_SHARE` | `false` | Enables public Gradio share URL generation. | `false` |
| `LOG_LEVEL` | `INFO` | Application logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). | `DEBUG` |
| `LOG_FORMAT` | `text` | Application log formatter mode (`text` or `json`) for human-readable or structured output. | `json` |
| `INPUT_MAX_CHARS` | `2000` | Maximum user message length accepted by the chat input adapter. | `4000` |
| `RATE_LIMIT_REQUESTS` | `8` | Maximum chat requests allowed per rate-limit window. | `10` |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate-limit window size, in seconds. | `60` |

## Observability and safeguards

- **Metrics**: The app tracks submission counts and recent LLM latency in memory.
- **Rate limiting**: Per-session sliding window rate limiter (defaults to 8 messages/minute).
- **Input limits**: Messages are trimmed to `INPUT_MAX_CHARS` to prevent oversized payloads.

## Testing

Run all tests and enforce coverage threshold:

```bash
pytest tests/
```

The test suite enforces a minimum of 98% coverage via pytest configuration.

Coverage scope is intentionally limited to `src/qa_chatbot` (`--cov=src/qa_chatbot`).
The `scripts/` directory is currently excluded from measured coverage because scripts are
operational entry points, and their behavior is validated through direct execution flows
and integration/e2e coverage of the underlying application modules.

Useful marker-based subsets:

```bash
pytest -m integration --no-cov
pytest -m e2e --no-cov
pytest -m "not slow" --no-cov
```

Playwright e2e tests require Chromium binaries:

```bash
python -m playwright install chromium
pytest --browser chromium tests/e2e/test_chatbot_positive_flow_playwright.py -m e2e --no-cov
```

When using `pytest-playwright`, you can also run marker-based e2e suites with an explicit browser:

```bash
pytest --browser chromium -m e2e --no-cov
```

Or run a single Playwright e2e file directly:

```bash
pytest tests/e2e/test_chatbot_positive_flow_playwright.py -m e2e --no-cov
```
