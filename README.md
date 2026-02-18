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

| Variable | Default | Description |
| --- | --- | --- |
| `OPENAI_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible API base URL (Ollama or OpenAI). |
| `OPENAI_API_KEY` | `ollama` | API key (ignored by Ollama). |
| `OPENAI_MODEL` | `llama2` | Model name to use. |
| `OPENAI_MAX_RETRIES` | `3` | Max retry attempts for transient LLM API failures. |
| `OPENAI_BACKOFF_SECONDS` | `1.0` | Base delay in seconds for exponential retry backoff. |
| `OPENAI_VERIFY_SSL` | `true` | Toggle TLS certificate verification for OpenAI HTTP calls. |
| `OPENAI_TIMEOUT_SECONDS` | `30.0` | Timeout in seconds for OpenAI HTTP calls. |
| `DATABASE_URL` | `sqlite:///./qa_chatbot.db` | SQLite connection string. |
| `DATABASE_ECHO` | `false` | SQLAlchemy logging toggle. |
| `DASHBOARD_OUTPUT_DIR` | `./dashboard_html` | Output folder for generated dashboards. |
| `DASHBOARD_TAILWIND_SCRIPT_SRC` | `https://cdn.tailwindcss.com` | Script URL for Tailwind in browser dashboard templates. |
| `DASHBOARD_PLOTLY_SCRIPT_SRC` | `https://cdn.plot.ly/plotly-2.27.0.min.js` | Script URL for Plotly in browser dashboard templates. |
| `JIRA_BASE_URL` | `https://jira.example.com` | Jira base URL for generated issue links. |
| `JIRA_USERNAME` | `jira-user@example.com` | Jira username stored in app settings for adapter wiring. |
| `JIRA_API_TOKEN` | `replace-with-jira-api-token` | Jira API token stored in app settings for adapter wiring. |
| `GRADIO_SERVER_PORT` | `7860` | Gradio server port. |
| `GRADIO_SHARE` | `false` | Generate a public Gradio share link. |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `INPUT_MAX_CHARS` | `2000` | Max characters accepted per chat message. |
| `RATE_LIMIT_REQUESTS` | `8` | Max messages per session within the rate limit window. |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate limit window size in seconds. |

## Observability and safeguards

- **Metrics**: The app tracks submission counts and recent LLM latency in memory.
- **Rate limiting**: Per-session sliding window rate limiter (defaults to 8 messages/minute).
- **Input limits**: Messages are trimmed to `INPUT_MAX_CHARS` to prevent oversized payloads.
