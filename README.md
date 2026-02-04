# xm-qa-chatbot

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
4. Health check endpoint: `http://localhost:8081/health`.

## Dashboard HTML

Each submission refreshes static dashboard pages under `DASHBOARD_OUTPUT_DIR` (default: `./dashboard_html`).

Serve the generated dashboard HTML locally:

```bash
python scripts/serve_dashboard.py --directory ./dashboard_html --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/overview.html` in your browser.

## Configuration

Copy `.env.example` to `.env` and adjust values as needed. Environment variables override `.env` values.
The application validates configuration at startup and will raise an error if values are missing or invalid.

## OpenAI migration notes

The LLM adapter uses an OpenAI-compatible API. To switch from a local provider (e.g. Ollama) to OpenAI:

1. Set `OPENAI_BASE_URL` to `https://api.openai.com/v1`.
2. Set `OPENAI_API_KEY` to your OpenAI API key.
3. Update `OPENAI_MODEL` to an OpenAI chat model (e.g., `gpt-4o-mini`).

Retries use exponential backoff defined in `src/qa_chatbot/adapters/output/llm/openai/retry_logic.py`.

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `OPENAI_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible API base URL (Ollama or OpenAI). |
| `OPENAI_API_KEY` | `ollama` | API key (ignored by Ollama). |
| `OPENAI_MODEL` | `llama2` | Model name to use. |
| `DATABASE_URL` | `sqlite:///./qa_chatbot.db` | SQLite connection string. |
| `DATABASE_ECHO` | `false` | SQLAlchemy logging toggle. |
| `DASHBOARD_OUTPUT_DIR` | `./dashboard_html` | Output folder for generated dashboards. |
| `GRADIO_SERVER_PORT` | `7860` | Gradio server port. |
| `GRADIO_SHARE` | `false` | Generate a public Gradio share link. |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `LOG_FORMAT` | `json` | Log format (`json` or `text`). |
| `HEALTHCHECK_PORT` | `8081` | Port for the HTTP health check endpoint. |
| `INPUT_MAX_CHARS` | `2000` | Max characters accepted per chat message. |
| `RATE_LIMIT_REQUESTS` | `8` | Max messages per session within the rate limit window. |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate limit window size in seconds. |

## Observability and safeguards

- **Metrics**: The app tracks submission counts and recent LLM latency in memory and includes them in the `/health` payload.
- **Health checks**: `/health` reports database connectivity and recent metrics.
- **Rate limiting**: Per-session sliding window rate limiter (defaults to 8 messages/minute).
- **Input limits**: Messages are trimmed to `INPUT_MAX_CHARS` to prevent oversized payloads.
