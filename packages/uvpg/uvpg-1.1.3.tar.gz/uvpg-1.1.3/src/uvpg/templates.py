"""Templates for uvpg project generator."""

TEMPLATE_PYPROJECT_ROOT = """\
# ============================
# UV Instructions
# ============================
# # On macOS and Linux.
# curl -LsSf https://astral.sh/uv/install.sh | sh
# #  On Windows (PowerShell).
# powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# uv --version
# # Initialized project
# uv init
# # Initialized project with python version
# uv init --python {python_version}
# # Update uv to the latest version
# uv self update
# # Resolve and install dependencies
# uv sync
# #  Upgrade all packages in the workspace
# uv sync --upgrade
# # Cache directory
# uv cache dir
# # Install python versions
# uv python install {python_version}
# # Set project python version
# uv python pin {python_version}

# ============================
# Project Metadata
# ============================
[project]
name = "{name}"
version = "1.0.0"
description = ""
readme = "README.md"
license = "MIT"
authors = [{{ name = "{authors_name}", email = "{authors_email}" }}]
requires-python = ">={python_version}"
dependencies = ["uvicorn", "fastapi"]

# ============================
# Dependency Groups
# dependencies: "ruff", "ty", "watchfiles", "pytest", "pytest-cov"
# ============================
[dependency-groups]
dev = ["ruff", "ty", "watchfiles"]

# # ============================
# # UV Configuration
# # ============================
# [tool.uv]
# link-mode = "copy"

# ============================
# Workspace Configuration
# https://docs.astral.sh/uv/concepts/projects/workspaces/#workspace-layouts
# ============================
[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]

# ============================
# Scripts Entry Points
# ============================
[project.scripts]
app = "app.main:main"

# ============================
# Build System Configuration
# ============================
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/app"]

# ============================
# Linting Configuration (Ruff)
# uv add ruff --dev
# ruff --version
# uv sync --upgrade-package ruff
# ============================
[tool.ruff]
line-length = 100
target-version = "{py_target}"
fix = true
show-fixes = true
indent-width = 4
exclude = ["venv", ".venv", "env", ".env", "node_modules", "__pycache__"]

[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "T201",   # Checks for print statements,
    "COM812", # Checks for the absence of trailing commas.
    "INP001", # Checks for packages that are missing an __init__.py file.
    "D",      # All pydocstyle (D)
    "ANN401", # Checks that function arguments are annotated with a more specific type than Any.
    "ERA001", # Checks for commented-out Python code.
    "A004",   # Shadowing Python Builtin
    "EXE001", # Shebang is present but file is not executable.
]

[tool.ruff.lint.per-file-ignores]
"**/tests/**/*.py" = ["ANN201", "S101", "ANN001"]

# ============================
# Typing Configuration (Ty)
# uv add ty --dev
# ty --version
# uv sync --upgrade-package ty
# ============================
[tool.ty.rules]
possibly-unresolved-reference = "warn"
# division-by-zero = "ignore"

# # ============================
# # Testing Configuration (pytest)
# # uv add pytest --dev
# # pytest --version
# # uv sync --upgrade-package pytest
# # ============================
# [tool.pytest.ini_options]
# addopts = "-vs --color=yes --tb=short --cov=packages --cov=src --cov-report=term-missing"
# testpaths = ["packages", "tests"]

# # ============================
# # Coverage Configuration (pytest-cov)
# # uv add pytest-cov --dev
# # pytest --version
# # uv sync --upgrade-package pytest-cov
# # ============================
# [tool.coverage.run]
# source = ["packages", "src"]
# omit = ["*/__pycache__/*", "*/tests/*"]

# [tool.coverage.report]
# exclude_lines = [
#     "pragma: no cover",           # Ignore pragma no cover ex.: def foo():  # pragma: no cover
#     "if __name__ == .__main__.:", # Ignore if __name__ == "__main__" blocks
# ]
"""

