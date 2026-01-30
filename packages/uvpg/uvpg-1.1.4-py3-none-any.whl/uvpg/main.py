#!/usr/bin/env python3
"""
uvpg - UV Project generator based on monorepo template with uv workspaces.

Usage:
    uvpg my-project
    uvpg my-project --package my-lib
    uvpg my-project -p lib1 -p lib2
"""

import argparse
import platform
import re
import subprocess
import sys
from datetime import UTC, datetime

# ============================================================================
# Configuration
# ============================================================================
from importlib.metadata import version
from pathlib import Path

from uvpg.templates import (
    TEMPLATE_COMPOSE,
    TEMPLATE_DOCKERFILE,
    TEMPLATE_DOCKERIGNORE,
    TEMPLATE_GITIGNORE,
    TEMPLATE_LICENSE_MIT,
    TEMPLATE_MAIN_APP,
    TEMPLATE_MAKEFILE,
    TEMPLATE_PACKAGE_MAIN,
    TEMPLATE_PYPROJECT_PACKAGE,
    TEMPLATE_PYPROJECT_ROOT,
    TEMPLATE_README,
    TEMPLATE_VSCODE_EXTENSIONS,
    TEMPLATE_VSCODE_SETTINGS,
)

VERSION: str = version(distribution_name="uvpg")
AUTHORS_NAME = "John Doe"
AUTHORS_EMAIL = "john@example.com"
PYTHON_VERSION_DEFAULT = f"{sys.version_info.major}.{sys.version_info.minor}"


# ============================================================================
# Functions
# ============================================================================


def run_command(cmd: list[str], cwd: Path | None = None) -> bool:
    """Execute command and return success status."""
    try:
        subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)  # noqa: S603
    except subprocess.CalledProcessError as e:
        print(f"Error running {' '.join(cmd)}: {e.stderr.decode()}")
        return False
    else:
        return True


def create_package(root: Path, name: str, python_version: str = PYTHON_VERSION_DEFAULT) -> bool:
    """Create a package inside packages/."""
    package_name = name.replace("-", "_")
    package_dir = root / "packages" / package_name

    if package_dir.exists():
        print(f"Package '{name}' already exists!")
        return False

    print(f"Creating package: {name}")

    # Package structure
    src_dir = package_dir / "src" / package_name
    src_dir.mkdir(parents=True)
    (package_dir / "tests").mkdir()

    # Files
    (package_dir / "pyproject.toml").write_text(
        TEMPLATE_PYPROJECT_PACKAGE.format(
            name=name,
            package_name=package_name,
            python_version=python_version,
        ),
        encoding="utf-8",
    )
    (src_dir / "__init__.py").touch()
    (src_dir / "main.py").write_text(TEMPLATE_PACKAGE_MAIN.format(name=name), encoding="utf-8")
    (package_dir / "tests" / "__init__.py").touch()

    # Register package in root pyproject.toml
    register_package_in_root(root, package_name)

    return True


def register_package_in_root(root: Path, package_name: str) -> None:
    """Register a package in root pyproject.toml dependencies and sources."""
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        return

    content = pyproject_path.read_text(encoding="utf-8")

    # Add to dependencies = []
    if "dependencies = []" in content:
        content = content.replace("dependencies = []", f'dependencies = ["{package_name}"]')
    elif "dependencies = [" in content:
        # Find the dependencies line and add the package
        pattern = r"dependencies = \[([^\]]*)\]"
        match = re.search(pattern, content)
        if match:
            current_deps = match.group(1).strip()
            if current_deps and f'"{package_name}"' not in current_deps:
                new_deps = f'{current_deps}, "{package_name}"'
                content = re.sub(pattern, f"dependencies = [{new_deps}]", content)
            elif not current_deps:
                content = re.sub(pattern, f'dependencies = ["{package_name}"]', content)

    # Add to [tool.uv.sources]
    source_entry = f"{package_name} = {{ workspace = true }}"
    if "[tool.uv.sources]" in content and f"{package_name} = " not in content:
        content = content.replace("[tool.uv.sources]", f"[tool.uv.sources]\n{source_entry}")

    pyproject_path.write_text(content, encoding="utf-8")


