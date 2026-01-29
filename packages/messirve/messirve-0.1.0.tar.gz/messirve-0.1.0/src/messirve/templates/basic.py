"""Basic task templates."""

from typing import Any

BASIC_TEMPLATES: dict[str, dict[str, Any]] = {
    "example": {
        "name": "Basic Example",
        "description": "A simple example task to get started with Messirve",
        "tasks": [
            {
                "id": "TASK-001",
                "title": "Create Hello World Script",
                "description": "Create a simple Python script that prints 'Hello, World!'",
                "context": "This is a starter project with no existing code.",
                "acceptance_criteria": [
                    "Script runs without errors",
                    "Output contains 'Hello, World!'",
                ],
                "flavor": "poc",
            }
        ],
    },
    "api-endpoint": {
        "name": "REST API Endpoint",
        "description": "Create a REST API endpoint with FastAPI",
        "tasks": [
            {
                "id": "API-001",
                "title": "Setup FastAPI Project",
                "description": "Initialize a FastAPI project with basic structure",
                "context": "New project, need to set up from scratch",
                "acceptance_criteria": [
                    "FastAPI app runs on localhost:8000",
                    "Health check endpoint returns 200",
                    "OpenAPI docs available at /docs",
                ],
                "flavor": "production-ready",
            },
            {
                "id": "API-002",
                "title": "Create CRUD Endpoints",
                "description": "Implement CRUD operations for a resource",
                "context": "FastAPI project already set up",
                "acceptance_criteria": [
                    "GET /items returns list of items",
                    "POST /items creates new item",
                    "GET /items/{id} returns single item",
                    "PUT /items/{id} updates item",
                    "DELETE /items/{id} removes item",
                ],
                "depends_on": ["API-001"],
                "flavor": "production-ready",
            },
        ],
    },
    "cli-tool": {
        "name": "CLI Tool",
        "description": "Create a command-line tool with Typer",
        "tasks": [
            {
                "id": "CLI-001",
                "title": "Setup CLI Structure",
                "description": "Create CLI using Typer with basic commands",
                "context": "New CLI project",
                "acceptance_criteria": [
                    "CLI runs with --help",
                    "Version command works",
                    "Basic command structure in place",
                ],
                "flavor": "production-ready",
            },
        ],
    },
}