TEMPLATE_PYPROJECT_PACKAGE = """\
# ============================
# Project Metadata
# ============================
[project]
name = "{name}"
version = "1.0.0"
description = ""
requires-python = ">={python_version}"
dependencies = []

# # ============================
# # Scripts Entry Points
# # ============================
# [project.scripts]
# {package_name} = "{package_name}.main:hello"

# ============================
# Build System Configuration
# ============================
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/{package_name}"]
"""

TEMPLATE_README = """\
# {name}

## Structure

```
{name}/
├── .vscode/          # VSCode settings
├── packages/         # Internal libraries (uv workspace)
├── src/app/          # FastAPI application
├── tests/            # Test files
├── Dockerfile        # Multi-stage Docker build
├── Makefile          # Build automation
└── compose.yaml      # Docker Compose config
```

## Getting Started

### Local Development

```bash
# Install dependencies
uv sync

# Run application
uv run app

# Or run directly
uv run python src/app/main.py

# Run with auto-reload
uv run watchfiles 'python src/app/main.py'
```

### Docker

```bash
# Build and run
docker compose up --build

# Run with watch mode (auto-reload on file changes)
docker compose up --watch

# Stop
docker compose down
```

## API

Once running, access:

- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Makefile Commands

```bash
make help       # Show available commands
make sync       # Sync dependencies
make lint       # Run linters
make format     # Format code
make type       # Run type checker
make check      # Run all checks (format, lint, type)
make clean      # Clean build artifacts
make build      # Build package
```

## Add new package

```bash
uvpg . --package package-name
```

## Build

```bash
uv build
```
"""

TEMPLATE_MAIN_APP = """\
\"\"\"Main application.\"\"\"

from datetime import UTC, datetime

import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def home() -> dict[str, str | int]:
    return {"message": "Hello, world!", "now": datetime.now(tz=UTC).isoformat()}


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)  # noqa: S104


if __name__ == "__main__":
    main()
"""

TEMPLATE_PACKAGE_MAIN = """\
\"\"\"{name} main module.\"\"\"


def hello() -> str:
    return "Hello from {name}!"
"""

TEMPLATE_LICENSE_MIT = """\
MIT License

Copyright (c) {year} {authors_name}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

TEMPLATE_GITIGNORE = """\
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.eggs/

# Virtual environments
.env
.envrc
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# uv
.python-version

# Testing
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py.cover
.hypothesis/
.pytest_cache/
cover

# Ruff
.ruff_cache/

