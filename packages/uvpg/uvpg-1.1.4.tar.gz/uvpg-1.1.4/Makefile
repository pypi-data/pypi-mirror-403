# Makefile for uvpg development
.PHONY: help install sync lint format clean build security version

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

sync: ## Sync dependencies
	uv sync

install: ## Install the package (for testing after build)
	uv tool install dist/uvpg-*.whl

lint: ## Run linters
	uv run ruff check .

format: ## Format code
	uv run ruff format .

type: ## Run type checker
	uv run ty check .

security: ## Run security checks
	@uvx bandit -r .
# 	@uvx bandit -r . -lll

clean: ## Clean build artifacts
	@echo "✅ Clean build artifacts"
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.pyc' -delete 2>/dev/null || true
	@find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name '.ruff_cache' -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.Identifier' -delete 2>/dev/null || true
	@find . -type d -name 'dist' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name 'build' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name 'coverage' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name 'htmlcov' -exec rm -rf {} + 2>/dev/null || true

build: clean ## Build package
	uv build

version: ## Show current version
	uv version

version-patch: ## Bump patch version (0.1.0 -> 0.1.1)
	@echo "Bumping patch version..."
	@uv version --bump patch --dry-run
	@printf "Continue? [y/n] "
	@read REPLY; \
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
		uv version --bump patch; \
	else \
		echo "Aborted."; \
	fi

version-minor: ## Bump minor version (0.1.0 -> 0.2.0)
	@echo "Bumping minor version..."
	@uv version --bump minor --dry-run
	@printf "Continue? [y/n] "
	@read REPLY; \
	echo; \
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
		uv version --bump minor; \
	else \
		echo "Aborted."; \
	fi

version-major: ## Bump major version (0.1.0 -> 1.0.0)
	@echo "Bumping major version..."
	@uv version --bump major --dry-run
	@printf "Continue? [y/n] "
	@read REPLY; \
	echo; \
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
		uv version --bump major; \
	else \
		echo "Aborted."; \
	fi

check: format lint type ## Run all checks (lint, format, type)
