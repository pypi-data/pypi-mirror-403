color := $(shell tput setaf 2)
off := $(shell tput sgr0)
TARGETS = meraki_client codegen tests

.PHONY: lint
lint: format linter typecheck docs

.PHONY: test
test:
	@printf '\n\n*****************\n'
	@printf '$(color)Running tests$(off)\n'
	@printf '*****************\n'
	uv run pytest

.PHONY: test-mutating
test-mutating:
	@printf '\n\n*****************\n'
	@printf '$(color)Running mutating tests$(off)\n'
	@printf '*****************\n'
	uv run pytest -m mutating

.PHONY: typecheck
typecheck:
	@printf '\n\n*****************\n'
	@printf '$(color)Running type checker$(off)\n'
	@printf '*****************\n'
	uv run ty check ${TARGETS}

.PHONY: format
format:
	@printf '\n\n*****************\n'
	@printf '$(color)Running format$(off)\n'
	@printf '*****************\n'
	uv run ruff format --check ${TARGETS}

.PHONY: linter
linter:
	@printf '\n\n*****************\n'
	@printf '$(color)Running linter$(off)\n'
	@printf '*****************\n'
	uv run ruff check ${TARGETS}

.PHONY: generate
generate:
	@printf '\n\n*****************\n'
	@printf '$(color)Generating SDK$(off)\n'
	@printf '*****************\n'
	@uv run python codegen/main.py

.PHONY: docs
docs:
	@printf '\n\n*****************\n'
	@printf '$(color)Test building docs$(off)\n'
	@printf '*****************\n'
	uv run mkdocs build --strict

.PHONY: serve
serve:
	uv run mkdocs serve --open --livereload
