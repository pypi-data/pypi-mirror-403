.PHONY: install
install:
	@uv sync

.PHONY: lint
lint:
	@uv run ruff check --fix
	@uv run ruff format

.PHONY: check
check:
	@uv run ruff check

.PHONY: format
format:
	@uv run ruff format

.PHONY: test
test:
	@uv run pytest -m "not learning and not api"

.PHONY: test-current
test-current:
	@uv run pytest -m "current"

.PHONY: test-all
test-all:
	@uv run pytest -m all -n auto --dist=loadfile

.PHONY: test-min
test-min:
	@uv run pytest -m "minimum"

.PHONY: test-learning
test-learning:
	@uv run pytest -m "learning"

.PHONY: test-api
test-api:
	@uv run pytest -m "api"

.PHONY: build
build:
	@uv run python -m build

.PHONY: release
release: build
	@uv run twine upload --repository pypi dist/*
	@rm -fr dist

.PHONY: clean
clean:
	@rm -rf dist/
	@rm -rf src/*.egg-info
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
