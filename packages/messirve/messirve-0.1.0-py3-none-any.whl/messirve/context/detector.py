"""Project type and tech stack detection."""

import json
import re
from pathlib import Path

from messirve.context.models import ProjectContext, ProjectType, TechStack


class ProjectDetector:
    """Detects project type and technology stack."""

    def __init__(self, project_dir: Path) -> None:
        """Initialize detector.

        Args:
            project_dir: Path to the project directory.
        """
        self.project_dir = project_dir

    def detect(self) -> ProjectContext:
        """Detect project type and generate context.

        Returns:
            ProjectContext with detected information.
        """
        project_type = self._detect_project_type()
        tech_stack = self._detect_tech_stack(project_type)
        structure = self._detect_structure()
        key_files = self._detect_key_files(project_type)
        name = self._detect_name(project_type)
        description = self._detect_description()
        setup_commands = self._get_setup_commands(project_type, tech_stack)
        verify_commands = self._get_verify_commands(project_type, tech_stack)
        coding_standards = self._get_default_coding_standards(project_type)

        return ProjectContext(
            name=name,
            description=description,
            project_type=project_type,
            tech_stack=tech_stack,
            structure=structure,
            key_files=key_files,
            setup_commands=setup_commands,
            verify_commands=verify_commands,
            coding_standards=coding_standards,
        )

    def _detect_project_type(self) -> ProjectType:
        """Detect the project type based on files present."""
        # Python indicators
        if (self.project_dir / "pyproject.toml").exists():
            return ProjectType.PYTHON
        if (self.project_dir / "setup.py").exists():
            return ProjectType.PYTHON
        if (self.project_dir / "requirements.txt").exists():
            return ProjectType.PYTHON

        # Node indicators
        if (self.project_dir / "package.json").exists():
            return ProjectType.NODE

        # Go indicators
        if (self.project_dir / "go.mod").exists():
            return ProjectType.GO

        # Rust indicators
        if (self.project_dir / "Cargo.toml").exists():
            return ProjectType.RUST

        # Java indicators
        if (self.project_dir / "pom.xml").exists():
            return ProjectType.JAVA
        if (self.project_dir / "build.gradle").exists():
            return ProjectType.JAVA

        return ProjectType.UNKNOWN

    def _detect_tech_stack(self, project_type: ProjectType) -> TechStack:
        """Detect technology stack based on project type."""
        if project_type == ProjectType.PYTHON:
            return self._detect_python_stack()
        elif project_type == ProjectType.NODE:
            return self._detect_node_stack()
        elif project_type == ProjectType.GO:
            return self._detect_go_stack()
        elif project_type == ProjectType.RUST:
            return self._detect_rust_stack()
        return TechStack()

    def _detect_python_stack(self) -> TechStack:
        """Detect Python project tech stack."""
        stack = TechStack(language="Python")

        # Check pyproject.toml
        pyproject_path = self.project_dir / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text()

            # Package manager
            if "[tool.poetry]" in content:
                stack.package_manager = "Poetry"
            elif "[build-system]" in content and "hatchling" in content:
                stack.package_manager = "Hatch"
            elif "[build-system]" in content:
                stack.package_manager = "pip"

            # Python version
            version_match = re.search(r'python\s*=\s*"[\^~]?(\d+\.\d+)', content)
            if version_match:
                stack.language_version = version_match.group(1)

            # Framework detection
            if "fastapi" in content.lower():
                stack.framework = "FastAPI"
                version_match = re.search(r'fastapi\s*=\s*"[\^~]?([^"]+)"', content)
                if version_match:
                    stack.framework_version = version_match.group(1)
            elif "django" in content.lower():
                stack.framework = "Django"
            elif "flask" in content.lower():
                stack.framework = "Flask"
            elif "typer" in content.lower():
                stack.framework = "Typer (CLI)"

            # Testing
            testing = []
            if "pytest" in content:
                testing.append("pytest")
            if "pytest-asyncio" in content:
                testing.append("pytest-asyncio")
            if "pytest-cov" in content:
                testing.append("pytest-cov")
            stack.testing = testing

            # Linting
            linting = []
            if "ruff" in content:
                linting.append("ruff")
            if "mypy" in content:
                linting.append("mypy")
            if "black" in content:
                linting.append("black")
            if "flake8" in content:
                linting.append("flake8")
            stack.linting = linting

            # Database
            if "sqlalchemy" in content.lower():
                stack.database = "SQLAlchemy"
            if "asyncpg" in content.lower() or "psycopg" in content.lower():
                stack.database = "PostgreSQL"

            # Other dependencies
            other = []
            if "pydantic" in content:
                other.append("Pydantic")
            if "httpx" in content:
                other.append("httpx")
            if "aiohttp" in content:
                other.append("aiohttp")
            if "celery" in content:
                other.append("Celery")
            if "redis" in content:
                other.append("Redis")
            stack.other = other

        return stack

    def _detect_node_stack(self) -> TechStack:
        """Detect Node.js project tech stack."""
        stack = TechStack(language="JavaScript/TypeScript", package_manager="npm")

        package_json_path = self.project_dir / "package.json"
        if package_json_path.exists():
            try:
                data = json.loads(package_json_path.read_text())
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

                # TypeScript
                if "typescript" in deps:
                    stack.language = "TypeScript"

                # Framework
                if "next" in deps:
                    stack.framework = "Next.js"
                elif "react" in deps:
                    stack.framework = "React"
                elif "express" in deps:
                    stack.framework = "Express"
                elif "fastify" in deps:
                    stack.framework = "Fastify"

                # Testing
                testing = []
                if "jest" in deps:
                    testing.append("Jest")
                if "vitest" in deps:
                    testing.append("Vitest")
                if "mocha" in deps:
                    testing.append("Mocha")
                stack.testing = testing

                # Linting
                linting = []
                if "eslint" in deps:
                    linting.append("ESLint")
                if "prettier" in deps:
                    linting.append("Prettier")
                stack.linting = linting

                # Package manager
                if (self.project_dir / "pnpm-lock.yaml").exists():
                    stack.package_manager = "pnpm"
                elif (self.project_dir / "yarn.lock").exists():
                    stack.package_manager = "yarn"

            except json.JSONDecodeError:
                pass

        return stack

    def _detect_go_stack(self) -> TechStack:
        """Detect Go project tech stack."""
        stack = TechStack(language="Go", package_manager="go modules")

        go_mod_path = self.project_dir / "go.mod"
        if go_mod_path.exists():
            content = go_mod_path.read_text()

            # Go version
            version_match = re.search(r"go\s+(\d+\.\d+)", content)
            if version_match:
                stack.language_version = version_match.group(1)

            # Framework detection
            if "gin-gonic" in content:
                stack.framework = "Gin"
            elif "echo" in content:
                stack.framework = "Echo"
            elif "fiber" in content:
                stack.framework = "Fiber"

        return stack

    def _detect_rust_stack(self) -> TechStack:
        """Detect Rust project tech stack."""
        stack = TechStack(language="Rust", package_manager="Cargo")

        cargo_toml_path = self.project_dir / "Cargo.toml"
        if cargo_toml_path.exists():
            content = cargo_toml_path.read_text()

            # Framework detection
            if "actix-web" in content:
                stack.framework = "Actix Web"
            elif "axum" in content:
                stack.framework = "Axum"
            elif "rocket" in content:
                stack.framework = "Rocket"

        return stack

    def _detect_structure(self) -> dict[str, str]:
        """Detect project directory structure."""
        structure: dict[str, str] = {}

        # Common directories to look for
        common_dirs = {
            "src": "Source code",
            "lib": "Library code",
            "app": "Application code",
            "tests": "Test files",
            "test": "Test files",
            "docs": "Documentation",
            "config": "Configuration files",
            "scripts": "Utility scripts",
            "migrations": "Database migrations",
            "alembic": "Alembic migrations",
            "static": "Static files",
            "templates": "Template files",
            "public": "Public assets",
            "api": "API routes",
            "models": "Data models",
            "services": "Business logic",
            "utils": "Utility functions",
            "helpers": "Helper functions",
            "middlewares": "Middleware",
            "handlers": "Request handlers",
            "controllers": "Controllers",
            "views": "Views",
            "components": "UI components",
        }

        for dir_name, description in common_dirs.items():
            dir_path = self.project_dir / dir_name
            if dir_path.is_dir():
                structure[f"{dir_name}/"] = description

            # Also check in src/
            src_dir_path = self.project_dir / "src" / dir_name
            if src_dir_path.is_dir():
                structure[f"src/{dir_name}/"] = description

        return structure

    def _detect_key_files(self, project_type: ProjectType) -> dict[str, str]:
        """Detect key files based on project type."""
        key_files: dict[str, str] = {}

        # Common files
        common_files = {
            "README.md": "Project documentation",
            "LICENSE": "License file",
            ".gitignore": "Git ignore patterns",
            ".env.example": "Environment variables template",
            "Makefile": "Build automation",
            "docker-compose.yml": "Docker services",
            "Dockerfile": "Container definition",
        }

        for file_name, description in common_files.items():
            if (self.project_dir / file_name).exists():
                key_files[file_name] = description

        # Python specific
        if project_type == ProjectType.PYTHON:
            python_files = {
                "pyproject.toml": "Project configuration",
                "setup.py": "Package setup",
                "requirements.txt": "Dependencies",
                "alembic.ini": "Alembic configuration",
                "pytest.ini": "Pytest configuration",
                "mypy.ini": "Mypy configuration",
                ".ruff.toml": "Ruff configuration",
            }
            for file_name, description in python_files.items():
                if (self.project_dir / file_name).exists():
                    key_files[file_name] = description

            # Look for main entry points
            for entry in ["src/main.py", "main.py", "app.py", "src/app.py"]:
                if (self.project_dir / entry).exists():
                    key_files[entry] = "Application entry point"
                    break

        # Node specific
        elif project_type == ProjectType.NODE:
            node_files = {
                "package.json": "Package configuration",
                "tsconfig.json": "TypeScript configuration",
                ".eslintrc.js": "ESLint configuration",
                "next.config.js": "Next.js configuration",
            }
            for file_name, description in node_files.items():
                if (self.project_dir / file_name).exists():
                    key_files[file_name] = description

        return key_files

    def _detect_name(self, project_type: ProjectType) -> str:
        """Detect project name."""
        # Try pyproject.toml
        if project_type == ProjectType.PYTHON:
            pyproject_path = self.project_dir / "pyproject.toml"
            if pyproject_path.exists():
                content = pyproject_path.read_text()
                match = re.search(r'name\s*=\s*"([^"]+)"', content)
                if match:
                    return match.group(1)

        # Try package.json
        if project_type == ProjectType.NODE:
            package_json_path = self.project_dir / "package.json"
            if package_json_path.exists():
                try:
                    data = json.loads(package_json_path.read_text())
                    if "name" in data:
                        return str(data["name"])
                except json.JSONDecodeError:
                    pass

        # Fall back to directory name
        return self.project_dir.name

    def _detect_description(self) -> str:
        """Detect project description from README."""
        readme_path = self.project_dir / "README.md"
        if readme_path.exists():
            content = readme_path.read_text()
            # Get first paragraph after title
            lines = content.split("\n")
            in_description = False
            description_lines = []

            for line in lines:
                if line.startswith("# "):
                    in_description = True
                    continue
                if in_description:
                    if line.startswith("#") or line.startswith("```"):
                        break
                    if line.strip():
                        description_lines.append(line.strip())
                    elif description_lines:
                        break

            if description_lines:
                return " ".join(description_lines)[:500]

        return ""

    def _get_setup_commands(self, project_type: ProjectType, tech_stack: TechStack) -> list[str]:
        """Get setup commands based on project type."""
        commands: list[str] = []

        if project_type == ProjectType.PYTHON:
            if tech_stack.package_manager == "Poetry":
                commands.append("poetry install")
            else:
                commands.append("pip install -r requirements.txt")

            # Check for .env.example
            if (self.project_dir / ".env.example").exists():
                commands.append("cp .env.example .env")

            # Check for alembic
            if (self.project_dir / "alembic.ini").exists():
                commands.append("alembic upgrade head")

        elif project_type == ProjectType.NODE:
            if tech_stack.package_manager == "pnpm":
                commands.append("pnpm install")
            elif tech_stack.package_manager == "yarn":
                commands.append("yarn install")
            else:
                commands.append("npm install")

        elif project_type == ProjectType.GO:
            commands.append("go mod download")

        elif project_type == ProjectType.RUST:
            commands.append("cargo build")

        return commands

    def _get_verify_commands(self, project_type: ProjectType, tech_stack: TechStack) -> list[str]:
        """Get verification commands based on project type."""
        commands: list[str] = []

        if project_type == ProjectType.PYTHON:
            # Testing
            if "pytest" in tech_stack.testing:
                commands.append("pytest --tb=short -q")

            # Linting
            if "ruff" in tech_stack.linting:
                commands.append("ruff check src/ --fix")
            if "mypy" in tech_stack.linting:
                commands.append("mypy src/")

        elif project_type == ProjectType.NODE:
            commands.append("npm test")
            if "ESLint" in tech_stack.linting:
                commands.append("npm run lint")

        elif project_type == ProjectType.GO:
            commands.append("go test ./...")

        elif project_type == ProjectType.RUST:
            commands.append("cargo test")

        return commands

    def _get_default_coding_standards(self, project_type: ProjectType) -> list[str]:
        """Get default coding standards based on project type."""
        if project_type == ProjectType.PYTHON:
            return [
                "Use type hints for all function parameters and return values",
                "Add docstrings to all public functions and classes",
                "Follow PEP 8 naming conventions",
                "Keep functions under 50 lines",
                "Prefer composition over inheritance",
                "Use async/await for I/O operations where appropriate",
            ]
        elif project_type == ProjectType.NODE:
            return [
                "Use TypeScript strict mode",
                "Add JSDoc comments to public functions",
                "Use ESLint and Prettier for formatting",
                "Prefer functional components in React",
                "Use async/await over callbacks",
            ]
        elif project_type == ProjectType.GO:
            return [
                "Follow Go naming conventions",
                "Add godoc comments to exported functions",
                "Handle all errors explicitly",
                "Use interfaces for dependencies",
                "Run go fmt before committing",
            ]
        return []
