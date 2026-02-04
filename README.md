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

## Configuration

Copy `.env.example` to `.env` and adjust values as needed. Environment variables override `.env` values.
The application validates configuration at startup and will raise an error if values are missing or invalid.

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
