.PHONY: format lint typecheck test quality-gate serve

format:
	ruff format .
	ruff check . --fix

lint:
	ruff check .

typecheck:
	mypy src/ tests/

test:
	pytest tests/

quality-gate: format lint typecheck test

serve:
	python scripts/serve_dashboard.py
