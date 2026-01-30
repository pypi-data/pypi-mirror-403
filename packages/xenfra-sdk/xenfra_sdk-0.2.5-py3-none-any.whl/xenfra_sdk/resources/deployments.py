import json
import logging
from typing import Iterator

# Import Deployment model when it's defined in models.py
# from ..models import Deployment
from ..exceptions import XenfraAPIError, XenfraError  # Add XenfraError
from ..utils import safe_get_json_field, safe_json_parse
from .base import BaseManager

logger = logging.getLogger(__name__)


class DeploymentsManager(BaseManager):
    def create(self, project_name: str, git_repo: str, branch: str, framework: str, region: str = None, size_slug: str = None, is_dockerized: bool = True, port: int = None, command: str = None, entrypoint: str = None, database: str = None, package_manager: str = None, dependency_file: str = None, file_manifest: list = None, cleanup_on_failure: bool = False, services: list = None, mode: str = None) -> dict:
        """Creates a new deployment."""
        try:
            payload = {
                "project_name": project_name,
                "git_repo": git_repo,
                "branch": branch,
                "framework": framework,
            }
            if region:
                payload["region"] = region
            if size_slug:
                payload["size_slug"] = size_slug
            if is_dockerized is not None:
                payload["is_dockerized"] = is_dockerized
            if port:
                payload["port"] = port
            if command:
                payload["command"] = command
            if entrypoint:
                payload["entrypoint"] = entrypoint
            if database:
                payload["database"] = database
            if package_manager:
                payload["package_manager"] = package_manager
            if dependency_file:
                payload["dependency_file"] = dependency_file
            if file_manifest:
                payload["file_manifest"] = file_manifest
            if cleanup_on_failure:
                payload["cleanup_on_failure"] = True
            # Microservices support
            if services:
                payload["services"] = services
            if mode:
                payload["mode"] = mode
            
            response = self._client._request("POST", "/deployments", json=payload)
            # Safe JSON parsing
            return safe_json_parse(response)
        except XenfraAPIError:
            raise
        except Exception as e:
            raise XenfraError(f"Failed to create deployment: {e}")

    def get_status(self, deployment_id: str) -> dict:
        """Get status for a specific deployment.

        Args:
            deployment_id: The unique identifier for the deployment.

        Returns:
            dict: Deployment status information including state, progress, etc.

        Raises:
            XenfraAPIError: If the API returns an error (e.g., 404 not found).
            XenfraError: If there's a network or parsing error.
        """
        try:
            response = self._client._request("GET", f"/deployments/{deployment_id}/status")
            logger.debug(
                f"DeploymentsManager.get_status({deployment_id}) response: {response.status_code}"
            )
            # Safe JSON parsing - _request() already handles status codes
            return safe_json_parse(response)
        except XenfraAPIError:
            raise  # Re-raise API errors
        except Exception as e:
            raise XenfraError(f"Failed to get status for deployment {deployment_id}: {e}")

    def get_logs(self, deployment_id: str) -> str:
        """Get logs for a specific deployment.

        Args:
            deployment_id: The unique identifier for the deployment.

        Returns:
            str: The deployment logs as plain text.

        Raises:
            XenfraAPIError: If the API returns an error (e.g., 404 not found).
            XenfraError: If there's a network or parsing error.
        """
        try:
            response = self._client._request("GET", f"/deployments/{deployment_id}/logs")
            logger.debug(
                f"DeploymentsManager.get_logs({deployment_id}) response: {response.status_code}"
            )

            # Safe JSON parsing with structure validation - _request() already handles status codes
            data = safe_json_parse(response)
            if not isinstance(data, dict):
                raise XenfraError(f"Expected dictionary response, got {type(data).__name__}")

            logs = safe_get_json_field(data, "logs", "")

            if not logs:
                logger.warning(f"No logs found for deployment {deployment_id}")

            return logs

        except XenfraAPIError:
            raise  # Re-raise API errors
        except Exception as e:
            raise XenfraError(f"Failed to get logs for deployment {deployment_id}: {e}")

    def create_stream(self, project_name: str, git_repo: str, branch: str, framework: str, region: str = None, size_slug: str = None, is_dockerized: bool = True, port: int = None, command: str = None, entrypoint: str = None, database: str = None, package_manager: str = None, dependency_file: str = None, file_manifest: list = None, cleanup_on_failure: bool = False, services: list = None, mode: str = None) -> Iterator[dict]:
        """
        Creates a new deployment with real-time SSE log streaming.

        Yields SSE events as dictionaries with 'event' and 'data' keys.

        Args:
            project_name: Name of the project
            git_repo: Git repository URL (optional if file_manifest provided)
            branch: Git branch to deploy
            framework: Framework type (fastapi, flask, django)
            region: DigitalOcean region (optional)
            size_slug: DigitalOcean droplet size (optional)
            is_dockerized: Whether to use Docker (optional)
            port: Application port (optional, default 8000)
            command: Start command (optional, auto-detected if not provided)
            entrypoint: Application entrypoint (optional, e.g. 'todo.main:app')
            database: Database type (optional, e.g. 'postgres')
            package_manager: Package manager (optional, e.g. 'pip', 'uv')
            dependency_file: Dependency file (optional, e.g. 'requirements.txt')
            file_manifest: List of files for delta upload [{path, sha, size}, ...]
            cleanup_on_failure: Automatically cleanup resources if deployment fails (optional)
            services: List of service definitions for multi-service deployments (optional)
            mode: Deployment mode - 'monolithic', 'single-droplet', or 'multi-droplet' (optional)

        Yields:
            dict: SSE events with 'event' and 'data' fields

        Example:
            for event in client.deployments.create_stream(...):
                if event['event'] == 'log':
                    print(event['data'])
                elif event['event'] == 'deployment_complete':
                    print("Done!")
        """
        payload = {
            "project_name": project_name,
            "git_repo": git_repo,
            "branch": branch,
            "framework": framework,
        }
        if region:
            payload["region"] = region
        if size_slug:
            payload["size_slug"] = size_slug
        if is_dockerized is not None:
            payload["is_dockerized"] = is_dockerized
        if port:
            payload["port"] = port
        if command:
            payload["command"] = command
        if entrypoint:
            payload["entrypoint"] = entrypoint
        if database:
            payload["database"] = database
        if package_manager:
            payload["package_manager"] = package_manager
        if dependency_file:
            payload["dependency_file"] = dependency_file
        if file_manifest:
            payload["file_manifest"] = file_manifest
        if cleanup_on_failure:
            payload["cleanup_on_failure"] = True
        # Microservices support
        if services:
            payload["services"] = services
        if mode:
            payload["mode"] = mode

        try:
            # Use httpx to stream the SSE response
            import httpx
            import os

            headers = {
                "Authorization": f"Bearer {self._client._token}",
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
            }

            # Use streaming API URL if available (bypasses Cloudflare timeout)
            # Otherwise fall back to regular API URL
            streaming_api_url = os.getenv("XENFRA_STREAMING_API_URL")
            if streaming_api_url:
                base_url = streaming_api_url
            else:
                # Local/dev/production: use regular API URL
                base_url = self._client.api_url

            url = f"{base_url}/deployments/stream"

            with httpx.stream(
                "POST",
                url,
                json=payload,
                headers=headers,
                timeout=600.0,  # 10 minute timeout for deployments
            ) as response:
                # Check status before consuming stream
                if response.status_code not in [200, 201, 202]:
                    # For error responses from streaming endpoint, read via iteration
                    error_text = ""
                    try:
                        for chunk in response.iter_bytes():
                            error_text += chunk.decode('utf-8', errors='ignore')
                            if len(error_text) > 1000:  # Limit error message size
                                break
                        if not error_text:
                            error_text = "Unknown error"
                    except Exception as e:
                        error_text = f"Could not read error response: {e}"

                    raise XenfraAPIError(
                        status_code=response.status_code,
                        detail=f"Deployment failed: {error_text}"
                    )

                # Parse SSE events
                current_event = None  # Initialize before loop
                for line in response.iter_lines():
                    # No need to explicitly decode if iter_lines is used on a decoded response,
                    # but if it returns bytes, we decode it.
                    if isinstance(line, bytes):
                        line = line.decode('utf-8', errors='ignore')
                    
                    line = line.strip()
                    if not line:
                        continue

                    # SSE format: "event: eventname" or "data: eventdata"
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:"):
                        data = line[5:].strip()

                        # Get event type (default to "message" if no event line was sent)
                        event_type = current_event if current_event is not None else "message"

                        # Skip keep-alive events (used to prevent proxy timeouts)
                        if event_type == "keep-alive":
                            current_event = None
                            continue

                        try:
                            # Try to parse as JSON
                            data_parsed = json.loads(data)
                            yield {"event": event_type, "data": data_parsed}
                        except json.JSONDecodeError:
                            # If not JSON, yield as plain text
                            yield {"event": event_type, "data": data}

                        # Reset current_event after yielding
                        current_event = None

        except httpx.HTTPError as e:
            raise XenfraError(f"HTTP error during streaming deployment: {e}")
        except Exception as e:
            raise XenfraError(f"Failed to create streaming deployment: {e}")
