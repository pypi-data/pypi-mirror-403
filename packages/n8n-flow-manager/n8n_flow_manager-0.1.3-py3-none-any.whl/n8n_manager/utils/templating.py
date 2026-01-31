"""Templating utilities for workflow management."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

from ..exceptions import N8NValidationError
from ..models.workflow import Workflow


def render_workflow_template(
    template_content: str,
    variables: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Render a workflow JSON template with Jinja2 variables.

    Args:
        template_content: Workflow JSON as string (with Jinja2 syntax)
        variables: Dictionary of variables to inject

    Returns:
        Rendered workflow as dictionary

    Raises:
        N8NValidationError: If template rendering or JSON parsing fails
    """
    try:
        # Render template
        template = Template(template_content)
        rendered = template.render(**variables)

        # Parse as JSON
        workflow_data = json.loads(rendered)
        return workflow_data

    except json.JSONDecodeError as e:
        raise N8NValidationError(
            f"Invalid JSON after template rendering: {e}",
            details={"error": str(e)},
        )
    except Exception as e:
        raise N8NValidationError(
            f"Template rendering failed: {e}",
            details={"error": str(e)},
        )


def load_workflow_from_file(
    file_path: Union[Path, str],
    variables: Optional[Dict[str, Any]] = None,
) -> Workflow:
    """
    Load a workflow from a JSON file, optionally with Jinja2 templating.

    Args:
        file_path: Path to workflow JSON file
        variables: Optional variables for template rendering

    Returns:
        Workflow object

    Raises:
        FileNotFoundError: If file doesn't exist
        N8NValidationError: If file content is invalid
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Workflow file not found: {file_path}")

    try:
        content = file_path.read_text(encoding="utf-8")

        # If variables provided, treat as template
        if variables:
            workflow_data = render_workflow_template(content, variables)
        else:
            workflow_data = json.loads(content)

        # Validate and create Workflow object
        return Workflow(**workflow_data)

    except json.JSONDecodeError as e:
        raise N8NValidationError(
            f"Invalid JSON in workflow file: {e}",
            details={"file": str(file_path), "error": str(e)},
        )
    except Exception as e:
        raise N8NValidationError(
            f"Failed to load workflow from file: {e}",
            details={"file": str(file_path), "error": str(e)},
        )


def load_workflow_from_directory(
    directory: Union[Path, str],
    template_name: str,
    variables: Optional[Dict[str, Any]] = None,
) -> Workflow:
    """
    Load a workflow template from a directory using Jinja2 FileSystemLoader.

    This allows for template inheritance and includes.

    Args:
        directory: Directory containing templates
        template_name: Name of the template file
        variables: Variables for template rendering

    Returns:
        Workflow object

    Raises:
        TemplateNotFound: If template doesn't exist
        N8NValidationError: If template is invalid
    """
    try:
        env = Environment(loader=FileSystemLoader(str(directory)))
        template = env.get_template(template_name)

        rendered = template.render(**(variables or {}))
        workflow_data = json.loads(rendered)

        return Workflow(**workflow_data)

    except TemplateNotFound:
        raise N8NValidationError(
            f"Template not found: {template_name}",
            details={"directory": str(directory), "template": template_name},
        )
    except json.JSONDecodeError as e:
        raise N8NValidationError(
            f"Invalid JSON after template rendering: {e}",
            details={"template": template_name, "error": str(e)},
        )
    except Exception as e:
        raise N8NValidationError(
            f"Failed to load template: {e}",
            details={"template": template_name, "error": str(e)},
        )


def save_workflow_to_file(
    workflow: Workflow,
    file_path: Union[Path, str],
    indent: int = 2,
) -> None:
    """
    Save a workflow to a JSON file.

    Args:
        workflow: Workflow object to save
        file_path: Destination file path
        indent: JSON indentation level
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Use mode='json' to ensure datetime objects are serialized to ISO strings
    workflow_dict = workflow.model_dump(by_alias=True, exclude_none=True, mode="json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(workflow_dict, f, indent=indent, ensure_ascii=False)
