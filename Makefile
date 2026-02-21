.PHONY: format lint typecheck test quality-gate audit-deps serve

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

audit-deps:
	mkdir -p .tmp
	uv export --frozen --no-hashes --format requirements-txt -o .tmp/requirements-audit.txt
	uvx --from pip-audit pip-audit -r .tmp/requirements-audit.txt

serve:
	python scripts/serve_dashboard.py