def create_project(
    name: str,
    packages: list[str] | None = None,
    python_version: str = PYTHON_VERSION_DEFAULT,
    authors_name: str = AUTHORS_NAME,
    authors_email: str = AUTHORS_EMAIL,
) -> bool:
    """Create complete project with monorepo structure."""
    root = Path(name).resolve()

    # If directory exists and has pyproject.toml, only add packages
    if root.exists() and (root / "pyproject.toml").exists():
        if packages:
            print(f"Adding packages to existing project: {root}")
            for pkg in packages:
                create_package(root, pkg, python_version)
            print("\nRun 'uv sync' to update dependencies.")
            return True
        print(f"Project already exists at {root}")
        return False

    print(f"Creating project: {name} (Python {python_version})")

    # Create directory structure
    root.mkdir(exist_ok=True)
    (root / "src" / "app").mkdir(parents=True)
    (root / "packages").mkdir()
    (root / "tests").mkdir()
    (root / ".vscode").mkdir()

    # Create root files
    py_target = f"py{python_version.replace('.', '')}"
    (root / "pyproject.toml").write_text(
        TEMPLATE_PYPROJECT_ROOT.format(
            name=name,
            python_version=python_version,
            py_target=py_target,
            authors_name=authors_name,
            authors_email=authors_email,
        ),
        encoding="utf-8",
    )
    (root / "README.md").write_text(TEMPLATE_README.format(name=name), encoding="utf-8")
    (root / "LICENSE").write_text(
        TEMPLATE_LICENSE_MIT.format(year=datetime.now(tz=UTC).year, authors_name=authors_name),
        encoding="utf-8",
    )
    (root / ".gitignore").write_text(TEMPLATE_GITIGNORE, encoding="utf-8")
    (root / ".python-version").write_text(f"{python_version}\n", encoding="utf-8")
    (root / "Dockerfile").write_text(
        TEMPLATE_DOCKERFILE.format(python_version=python_version), encoding="utf-8"
    )
    (root / ".dockerignore").write_text(TEMPLATE_DOCKERIGNORE, encoding="utf-8")
    (root / "compose.yaml").write_text(TEMPLATE_COMPOSE, encoding="utf-8")
    (root / "Makefile").write_text(TEMPLATE_MAKEFILE, encoding="utf-8")

    # Create VSCode config (detect OS for python path)
    if platform.system() == "Windows":
        python_interpreter_path = "${workspaceFolder}\\\\.venv\\\\Scripts\\\\python.exe"
    else:
        python_interpreter_path = "${workspaceFolder}/.venv/bin/python"

    (root / ".vscode" / "settings.json").write_text(
        TEMPLATE_VSCODE_SETTINGS.format(python_interpreter_path=python_interpreter_path),
        encoding="utf-8",
    )
    (root / ".vscode" / "extensions.json").write_text(TEMPLATE_VSCODE_EXTENSIONS, encoding="utf-8")

    # Create main app
    (root / "src" / "app" / "__init__.py").touch()
    (root / "src" / "app" / "main.py").write_text(TEMPLATE_MAIN_APP, encoding="utf-8")
    (root / "tests" / "__init__.py").touch()

    # Create initial packages
    if packages:
        for pkg in packages:
            create_package(root, pkg, python_version)

    # Initialize with uv
    print("Initializing with uv...")
    if not run_command(["uv", "sync"], cwd=root):
        print("Warning: failed to run 'uv sync'")

    # Initialize git
    print("Initializing git...")
    run_command(["git", "init"], cwd=root)

    print(f"\n✓ Project created at: {root}")
    print("\nNext steps:")
    print(f"  cd {name}")
    print("  uv sync")
    print("  uv run python src/app/main.py")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="uvpg",
        description="uvpg - UV Project generator for Python monorepos with uv workspaces.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""\
Examples:
  %(prog)s my-project                        # Create new project (Python {PYTHON_VERSION_DEFAULT})
  %(prog)s my-project --python {PYTHON_VERSION_DEFAULT}
  %(prog)s my-project -p utils -p core       # With initial packages
  %(prog)s my-project --author "John Doe" --email "john@example.com"
  %(prog)s . -p new-lib                      # Add package to current project
""",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )
    parser.add_argument("name", help="Project name or '.' for current directory")
    parser.add_argument(
        "-p",
        "--package",
        action="append",
        dest="packages",
        metavar="NAME",
        help="Package name to create (can be repeated)",
    )
    parser.add_argument(
        "--python",
        default=PYTHON_VERSION_DEFAULT,
        metavar="VERSION",
        help=f"Python version (default: {PYTHON_VERSION_DEFAULT})",
    )
    parser.add_argument(
        "--author",
        default=AUTHORS_NAME,
        metavar="NAME",
        help=f"Author name (default: {AUTHORS_NAME})",
    )
    parser.add_argument(
        "--email",
        default=AUTHORS_EMAIL,
        metavar="EMAIL",
        help=f"Author email (default: {AUTHORS_EMAIL})",
    )

    args = parser.parse_args()

    # Use current directory if '.'
    name = args.name
    if name == ".":
        name = str(Path.cwd())

    success = create_project(name, args.packages, args.python, args.author, args.email)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