# IDEs
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
*.Identifier
"""

TEMPLATE_VSCODE_SETTINGS = """\
{{
    // VsCode general settings
    "editor.fontSize": 14,
    "window.zoomLevel": 0,
    "explorer.compactFolders": false,
    // Action Buttons settings
    "actionButtons": {{
        "defaultColor": "Lime",
        "reloadButton": "$(refresh)",
        "commands": [
            {{
                "name": "$(sync)",
                "tooltip": "Reload Windows",
                "useVsCodeApi": true,
                "command": "workbench.action.reloadWindow"
            }},
            {{
                "name": "$(trash)",
                "tooltip": "Clean Project",
                "singleInstance": true,
                "cwd": "${{workspaceFolder}}",
                "command": "make clean"
            }},
            {{
                "name": "$(beaker)",
                "tooltip": "Run Tests",
                "singleInstance": true,
                "cwd": "${{workspaceFolder}}",
                "command": "uv run pytest"
            }},
            {{
                "name": "$(check)",
                "tooltip": "Lint Project",
                "singleInstance": true,
                "cwd": "${{workspaceFolder}}",
                "command": "make check"
            }},
            {{
                "name": "$(terminal)",
                "tooltip": "Open New Terminal",
                "useVsCodeApi": true,
                "command": "workbench.action.terminal.new"
            }},
            {{
                "name": "$(package)",
                "tooltip": "UV Sync",
                "singleInstance": true,
                "cwd": "${{workspaceFolder}}",
                "command": "uv sync"
            }},
            {{
                "name": "$(build)",
                "tooltip": "UV Build",
                "singleInstance": true,
                "cwd": "${{workspaceFolder}}",
                "command": "make build"
            }},
            {{
                "name": "$(run)",
                "tooltip": "UV Run",
                "singleInstance": true,
                "cwd": "${{workspaceFolder}}",
                "command": "uv run src/app/main.py"
            }},
            {{
                "name": "$(debug-alt)",
                "tooltip": "Run Watch Files",
                "singleInstance": true,
                "cwd": "${{workspaceFolder}}",
                "command": "uv run watchfiles 'python src/app/main.py'"
            }}
        ]
    }},
    // Code Runner settings
    "code-runner.clearPreviousOutput": true,
    "code-runner.ignoreSelection": true,
    "code-runner.saveFileBeforeRun": true,
    "code-runner.runInTerminal": true,
    "code-runner.preserveFocus": false,
    "code-runner.executorMap": {{
        "python": "clear ; python -u"
    }},
    // Python settings
    "[python]": {{
        "editor.formatOnSave": true,
        "editor.tabSize": 4,
        "editor.insertSpaces": true,
        "editor.codeActionsOnSave": {{
            "source.fixAll": "explicit",
            "source.organizeImports": "explicit"
        }},
        "editor.defaultFormatter": "charliermarsh.ruff"
    }},
    "python.defaultInterpreterPath": "{python_interpreter_path}",
    "python.analysis.autoImportCompletions": true,
    "python.terminal.activateEnvInCurrentTerminal": true,
    "python.terminal.activateEnvironment": true,
    "python.languageServer": "None",
    "python.venvPath": ".venv",
    // Ty settings (https://docs.astral.sh/ty/reference/editor-settings)
    "ty.disableLanguageServices": false,
    "ty.diagnosticMode": "workspace"
}}
"""

TEMPLATE_VSCODE_EXTENSIONS = """\
{
    // Search for extensions in the Marketplace: @recommended
    "recommendations": [
        "dracula-theme.theme-dracula",
        "pkief.material-icon-theme",
        "seunlanlege.action-buttons",
        "mhutchie.git-graph",
        "ms-python.python",
        "formulahendry.code-runner",
        "tamasfe.even-better-toml",
        "charliermarsh.ruff",
        "astral-sh.ty",
        "tal7aouy.rainbow-bracket",
        "ms-vscode-remote.remote-wsl"
    ]
}
"""

TEMPLATE_DOCKERFILE = """\
################################################################################
# Global Arguments
################################################################################
ARG UID=1000
ARG GID=1000
ARG USERNAME=python
ARG PYTHON_VERSION={python_version}
ARG DEBIAN_VERSION=trixie-slim
ARG PYTHON_ENV=development

################################################################################
# Builder
################################################################################
FROM debian:${{DEBIAN_VERSION}} AS builder

ARG PYTHON_VERSION
ARG PYTHON_ENV

RUN apt-get update \\
  && apt-get install -y --no-install-recommends build-essential \\
  && apt-get clean \\
  && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \\
  UV_LINK_MODE=copy \\
  UV_PYTHON_PREFERENCE=only-managed \\
  UV_NO_DEV=1 \\
  UV_PYTHON_INSTALL_DIR=/python

RUN uv python install ${{PYTHON_VERSION}}

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \\
  --mount=type=bind,source=uv.lock,target=uv.lock \\
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \\
  --mount=type=bind,source=packages,target=packages \\
  uv sync --frozen --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \\
  mkdir -p /artifacts; \\
  if [ "${{PYTHON_ENV}}" = "production" ]; then \\
    uv sync --frozen --no-dev --no-editable; \\
    find . -maxdepth 1 -mindepth 1 ! -name '.venv' -exec rm -rf {{}} +; \\
  else \\
    uv sync --frozen --no-dev; \\
  fi

