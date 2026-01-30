import os
import tomllib  # Python 3.11+
from typing import Any, Dict

import httpx

from .exceptions import XenfraError


def get_project_context():
    """
    Scans for project configuration.
    Prioritizes: pyproject.toml > requirements.txt
    Prioritizes: uv > poetry > pip
    """
    options = {}

    # 1. Check for Lockfiles (Determines the Manager)
    if os.path.exists("uv.lock"):
        options["uv"] = True
    if os.path.exists("poetry.lock"):
        options["poetry"] = True

    # 2. Extract Dependencies from pyproject.toml (Best source for names)
    if os.path.exists("pyproject.toml"):
        try:
            with open("pyproject.toml", "rb") as f:
                data = tomllib.load(f)
                deps = data.get("project", {}).get("dependencies", [])
                if deps:
                    # Clean versions if needed, or just pass them to pip/uv
                    options["toml"] = " ".join(deps)
        except Exception:
            pass

    # 3. Extract Dependencies from requirements.txt (Fallback source)
    if os.path.exists("requirements.txt"):
        try:
            with open("requirements.txt", "r") as f:
                pkgs = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                if pkgs:
                    options["pip"] = " ".join(pkgs)
        except Exception:
            pass

    # --- DECISION LOGIC ---
    context = {"type": "pip", "packages": None, "conflict": False}

    # A. Determine the Manager (Type)
    if "uv" in options:
        context["type"] = "uv"
    elif "poetry" in options:
        context["type"] = "poetry"
    else:
        context["type"] = "pip"

    # B. Determine the Packages (Content)
    # We prefer TOML because it's the modern standard usually paired with UV/Poetry
    if "toml" in options:
        context["packages"] = options["toml"]
    elif "pip" in options:
        context["packages"] = options["pip"]

    # C. Check for "True" Conflicts
    # A conflict is when we have ambiguous package sources (TOML vs Requirements)
    # AND we aren't sure which one the user wants.
    if "toml" in options and "pip" in options:
        # If we have both, we flag it so the UI can ask (or default to TOML)
        context["conflict"] = True
        context["choices"] = {
            "1": {"name": "pyproject.toml", "pkgs": options["toml"]},
            "2": {"name": "requirements.txt", "pkgs": options["pip"]},
        }

    return context


def safe_json_parse(response: httpx.Response) -> Dict[str, Any]:
    """
    Safely parse JSON from HTTP response with content-type validation and error handling.

    Args:
        response: HTTP response object

    Returns:
        Parsed JSON dictionary

    Raises:
        XenfraError: If response is not JSON or parsing fails
    """
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        # Try to get error text for better error messages
        error_text = response.text[:500] if response.text else "Unknown error"
        raise XenfraError(f"Expected JSON response, got {content_type}. Response: {error_text}")

    try:
        return response.json()
    except (ValueError, TypeError) as e:
        error_text = response.text[:500] if response.text else "Unknown error"
        raise XenfraError(f"Failed to parse JSON response: {e}. Response: {error_text}")


def safe_get_json_field(data: Dict[str, Any], field: str, default: Any = None) -> Any:
    """
    Safely get a field from JSON data with validation.

    Args:
        data: JSON dictionary
        field: Field name to retrieve
        default: Default value if field is missing

    Returns:
        Field value or default
    """
    if not isinstance(data, dict):
        raise XenfraError(f"Expected dictionary, got {type(data).__name__}")

    return data.get(field, default)
