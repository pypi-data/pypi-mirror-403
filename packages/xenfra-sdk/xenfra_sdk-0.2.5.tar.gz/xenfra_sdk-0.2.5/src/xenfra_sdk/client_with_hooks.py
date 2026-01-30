"""
Enhanced XenfraClient with context management and lifecycle hooks.
"""

import logging
import os
from typing import Callable

import httpx

from .exceptions import AuthenticationError, XenfraAPIError, XenfraError
from .resources.deployments import DeploymentsManager
from .resources.intelligence import IntelligenceManager
from .resources.projects import ProjectsManager

logger = logging.getLogger(__name__)


class RequestHooks:
    """Container for request lifecycle hooks."""

    def __init__(self):
        self.before_request: list[Callable] = []
        self.after_request: list[Callable] = []
        self.on_error: list[Callable] = []
        self.on_retry: list[Callable] = []

    def register_before_request(self, callback: Callable):
        """Register a callback to run before each request."""
        self.before_request.append(callback)

    def register_after_request(self, callback: Callable):
        """Register a callback to run after each request."""
        self.after_request.append(callback)

    def register_on_error(self, callback: Callable):
        """Register a callback to run on request errors."""
        self.on_error.append(callback)

    def register_on_retry(self, callback: Callable):
        """Register a callback to run on request retries."""
        self.on_retry.append(callback)


class XenfraClient:
    """
    Xenfra SDK client with context manager support and lifecycle hooks.

    Usage:
        # With context manager (recommended):
        with XenfraClient(token=token) as client:
            projects = client.projects.list()

        # Without context manager (manual cleanup):
        client = XenfraClient(token=token)
        try:
            projects = client.projects.list()
        finally:
            client.close()

        # With hooks:
        client = XenfraClient(token=token)
        client.hooks.register_before_request(lambda req: print(f"Calling {req.url}"))
        client.hooks.register_after_request(lambda req, resp: print(f"Status: {resp.status_code}"))
    """

    def __init__(
        self,
        token: str = None,
        api_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        max_retries: int = 3,
        enable_logging: bool = False,
    ):
        """
        Initialize Xenfra client.

        Args:
            token: API authentication token
            api_url: Base URL for Xenfra API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            enable_logging: Enable request/response logging
        """
        self.api_url = api_url
        self._token = token or os.getenv("XENFRA_TOKEN")
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_logging = enable_logging

        if not self._token:
            raise AuthenticationError(
                "No API token provided. Pass it to the client or set XENFRA_TOKEN."
            )

        # Initialize hooks
        self.hooks = RequestHooks()

        # Create HTTP client with retry logic
        transport = httpx.HTTPTransport(retries=max_retries)
        self._http_client = httpx.Client(
            base_url=self.api_url,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
                "User-Agent": "Xenfra-SDK/0.2.4",
            },
            timeout=timeout,
            transport=transport,
        )

        # Track if client is closed
        self._closed = False

        # Initialize resource managers
        self.projects = ProjectsManager(self)
        self.deployments = DeploymentsManager(self)
        self.intelligence = IntelligenceManager(self)

        logger.debug(f"XenfraClient initialized for {api_url}")

    def _request(self, method: str, path: str, json: dict = None) -> httpx.Response:
        """
        Internal method to handle all HTTP requests with hooks.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            json: Optional JSON body

        Returns:
            HTTP response

        Raises:
            XenfraAPIError: For API errors (4xx, 5xx)
            XenfraError: For connection/network errors
        """
        if self._closed:
            raise XenfraError("Client is closed. Create a new client or use context manager.")

        # Build request context
        request_context = {
            "method": method,
            "path": path,
            "json": json,
            "url": f"{self.api_url}{path}",
        }

        # Run before_request hooks
        for hook in self.hooks.before_request:
            try:
                hook(request_context)
            except Exception as e:
                logger.warning(f"before_request hook failed: {e}")

        # Log request if enabled
        if self.enable_logging or logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"{method} {path}")
            if json:
                logger.debug(f"Request body: {json}")

        try:
            # Make the request
            response = self._http_client.request(method, path, json=json)
            response.raise_for_status()

            # Log response if enabled
            if self.enable_logging or logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Response: {response.status_code}")

            # Run after_request hooks
            for hook in self.hooks.after_request:
                try:
                    hook(request_context, response)
                except Exception as e:
                    logger.warning(f"after_request hook failed: {e}")

            return response

        except httpx.HTTPStatusError as e:
            # API error (4xx, 5xx)
            # Safe JSON parsing with fallback
            if e.response:
                try:
                    content_type = e.response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        try:
                            error_data = e.response.json()
                            detail = error_data.get(
                                "detail",
                                e.response.text[:500] if e.response.text else "Unknown error",
                            )
                        except (ValueError, TypeError):
                            detail = e.response.text[:500] if e.response.text else "Unknown error"
                    else:
                        detail = e.response.text[:500] if e.response.text else "Unknown error"
                except Exception:
                    detail = "Unknown error"
            else:
                detail = str(e)

            # Run error hooks
            error_context = {**request_context, "error": e, "response": e.response}
            for hook in self.hooks.on_error:
                try:
                    hook(error_context)
                except Exception as hook_error:
                    logger.warning(f"on_error hook failed: {hook_error}")

            # Log error
            logger.error(
                f"{method} {path} failed: {e.response.status_code if e.response else 'unknown'}"
            )

            raise XenfraAPIError(
                status_code=e.response.status_code if e.response else 500, detail=detail
            ) from e

        except httpx.RequestError as e:
            # Connection/network error
            error_context = {**request_context, "error": e}
            for hook in self.hooks.on_error:
                try:
                    hook(error_context)
                except Exception as hook_error:
                    logger.warning(f"on_error hook failed: {hook_error}")

            logger.error(f"{method} {path} failed: {e}")
            raise XenfraError(f"HTTP request failed: {e}") from e

    def close(self):
        """Close the HTTP client and cleanup resources."""
        if not self._closed:
            logger.debug("Closing XenfraClient")
            self._http_client.close()
            self._closed = True

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.close()
        return False  # Don't suppress exceptions

    def __del__(self):
        """Destructor - cleanup if not already closed."""
        if not self._closed:
            logger.warning(
                "XenfraClient was not properly closed. Use 'with' statement or call close()."
            )
            self.close()

    def __repr__(self):
        """String representation."""
        status = "closed" if self._closed else "open"
        return f"<XenfraClient(api_url='{self.api_url}', status='{status}')>"


# Example hooks for common use cases


def logging_hook_before(request_context):
    """Example: Log all requests."""
    print(f"→ {request_context['method']} {request_context['url']}")


def logging_hook_after(request_context, response):
    """Example: Log all responses."""
    print(f"← {response.status_code} {request_context['url']}")


def error_notification_hook(error_context):
    """Example: Send notifications on errors."""
    # Could send to Sentry, DataDog, etc.
    print(f"⚠️  API Error: {error_context['url']} - {error_context['error']}")


def rate_limit_tracker_hook(request_context, response):
    """Example: Track rate limits."""
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining:
        print(f"Rate limit remaining: {remaining}")


def request_timing_hook(request_context):
    """Example: Track request timing."""
    import time

    request_context["start_time"] = time.time()


def response_timing_hook(request_context, response):
    """Example: Calculate request duration."""
    import time

    if "start_time" in request_context:
        duration = time.time() - request_context["start_time"]
        print(f"Request took {duration:.3f}s")
