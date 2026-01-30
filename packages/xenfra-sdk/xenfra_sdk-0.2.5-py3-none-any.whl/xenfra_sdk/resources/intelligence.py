"""
Intelligence resource manager for Xenfra SDK.
Provides AI-powered deployment diagnosis and codebase analysis.
"""

import logging

from ..exceptions import XenfraAPIError, XenfraError
from ..models import CodebaseAnalysisResponse, DiagnosisResponse
from ..utils import safe_json_parse
from .base import BaseManager

logger = logging.getLogger(__name__)


class IntelligenceManager(BaseManager):
    """
    Manager for AI-powered intelligence operations.

    Provides:
    - Deployment failure diagnosis (Zen Nod)
    - Codebase analysis for zero-config init (Zen Init)
    """

    def diagnose(
        self, 
        logs: str, 
        package_manager: str | None = None, 
        dependency_file: str | None = None,
        services: list | None = None
    ) -> DiagnosisResponse:
        """
        Diagnose deployment failure from logs using AI.

        Args:
            logs: The deployment logs to analyze
            package_manager: Optional package manager context (uv, pip, poetry, npm, etc.)
                           If provided, AI will target this manager's dependency file
            dependency_file: Optional dependency file context (pyproject.toml, requirements.txt, etc.)
                           If provided, AI will suggest patches for this file
            services: Optional list of service definitions for project structure context (Zen Mode)

        Returns:
            DiagnosisResponse with diagnosis, suggestion, and optional patch

        Raises:
            XenfraAPIError: If the API request fails
            XenfraError: If parsing the response fails
        """
        try:
            # Build request payload
            payload = {"logs": logs}
            if package_manager:
                payload["package_manager"] = package_manager
            if dependency_file:
                payload["dependency_file"] = dependency_file
            if services:
                payload["services"] = services

            response = self._client._request("POST", "/intelligence/diagnose", json=payload)

            logger.debug(f"IntelligenceManager.diagnose response: status={response.status_code}")

            # Safe JSON parsing
            data = safe_json_parse(response)
            return DiagnosisResponse(**data)
        except XenfraAPIError:
            raise
        except Exception as e:
            raise XenfraError(f"Failed to diagnose logs: {e}")

    def analyze_codebase(self, code_snippets: dict[str, str]) -> CodebaseAnalysisResponse:
        """
        Analyze codebase to detect framework, dependencies, and deployment config.

        Args:
            code_snippets: Dictionary of filename -> content
                           e.g., {"main.py": "...", "requirements.txt": "..."}

        Returns:
            CodebaseAnalysisResponse with detected configuration

        Raises:
            XenfraAPIError: If the API request fails
            XenfraError: If parsing the response fails
        """
        try:
            response = self._client._request(
                "POST", "/intelligence/analyze-codebase", json={"code_snippets": code_snippets}
            )

            logger.debug(
                f"IntelligenceManager.analyze_codebase response: status={response.status_code}"
            )

            # Safe JSON parsing
            data = safe_json_parse(response)
            return CodebaseAnalysisResponse(**data)
        except XenfraAPIError:
            raise
        except Exception as e:
            raise XenfraError(f"Failed to analyze codebase: {e}")
