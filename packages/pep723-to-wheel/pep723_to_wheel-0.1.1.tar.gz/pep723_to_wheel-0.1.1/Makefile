.PHONY: test typecheck ruff all-tests

test:
	uv run pytest --cov=pep723_to_wheel --cov-report=term-missing --cov-report=xml

typecheck:
	uv run ty check

ruff:
	uv run ruff check .

all-tests: test typecheck ruff
