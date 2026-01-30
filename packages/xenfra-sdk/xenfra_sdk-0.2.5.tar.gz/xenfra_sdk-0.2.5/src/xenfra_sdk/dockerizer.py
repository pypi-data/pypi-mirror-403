"""
Xenfra Dockerizer - Generates deployment assets as strings.

This module renders Dockerfile and docker-compose.yml templates
to strings (in-memory) so they can be written to the target droplet via SSH.
"""

from pathlib import Path
from typing import Dict, Optional
import re

from jinja2 import Environment, FileSystemLoader


def detect_python_version(file_manifest: list = None) -> str:
    """
    Detect Python version from project files.
    
    Checks in order:
    1. .python-version file (e.g., "3.13")
    2. pyproject.toml requires-python field (e.g., ">=3.13")
    
    Args:
        file_manifest: List of file info dicts with 'path' and optionally 'content'
                       If None, uses 3.11 as default.
    
    Returns:
        Docker image version string (e.g., "python:3.13-slim")
    """
    default_version = "python:3.11-slim"
    
    if not file_manifest:
        return default_version
    
    # Build a lookup dict for quick access
    file_lookup = {f.get('path', ''): f for f in file_manifest}
    
    # Option 1: Check .python-version file
    if '.python-version' in file_lookup:
        file_info = file_lookup['.python-version']
        content = file_info.get('content', '')
        if content:
            # Parse version like "3.13" or "3.13.1"
            version = content.strip().split('\n')[0].strip()
            if version:
                # Extract major.minor (e.g., "3.13" from "3.13.1")
                match = re.match(r'(\d+\.\d+)', version)
                if match:
                    return f"python:{match.group(1)}-slim"
    
    # Option 2: Check pyproject.toml requires-python
    if 'pyproject.toml' in file_lookup:
        file_info = file_lookup['pyproject.toml']
        content = file_info.get('content', '')
        if content:
            # Parse requires-python = ">=3.13" or "^3.13"
            match = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                version_spec = match.group(1)
                # Extract version number (e.g., "3.13" from ">=3.13")
                version_match = re.search(r'(\d+\.\d+)', version_spec)
                if version_match:
                    return f"python:{version_match.group(1)}-slim"
    
    return default_version


def render_deployment_assets(context: dict) -> Dict[str, str]:
    """
    Renders deployment assets (Dockerfile, docker-compose.yml) using Jinja2 templates.
    
    IMPORTANT: This function returns strings, NOT files. The caller is responsible
    for writing these to the correct location (e.g., via SSH to a remote droplet).

    Args:
        context: A dictionary containing information for rendering templates.
                 Required keys:
                   - framework: str (fastapi, flask, django)
                   - port: int (default 8000)
                 Optional keys:
                   - command: str (start command, auto-generated if not provided)
                   - database: str (postgres, mysql, etc.)
                   - package_manager: str (pip, uv)
                   - dependency_file: str (requirements.txt, pyproject.toml)
                   - python_version: str (default python:3.11-slim)

    Returns:
        Dict with keys "Dockerfile" and "docker-compose.yml", values are rendered content strings.
        Returns empty dict if no framework is provided.
    """
    # Path to the templates directory
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))

    # Get framework from context (MUST be provided by caller, no auto-detection)
    framework = context.get("framework")
    if not framework:
        # Framework is required - caller should have validated this
        return {}

    # Get port with default
    port = context.get("port") or 8000

    # Generate default command based on framework if not provided
    command = context.get("command")
    if not command:
        if framework == "fastapi":
            command = f"uvicorn main:app --host 0.0.0.0 --port {port}"
        elif framework == "flask":
            command = f"gunicorn app:app -b 0.0.0.0:{port}"
        elif framework == "django":
            command = f"gunicorn app.wsgi:application --bind 0.0.0.0:{port}"
        else:
            command = f"uvicorn main:app --host 0.0.0.0 --port {port}"

    # Build render context with all values
    render_context = {
        "framework": framework,
        "port": port,
        "command": command,
        "database": context.get("database"),
        "package_manager": context.get("package_manager", "pip"),
        "dependency_file": context.get("dependency_file", "requirements.txt"),
        "python_version": context.get("python_version", "python:3.11-slim"),
        "missing_deps": context.get("missing_deps", []),
        # Pass through any additional context
        **context,
    }

    result = {}

    # --- 1. Render Dockerfile ---
    dockerfile_template = env.get_template("Dockerfile.j2")
    result["Dockerfile"] = dockerfile_template.render(render_context)

    # --- 2. Render docker-compose.yml ---
    compose_template = env.get_template("docker-compose.yml.j2")
    result["docker-compose.yml"] = compose_template.render(render_context)

    return result


# Keep detect_framework for potential local CLI use (not used in remote deployment)
def detect_framework(path: str = ".") -> tuple:
    """
    Scans common Python project structures to guess the framework and entrypoint.
    
    NOTE: This is only useful when running LOCALLY on the user's machine.
    It should NOT be called when the engine runs on a remote server.
    
    Returns: (framework_name, default_port, start_command) or (None, None, None)
    """
    project_root = Path(path).resolve()

    # Check for Django first (common pattern: manage.py in root)
    if (project_root / "manage.py").is_file():
        project_name = project_root.name
        return "django", 8000, f"gunicorn {project_name}.wsgi:application --bind 0.0.0.0:8000"

    candidate_files = []
    
    # Check directly in project root
    for name in ["main.py", "app.py"]:
        if (project_root / name).is_file():
            candidate_files.append(project_root / name)

    # Check in src/*/ (standard package layout)
    for src_dir in project_root.glob("src/*"):
        if src_dir.is_dir():
            for name in ["main.py", "app.py"]:
                if (src_dir / name).is_file():
                    candidate_files.append(src_dir / name)

    import os
    for file_path in candidate_files:
        try:
            with open(file_path, "r") as f:
                content = f.read()
        except Exception:
            continue
            
        try:
            module_name = str(file_path.relative_to(project_root)).replace(os.sep, '.')[:-3]
            if module_name.startswith("src."):
                module_name = module_name[4:]
        except ValueError:
            module_name = file_path.stem

        if "FastAPI" in content:
            return "fastapi", 8000, f"uvicorn {module_name}:app --host 0.0.0.0 --port 8000"
        
        if "Flask" in content:
            return "flask", 5000, f"gunicorn {module_name}:app -b 0.0.0.0:5000"
    
    return None, None, None
