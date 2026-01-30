# src/xenfra_sdk/security.py
"""
Security utilities for the Xenfra SDK.
Provides token encryption/decryption for storing OAuth credentials.
"""

import os
from typing import Optional

from cryptography.fernet import Fernet

# --- Configuration from Environment ---
# These should be set in the service's environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")


def _get_fernet() -> Optional[Fernet]:
    """Get Fernet instance for encryption/decryption."""
    if not ENCRYPTION_KEY:
        return None
    try:
        return Fernet(ENCRYPTION_KEY.encode())
    except Exception:
        return None


# --- Token Encryption ---
def encrypt_token(token: str) -> str:
    """Encrypts a token using Fernet symmetric encryption."""
    fernet = _get_fernet()
    if fernet is None:
        raise ValueError("ENCRYPTION_KEY environment variable is not set or invalid")
    return fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypts a token."""
    fernet = _get_fernet()
    if fernet is None:
        raise ValueError("ENCRYPTION_KEY environment variable is not set or invalid")
    return fernet.decrypt(encrypted_token.encode()).decode()
