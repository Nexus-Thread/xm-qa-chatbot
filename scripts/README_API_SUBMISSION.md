# API Data Submission Scripts

This directory contains scripts for submitting test coverage data programmatically.

## Available Scripts

### 1. `submit_data_direct.py` (Recommended)
Submits data directly to the application use cases, bypassing the Gradio UI entirely.

**Advantages:**
- ✅ Fast and reliable
- ✅ No dependency on running Gradio server
- ✅ Direct access to domain logic
- ✅ Easy to customize for different data

**Usage:**
```bash
python scripts/submit_data_direct.py
```

**Customization:**
Edit the script to change:
- Project ID (line 49): `ProjectId.from_raw("client_trading")`
- Time period (line 50): `TimeWindow.from_year_month(2026, 1)`
- Test coverage metrics (lines 52-59): All the manual/automated counts

### 2. `submit_via_api.py` (Experimental)
Attempts to submit data via the Gradio Client API.

**Limitations:**
- ⚠️ Requires running Gradio server
- ⚠️ Session state not fully supported via API
- ⚠️ LLM extraction can be unpredictable

**Usage:**
```bash
# Start the Gradio server first
python -m qa_chatbot.main

# Then in another terminal
python scripts/submit_via_api.py
```

## Example: Submitted Data

The following data was successfully submitted on 2026-02-08:

```json
{
  "project_id": "client_trading",
  "period": "2026-01",
  "test_coverage": {
    "manual_total": 1000,
    "automated_total": 0,
    "manual_created_last_month": 100,
    "manual_updated_last_month": 120,
    "automated_created_last_month": 0,
    "automated_updated_last_month": 0,
    "percentage_automation": 0.0
  }
}
```

## Verification

After running the submission, verify the data was saved:

```bash
# Check the database
sqlite3 qa_chatbot.db "SELECT project_id, month, test_coverage FROM submissions WHERE project_id = 'client_trading';"

# View the generated dashboard
python scripts/serve_dashboard.py
# Then open http://127.0.0.1:8000/overview.html
```

## Creating Custom Submissions

To submit data for a different project or period, copy `submit_data_direct.py` and modify:

1. **Project ID** - Use the project ID from the registry (see `src/qa_chatbot/domain/registries/stream_registry.py`)
2. **Time Window** - Change year and month
3. **Test Coverage** - Update all metric values

Example for a different project:

```python
project_id = ProjectId.from_raw("kyc")  # KYC project
time_window = TimeWindow.from_year_month(2026, 2)  # February 2026

test_coverage = TestCoverageMetrics(
    manual_total=500,
    automated_total=200,
    manual_created_last_month=50,
    manual_updated_last_month=30,
    automated_created_last_month=25,
    automated_updated_last_month=15,
    percentage_automation=28.57,
)
```

## Troubleshooting

### Database Schema Issues

If you encounter "no such column" errors, the database schema may be outdated:

```bash
# Backup existing database
mv qa_chatbot.db qa_chatbot.db.backup

# Let the script create a fresh database
python scripts/submit_data_direct.py
```

### LLM Extraction Errors (Gradio API)

If using `submit_via_api.py` and the LLM fails to parse data:
- Try reformatting the message to be more explicit
- Use more structured language (e.g., "Manual total: 1000" instead of "1000 manual tests")
- Consider using `submit_data_direct.py` instead
