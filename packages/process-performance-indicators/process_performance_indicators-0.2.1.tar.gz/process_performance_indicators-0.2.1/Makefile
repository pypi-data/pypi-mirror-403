.PHONY: lint
lint: ruff mypy	--jobs ## Apply all the linters.

.PHONY: lint-check
lint-check:  ## Check whether the codebase satisfies the linter rules.
	@echo
	@echo "Checking linter rules..."
	@echo "========================"
	@echo
	@uv run ruff check process_performance_indicators/
	@echo
	@echo "Checking static type checking..."
	@echo "============================="
	@echo
	@uv run mypy process_performance_indicators/

.PHONY: ruff
ruff: ## Apply ruff.
	@echo "Applying ruff..."
	@echo "================"
	@echo
	@uv run ruff check --fix process_performance_indicators/
	@uv run ruff format process_performance_indicators/

.PHONY: mypy
mypy: ## Apply mypy.
	@echo
	@echo "Applying mypy..."
	@echo "================="
	@echo
	@uv run mypy process_performance_indicators/


.PHONY: build-serve-docs
build-serve-docs: ## Build and serve the documentation.
	@echo
	@echo "Building and serving documentation..."
	@echo "==================================="
	@echo
	@uv run mkdocs serve