# This file makes src/xenfra_sdk a Python package.

from .client import XenfraClient
from .exceptions import AuthenticationError, XenfraAPIError, XenfraError
from .models import (
    CodebaseAnalysisResponse,
    DiagnosisResponse,
    PatchObject,
    ProjectRead,
)

# Microservices support
from .manifest import (
    ServiceDefinition,
    load_services_from_xenfra_yaml,
    is_microservices_project,
    get_deployment_mode,
    add_services_to_xenfra_yaml,
    create_services_from_detected,
)
from .detection import (
    auto_detect_services,
    detect_docker_compose_services,
    detect_pyproject_services,
)
from .orchestrator import (
    ServiceOrchestrator,
    get_orchestrator_for_project,
)

# Security
from .security_scanner import (
    scan_directory,
    scan_file_list,
    ScanResult,
    SecurityIssue,
    Severity,
)

__all__ = [
    "XenfraClient",
    "XenfraError",
    "AuthenticationError",
    "XenfraAPIError",
    "DiagnosisResponse",
    "CodebaseAnalysisResponse",
    "PatchObject",
    "ProjectRead",
    # Microservices
    "ServiceDefinition",
    "load_services_from_xenfra_yaml",
    "is_microservices_project",
    "get_deployment_mode",
    "add_services_to_xenfra_yaml",
    "create_services_from_detected",
    "auto_detect_services",
    "detect_docker_compose_services",
    "detect_pyproject_services",
    "ServiceOrchestrator",
    "get_orchestrator_for_project",
]
