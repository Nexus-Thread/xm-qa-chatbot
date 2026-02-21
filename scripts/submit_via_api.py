"""Submit test coverage data via Gradio Client API."""

from __future__ import annotations

import sys

from gradio_client import Client


def _echo(message: str = "") -> None:
    """Write a user-facing message to stdout."""
    sys.stdout.write(f"{message}\n")


def _extract_message_content(history_item: dict[str, object]) -> str:
    """Extract normalized text content from a history item payload."""
    raw_content = history_item.get("content")
    if isinstance(raw_content, str):
        return raw_content
    if isinstance(raw_content, list):
        if not raw_content:
            return ""
        first_item = raw_content[0]
        if isinstance(first_item, dict):
            text_value = first_item.get("text", "")
            return text_value if isinstance(text_value, str) else ""
    return ""


def _print_submission_payload() -> None:
    """Print the submission payload summary."""
    _echo("\n" + "=" * 60)
    _echo("SUBMITTING DATA:")
    _echo("  Project: Client Trading")
    _echo("  Period: 2026-01")
    _echo("  Manual Total: 1000")
    _echo("  Manual Created: 100")
    _echo("  Manual Updated: 120")
    _echo("  Automated Total: 500")
    _echo("  Automated Created: 50")
    _echo("  Automated Updated: 30")
    _echo("=" * 60 + "\n")


def _submit_message(
    client: Client,
    message: str,
    history: list[dict[str, object]],
    *,
    step_label: str,
    preview_length: int,
) -> list[dict[str, object]]:
    """Submit one message and print a preview of the assistant response."""
    _echo(step_label)
    _, updated_history = client.predict(message, history, api_name="/respond")
    last_msg = _extract_message_content(updated_history[-1])
    _echo(f"✅ Response: {last_msg[:preview_length]}...\n")
    return updated_history


def _print_final_status(final_response: str) -> None:
    """Print submission outcome summary."""
    _echo("=" * 60)
    if "saved" in final_response.lower():
        _echo("✅ SUCCESS: Data submitted and saved!")
    else:
        _echo("⚠️  WARNING: Submission may not have completed. Check the response above.")
    _echo("=" * 60)


def submit_test_coverage_data() -> None:
    """Submit test coverage data through the Gradio chatbot API."""
    # Connect to the running Gradio server
    client = Client("http://localhost:7860")

    _echo("🔌 Connected to Gradio app at http://localhost:7860")
    _echo("\n📋 Available API endpoints:")
    _echo(client.view_api())
    _print_submission_payload()

    # Step 1: Initialize session
    _echo("Step 1: Initializing session...")
    history = client.predict(api_name="/initialize")
    _echo("✅ Session initialized with welcome message\n")

    # Step 2: Submit project name
    history = _submit_message(
        client,
        "Client Trading",
        history,
        step_label="Step 2: Submitting project 'Client Trading'...",
        preview_length=100,
    )

    # Step 3: Submit reporting period
    history = _submit_message(
        client,
        "2026-01",
        history,
        step_label="Step 3: Submitting period '2026-01'...",
        preview_length=100,
    )

    # Step 4: Submit test coverage data
    _echo("Step 4: Submitting test coverage data...")
    coverage_message = (
        "Manual total: 1000\n"
        "Manual created last month: 100\n"
        "Manual updated last month: 120\n"
        "Automated total: 500\n"
        "Automated created last month: 50\n"
        "Automated updated last month: 30"
    )
    history = _submit_message(
        client,
        coverage_message,
        history,
        step_label="Step 4: Submitting test coverage data...",
        preview_length=150,
    )

    # Step 5: Confirm submission
    _echo("Step 5: Confirming submission...")
    _, history = client.predict("yes", history, api_name="/respond")

    final_response = _extract_message_content(history[-1]) if history else "No response"
    _echo(f"✅ Final Response: {final_response}\n")
    _print_final_status(final_response)


if __name__ == "__main__":
    submit_test_coverage_data()
