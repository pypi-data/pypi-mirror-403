"""
API Key validation and management.

API Key format: ml_sk_{tenant_id}_{random}_{checksum}
Example: ml_sk_ten_abc123_x7k9m2p4_8f3a

The API key structure:
- ml_sk_ : Prefix identifying MemoryLayer secret key
- {tenant_id} : Tenant identifier (variable length, alphanumeric)
- {random} : 8-character random string
- {checksum} : 4-character checksum for validation
"""

import hashlib
import secrets
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class APIKeyInfo:
    """Parsed API key information."""

    tenant_id: str
    key_id: str  # random portion for identification
    is_valid: bool


# API key pattern: ml_sk_{tenant_id}_{random}_{checksum}
API_KEY_PATTERN = re.compile(r"^ml_sk_([a-zA-Z0-9_]+)_([a-z0-9]{8})_([a-z0-9]{4})$")

# Character set for random generation
ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"


def compute_checksum(data: str) -> str:
    """
    Compute a 4-character checksum from data.

    Args:
        data: Input data to checksum

    Returns:
        First 4 characters of SHA-256 hash (hex)
    """
    hash_digest = hashlib.sha256(data.encode()).hexdigest()
    return hash_digest[:4]


def generate_api_key(tenant_id: str) -> str:
    """
    Generate a new API key for the given tenant.

    Args:
        tenant_id: Tenant identifier (alphanumeric, underscores allowed)

    Returns:
        Generated API key in format: ml_sk_{tenant_id}_{random}_{checksum}

    Raises:
        ValueError: If tenant_id contains invalid characters

    Example:
        >>> key = generate_api_key("ten_abc123")
        >>> print(key)
        ml_sk_ten_abc123_x7k9m2p4_8f3a
    """
    # Validate tenant_id format
    if not re.match(r"^[a-zA-Z0-9_]+$", tenant_id):
        raise ValueError("tenant_id must contain only alphanumeric characters and underscores")

    # Generate random 8-character string
    random_part = "".join(secrets.choice(ALPHABET) for _ in range(8))

    # Compute checksum from tenant_id + random
    checksum_input = f"{tenant_id}_{random_part}"
    checksum = compute_checksum(checksum_input)

    # Construct full key
    api_key = f"ml_sk_{tenant_id}_{random_part}_{checksum}"

    return api_key


def parse_api_key(api_key: str) -> Optional[APIKeyInfo]:
    """
    Parse and validate API key structure.

    Args:
        api_key: API key string to parse

    Returns:
        APIKeyInfo if valid structure, None if invalid

    Example:
        >>> info = parse_api_key("ml_sk_ten_abc123_x7k9m2p4_8f3a")
        >>> print(info.tenant_id)
        ten_abc123
    """
    match = API_KEY_PATTERN.match(api_key)
    if not match:
        return None

    tenant_id, key_id, provided_checksum = match.groups()

    # Verify checksum
    expected_checksum = compute_checksum(f"{tenant_id}_{key_id}")
    is_valid = provided_checksum == expected_checksum

    return APIKeyInfo(
        tenant_id=tenant_id,
        key_id=key_id,
        is_valid=is_valid,
    )


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format and checksum.

    Args:
        api_key: API key to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_api_key("ml_sk_ten_abc123_x7k9m2p4_8f3a")
        True
        >>> validate_api_key("invalid_key")
        False
    """
    info = parse_api_key(api_key)
    return info is not None and info.is_valid
