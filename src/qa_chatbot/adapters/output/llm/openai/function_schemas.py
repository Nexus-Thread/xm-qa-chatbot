"""Schema placeholders for LLM structured extraction."""

TEAM_ID_SCHEMA = {
    "name": "extract_team_id",
    "description": "Extract a team identifier from conversation text.",
    "parameters": {
        "type": "object",
        "properties": {"team_id": {"type": "string"}},
        "required": ["team_id"],
    },
}

TIME_WINDOW_SCHEMA = {
    "name": "extract_time_window",
    "description": "Extract the reporting month from conversation text.",
    "parameters": {
        "type": "object",
        "properties": {"month": {"type": "string"}},
        "required": ["month"],
    },
}

QA_METRICS_SCHEMA = {
    "name": "extract_qa_metrics",
    "description": "Extract QA metrics from conversation text.",
    "parameters": {
        "type": "object",
        "properties": {
            "tests_passed": {"type": "integer"},
            "tests_failed": {"type": "integer"},
            "test_coverage_percent": {"type": "number"},
            "bug_count": {"type": "integer"},
            "critical_bugs": {"type": "integer"},
            "deployment_ready": {"type": "boolean"},
        },
        "required": ["tests_passed", "tests_failed"],
    },
}

PROJECT_STATUS_SCHEMA = {
    "name": "extract_project_status",
    "description": "Extract project status updates from conversation text.",
    "parameters": {
        "type": "object",
        "properties": {
            "sprint_progress_percent": {"type": "number"},
            "blockers": {"type": "array", "items": {"type": "string"}},
            "milestones_completed": {"type": "array", "items": {"type": "string"}},
            "risks": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["sprint_progress_percent"],
    },
}

DAILY_UPDATE_SCHEMA = {
    "name": "extract_daily_update",
    "description": "Extract daily update information from conversation text.",
    "parameters": {
        "type": "object",
        "properties": {
            "completed_tasks": {"type": "array", "items": {"type": "string"}},
            "planned_tasks": {"type": "array", "items": {"type": "string"}},
            "capacity_hours": {"type": "number"},
            "issues": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["completed_tasks"],
    },
}
