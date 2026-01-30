"""
Xenfra Microservices Manifest - Schema and Parser for xenfra.yaml services array.

This module defines the Pydantic models for microservices deployment configuration.
For microservices projects, xenfra.yaml includes a 'services' array:

  project_name: my-app
  framework: fastapi
  services:   # <-- This makes it a microservices project
    - name: users
      port: 8001
    - name: orders
      port: 8002
"""

from pathlib import Path
from typing import List, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class ServiceDefinition(BaseModel):
    """
    Single service definition in a microservices project.
    
    Example in xenfra.yaml:
        services:
          - name: users
            path: ./services/users
            port: 8001
            framework: fastapi
            entrypoint: users_api.main:app
    """
    
    name: str = Field(..., min_length=1, max_length=50, description="Service name (unique)")
    path: str = Field(default=".", description="Relative path to service directory")
    port: int = Field(..., ge=1, le=65535, description="Service port")
    framework: Literal["fastapi", "flask", "django", "other"] = Field(
        default="fastapi", description="Web framework"
    )
    entrypoint: Optional[str] = Field(
        default=None, description="Application entrypoint (e.g., 'users_api.main:app')"
    )
    command: Optional[str] = Field(
        default=None, description="Custom start command"
    )
    env: Optional[dict] = Field(
        default_factory=dict, description="Environment variables"
    )
    package_manager: Optional[str] = Field(
        default="pip", description="Package manager (pip, uv)"
    )
    dependency_file: Optional[str] = Field(
        default="requirements.txt", description="Dependency file"
    )
    missing_deps: List[str] = Field(
        default_factory=list, description="Proactively detected missing dependencies"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is URL-safe (alphanumeric + hyphens)."""
        import re
        if not re.match(r'^[a-z][a-z0-9-]*$', v.lower()):
            raise ValueError(
                f"Service name '{v}' must start with a letter and contain only "
                "lowercase letters, numbers, and hyphens"
            )
        return v.lower()


def validate_unique_names(services: List[ServiceDefinition]) -> List[ServiceDefinition]:
    """Ensure all service names are unique."""
    names = [s.name for s in services]
    if len(names) != len(set(names)):
        duplicates = [n for n in names if names.count(n) > 1]
        raise ValueError(f"Duplicate service names: {set(duplicates)}")
    return services


def validate_unique_ports(services: List[ServiceDefinition]) -> List[ServiceDefinition]:
    """Ensure all service ports are unique."""
    ports = [s.port for s in services]
    if len(ports) != len(set(ports)):
        duplicates = [p for p in ports if ports.count(p) > 1]
        raise ValueError(f"Duplicate service ports: {set(duplicates)}")
    return services


def load_services_from_xenfra_yaml(project_path: str = ".") -> Optional[List[ServiceDefinition]]:
    """
    Load services array from xenfra.yaml if present.
    
    Args:
        project_path: Path to the project directory (default: current directory)
    
    Returns:
        List of ServiceDefinition if 'services' key found, None otherwise
    
    Raises:
        ValueError: If services array is invalid
    """
    yaml_path = Path(project_path) / "xenfra.yaml"
    
    if not yaml_path.exists():
        return None
    
    with open(yaml_path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError:
            return None
    
    if not data or "services" not in data:
        return None
    
    services_data = data.get("services", [])
    if not services_data or not isinstance(services_data, list):
        return None
    
    try:
        services = [ServiceDefinition(**svc) for svc in services_data]
        validate_unique_names(services)
        validate_unique_ports(services)
        return services
    except Exception as e:
        raise ValueError(f"Invalid services configuration in xenfra.yaml: {e}")


def is_microservices_project(project_path: str = ".") -> bool:
    """
    Check if project has multiple services defined in xenfra.yaml.
    
    Returns:
        True if xenfra.yaml has 'services' array with 2+ services
    """
    try:
        services = load_services_from_xenfra_yaml(project_path)
        return services is not None and len(services) > 1
    except ValueError:
        return False


def get_deployment_mode(project_path: str = ".") -> Optional[str]:
    """
    Get deployment mode from xenfra.yaml if specified.
    
    Returns:
        "single-droplet", "multi-droplet", or None if not specified
    """
    yaml_path = Path(project_path) / "xenfra.yaml"
    
    if not yaml_path.exists():
        return None
    
    with open(yaml_path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError:
            return None
    
    return data.get("mode") if data else None


def add_services_to_xenfra_yaml(
    project_path: str,
    services: List[dict],
    mode: str = "single-droplet"
) -> Path:
    """
    Add or update services array in existing xenfra.yaml.
    
    Args:
        project_path: Path to the project directory
        services: List of service dictionaries from auto-detection
        mode: Deployment mode
    
    Returns:
        Path to the updated xenfra.yaml
    """
    yaml_path = Path(project_path) / "xenfra.yaml"
    
    # Load existing xenfra.yaml if present
    existing_data = {}
    if yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            existing_data = yaml.safe_load(f) or {}
    
    # Add services array
    existing_data["services"] = services
    existing_data["mode"] = mode
    
    # Write back
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(existing_data, f, default_flow_style=False, sort_keys=False)
    
    return yaml_path


def create_services_from_detected(services: List[dict]) -> List[ServiceDefinition]:
    """
    Create ServiceDefinition list from detected services.
    
    Args:
        services: List of service dictionaries from auto-detection
    
    Returns:
        List of ServiceDefinition instances
    """
    return [ServiceDefinition(**svc) for svc in services]
