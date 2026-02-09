"""Submit test coverage data via Gradio Client API."""

from __future__ import annotations

from gradio_client import Client

# ruff: noqa: T201, RUF059, PLR0915


def submit_test_coverage_data() -> None:
    """Submit test coverage data through the Gradio chatbot API."""
    # Connect to the running Gradio server
    client = Client("http://localhost:7860")

    print("🔌 Connected to Gradio app at http://localhost:7860")
    print("\n📋 Available API endpoints:")
    print(client.view_api())
    print("\n" + "=" * 60)
    print("SUBMITTING DATA:")
    print("  Project: Client Trading")
    print("  Period: 2026-01")
    print("  Manual Total: 1000")
    print("  Manual Created: 100")
    print("  Manual Updated: 120")
    print("  Automated Total: 500")
    print("  Automated Created: 50")
    print("  Automated Updated: 30")
    print("=" * 60 + "\n")

    # Step 1: Initialize session
    print("Step 1: Initializing session...")
    history = client.predict(api_name="/initialize")
    print("✅ Session initialized with welcome message\n")

    # Step 2: Submit project name
    print("Step 2: Submitting project 'Client Trading'...")
    cleared_input, history = client.predict("Client Trading", history, api_name="/respond")

    if history:
        last_msg = history[-1]["content"]
        # Handle both string and list content formats
        if isinstance(last_msg, list):
            last_msg = last_msg[0].get("text", "") if last_msg else ""
        print(f"✅ Response: {last_msg[:100]}...\n")

    # Step 3: Submit reporting period
    print("Step 3: Submitting period '2026-01'...")
    cleared_input, history = client.predict("2026-01", history, api_name="/respond")

    last_msg = history[-1]["content"]
    if isinstance(last_msg, list):
        last_msg = last_msg[0].get("text", "") if last_msg else ""
    print(f"✅ Response: {last_msg[:100]}...\n")

    # Step 4: Submit test coverage data
    print("Step 4: Submitting test coverage data...")
    coverage_message = (
        "Manual total: 1000\n"
        "Manual created last month: 100\n"
        "Manual updated last month: 120\n"
        "Automated total: 500\n"
        "Automated created last month: 50\n"
        "Automated updated last month: 30"
    )
    cleared_input, history = client.predict(coverage_message, history, api_name="/respond")

    last_msg = history[-1]["content"]
    if isinstance(last_msg, list):
        last_msg = last_msg[0].get("text", "") if last_msg else ""
    print(f"✅ Response: {last_msg[:150]}...\n")

    # Step 5: Confirm submission
    print("Step 5: Confirming submission...")
    cleared_input, history = client.predict("yes", history, api_name="/respond")

    final_response = history[-1]["content"] if history else "No response"
    if isinstance(final_response, list):
        final_response = final_response[0].get("text", "") if final_response else ""
    print(f"✅ Final Response: {final_response}\n")

    print("=" * 60)
    if "saved" in final_response.lower():
        print("✅ SUCCESS: Data submitted and saved!")
    else:
        print("⚠️  WARNING: Submission may not have completed. Check the response above.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        submit_test_coverage_data()
    except Exception as e:  # noqa: BLE001
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure the Gradio app is running at http://localhost:7860")
        print("Start it with: python -m qa_chatbot.main")