################################################################################
# Runtime
################################################################################
FROM debian:${{DEBIAN_VERSION}} AS runtime

ARG UID
ARG GID
ARG USERNAME

ENV PYTHONUNBUFFERED=1 \\
  PATH="/app/.venv/bin:${{PATH}}"

RUN groupadd --gid ${{GID}} ${{USERNAME}} \\
  && useradd --uid ${{UID}} --gid ${{USERNAME}} --shell /bin/bash --create-home ${{USERNAME}}

WORKDIR /app

COPY --from=builder --chown=${{UID}}:${{GID}} /python /python
COPY --from=builder --chown=${{UID}}:${{GID}} /app /app

USER ${{USERNAME}}

EXPOSE 8000

CMD ["app"]
"""

TEMPLATE_DOCKERIGNORE = """\
# ADDED
tests/
scripts/
docs/
Dockerfile*
*compose*.yaml
*compose*.yml
.python-version
model_cache/
TEMP.md
TMP.md
temp/
LICENSE
.ruff_cache/
# Git
.git
.gitignore
.gitattributes
# CI
.codeclimate.yml
.travis.yml
.taskcluster.yml
# Docker
docker-compose.yml
Dockerfile
.docker
.dockerignore
# Byte-compiled / optimized / DLL files
**/__pycache__/
**/*.py[cod]
# C extensions
*.so
# Distribution / packaging
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec
# Installer logs
pip-log.txt
pip-delete-this-directory.txt
# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.cache
nosetests.xml
coverage.xml
# Translations
*.mo
*.pot
# Django stuff:
*.log
# Sphinx documentation
docs/_build/
# PyBuilder
target/
# Virtual environment
.env
.venv/
venv/
# PyCharm
.idea
# Python mode for VIM
.ropeproject
**/.ropeproject
# Vim swap files
**/*.swp
# VS Code
.vscode/
"""

TEMPLATE_COMPOSE = """\
services:
  app:
    image: app
    container_name: app
    pull_policy: never
    restart: unless-stopped
    build:
      context: .
      args:
        PYTHON_ENV: development
        # PYTHON_ENV: production
      dockerfile: Dockerfile
      target: runtime
    ports:
      - "8000:8000"

    develop:
      watch:
        - action: sync+restart
          path: .
          target: /app
          ignore:
            - .venv/
            - __pycache__/
        - action: rebuild
          path: ./uv.lock
"""

TEMPLATE_MAKEFILE = """\
# Makefile for uvpg development
.PHONY: help install sync lint format clean build security version

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \\033[36m%-20s\\033[0m %s\\n", $$1, $$2}'

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
	@echo "Clean build artifacts"
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
	@uv version

version-patch: ## Bump patch version (0.1.0 -> 0.1.1)
	@echo "Bumping patch version..."
	@uv version --bump patch --dry-run
	@printf "Continue? [y/n] "
	@read REPLY; \\
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \\
		uv version --bump patch; \\
	else \\
		echo "Aborted."; \\
	fi

version-minor: ## Bump minor version (0.1.0 -> 0.2.0)
	@echo "Bumping minor version..."
	@uv version --bump minor --dry-run
	@printf "Continue? [y/n] "
	@read REPLY; \\
	echo; \\
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \\
		uv version --bump minor; \\
	else \\
		echo "Aborted."; \\
	fi

version-major: ## Bump major version (0.1.0 -> 1.0.0)
	@echo "Bumping major version..."
	@uv version --bump major --dry-run
	@printf "Continue? [y/n] "
	@read REPLY; \\
	echo; \\
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \\
		uv version --bump major; \\
	else \\
		echo "Aborted."; \\
	fi

check: format lint type ## Run all checks (lint, format, type)

dk-build: ## Build and run docker compose
	docker compose up --build

dk-watch: ## Run docker compose with watch
	docker compose up --watch

dk-up: ## Run docker compose
	docker compose up -d

dk-down: ## Stop docker compose
	docker compose down
"""  # noqa: E501
