import os

import httpx

from .exceptions import AuthenticationError, XenfraAPIError, XenfraError
from .resources.deployments import DeploymentsManager
from .resources.files import FilesManager
from .resources.intelligence import IntelligenceManager
from .resources.projects import ProjectsManager


class XenfraClient:
    def __init__(self, token: str = None, api_url: str = None):
        # Use provided URL, or fall back to env var, or default to production
        if api_url is None:
            api_url = os.getenv("XENFRA_API_URL", "https://api.xenfra.tech")

        self.api_url = api_url
        self._token = token or os.getenv("XENFRA_TOKEN")
        if not self._token:
            raise AuthenticationError(
                "No API token provided. Pass it to the client or set XENFRA_TOKEN."
            )

        self._http_client = httpx.Client(
            base_url=self.api_url,
            headers={"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"},
            timeout=30.0,  # Add a reasonable timeout
        )

        # Track if client is closed
        self._closed = False

        # Initialize resource managers
        self.projects = ProjectsManager(self)
        self.deployments = DeploymentsManager(self)
        self.intelligence = IntelligenceManager(self)
        self.files = FilesManager(self)


    def _request(self, method: str, path: str, json: dict = None) -> httpx.Response:
        """Internal method to handle all HTTP requests."""
        if self._closed:
            raise XenfraError("Client is closed. Create a new client or use context manager.")

        try:
            response = self._http_client.request(method, path, json=json)
            response.raise_for_status()  # Raise HTTPStatusError for 4xx/5xx
            return response
        except httpx.HTTPStatusError as e:
            # Convert httpx error to our custom SDK error
            # Safe JSON parsing with fallback
            try:
                content_type = e.response.headers.get("content-type", "")
                if "application/json" in content_type:
                    try:
                        error_data = e.response.json()
                        detail = error_data.get(
                            "detail", e.response.text[:500] if e.response.text else "Unknown error"
                        )
                    except (ValueError, TypeError):
                        detail = e.response.text[:500] if e.response.text else "Unknown error"
                else:
                    detail = e.response.text[:500] if e.response.text else "Unknown error"
            except Exception:
                detail = "Unknown error"
            raise XenfraAPIError(status_code=e.response.status_code, detail=detail) from e
        except httpx.RequestError as e:
            # Handle connection errors, timeouts, etc.
            raise XenfraError(f"HTTP request failed: {e}")

    def close(self):
        """Close the HTTP client and cleanup resources."""
        if not self._closed:
            self._http_client.close()
            self._closed = True

    def __enter__(self):
        """Context manager entry - allows 'with XenfraClient() as client:' usage."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.close()
        return False  # Don't suppress exceptions

    def __del__(self):
        """Destructor - cleanup if not already closed."""
        if hasattr(self, "_closed") and not self._closed:
            self.close()
