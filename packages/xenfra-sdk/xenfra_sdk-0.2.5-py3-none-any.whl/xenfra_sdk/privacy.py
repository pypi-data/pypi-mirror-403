"""
This module contains the Privacy Scrubber for the Xenfra SDK.
Its purpose is to redact sensitive information from logs or other text
before it is sent to diagnostic endpoints, upholding privacy-first principles.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import List, Optional

import httpx  # For fetching patterns from URL

logger = logging.getLogger(__name__)

# Path to the patterns file within the SDK
_PATTERNS_FILE_PATH = Path(__file__).parent / "patterns.json"
_REDACTION_PLACEHOLDER = "[REDACTED]"
_CACHED_PATTERNS: List[re.Pattern] = []


def _load_patterns_from_file(file_path: Path) -> List[str]:
    """Loads raw regex patterns from a JSON file."""
    if not file_path.exists():
        logger.warning(
            f"Patterns file not found at {file_path}. No patterns will be used for scrubbing."
        )
        return []
    try:
        with open(file_path, "r") as f:
            config = json.load(f)
        return config.get("redaction_patterns", [])
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding patterns.json: {e}. Falling back to empty patterns.")
        return []


async def _refresh_patterns_from_url(url: str) -> Optional[List[str]]:
    """
    Fetches updated patterns from a URL asynchronously.
    """
    try:
        # Configure timeout from environment or default to 30 seconds
        timeout_seconds = float(os.getenv("XENFRA_SDK_TIMEOUT", "30.0"))
        timeout = httpx.Timeout(timeout_seconds, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()

            # Safe JSON parsing with content-type check
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                logger.warning(
                    f"Expected JSON response from {url}, got {content_type}. "
                    "Skipping pattern refresh."
                )
                return None

            try:
                config = response.json()
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to parse JSON from patterns URL {url}: {e}")
                return None

            if not isinstance(config, dict):
                logger.error(
                    f"Expected dictionary from patterns URL {url}, got {type(config).__name__}"
                )
                return None

            return config.get("redaction_patterns", [])
    except httpx.TimeoutException as e:
        logger.warning(f"Timeout fetching patterns from {url}: {e}")
        return None
    except httpx.RequestError as e:
        logger.warning(f"Error fetching patterns from {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from patterns URL {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching patterns from {url}: {e}")
        return None


async def initialize_scrubber(refresh_from_url: Optional[str] = None):
    """
    Initializes or refreshes the scrubber patterns.
    Can optionally fetch patterns from a URL. This should be called on app startup.
    """
    global _CACHED_PATTERNS
    raw_patterns = []

    if refresh_from_url:
        refreshed = await _refresh_patterns_from_url(refresh_from_url)
        if refreshed:
            raw_patterns = refreshed

    if not raw_patterns:  # Fallback to file if no refresh URL or refresh failed
        raw_patterns = _load_patterns_from_file(_PATTERNS_FILE_PATH)

    _CACHED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in raw_patterns]


# Initialize patterns on module load (synchronously for initial load)
# For dynamic refresh, initialize_scrubber should be called during app startup
_raw_initial_patterns = _load_patterns_from_file(_PATTERNS_FILE_PATH)
_CACHED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _raw_initial_patterns]


def scrub_logs(logs: str) -> str:
    """
    Redacts sensitive information from log strings using loaded patterns.
    """
    if not logs:
        return logs

    scrubbed_logs = logs
    for pattern_re in _CACHED_PATTERNS:
        scrubbed_logs = pattern_re.sub(_REDACTION_PLACEHOLDER, scrubbed_logs)

    return scrubbed_logs


if __name__ == "__main__":
    # Example Usage
    test_logs = """
    Deployment failed. Error: Authentication failed with token dop_v1_abcdefghijklmnopqrstuvwxyz1234567890abcdef.
    Connecting to database at postgres://user:mypassword@127.0.0.1:5432/mydb.
    Received request from 192.168.1.100. User: test@example.com.
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
    eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.
    SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c.
    AWS Secret: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY.
    """

    # Test with file-based patterns
    print("--- Original Logs ---")
    print(test_logs)
    print("\n--- Scrubbed Logs (from file) ---")
    scrubbed_logs_from_file = scrub_logs(test_logs)
    print(scrubbed_logs_from_file)

    # Example of refreshing (conceptual)
    # import asyncio
    # async def demo_refresh():
    #     await initialize_scrubber(refresh_from_url="http://example.com/new-patterns.json")
    #     print("\n--- Scrubbed Logs (after conceptual refresh) ---")
    #     print(scrub_logs(test_logs))
    # asyncio.run(demo_refresh())
