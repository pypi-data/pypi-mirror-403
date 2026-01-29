"""Task templates for common project types."""

from typing import Any

from messirve.templates.ai_ml import AI_ML_TEMPLATES
from messirve.templates.basic import BASIC_TEMPLATES

__all__ = ["AI_ML_TEMPLATES", "BASIC_TEMPLATES", "get_all_templates", "get_template"]


def get_all_templates() -> dict[str, dict[str, Any]]:
    """Get all available templates.

    Returns:
        Dictionary mapping template names to template data.
    """
    templates: dict[str, dict[str, Any]] = {}
    templates.update(BASIC_TEMPLATES)
    templates.update(AI_ML_TEMPLATES)
    return templates


def get_template(name: str) -> dict[str, Any] | None:
    """Get a specific template by name.

    Args:
        name: Template name.

    Returns:
        Template data or None if not found.
    """
    all_templates = get_all_templates()
    return all_templates.get(name)
