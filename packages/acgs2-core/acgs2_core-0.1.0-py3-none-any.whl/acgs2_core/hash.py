"""
Constitutional Hash Implementation

The constitutional hash serves as an immutable anchor for governance verification.
Every verification includes this hash to ensure system integrity.

Constitutional Hash: cdd01ef066bc6cf2
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional

# The immutable constitutional hash anchor
CONSTITUTIONAL_HASH = "cdd01ef066bc6cf2"


def constitutional_hash(
    content: str,
    timestamp: Optional[datetime] = None,
    include_anchor: bool = True
) -> str:
    """
    Generate a constitutional hash for content verification.

    Args:
        content: The content to hash
        timestamp: Optional timestamp (defaults to current UTC time)
        include_anchor: Whether to include the constitutional anchor

    Returns:
        A cryptographic hash string

    Example:
        >>> from acgs2_core import constitutional_hash
        >>> hash_value = constitutional_hash("AI output to verify")
        >>> print(hash_value[:16])  # First 16 chars
        'a1b2c3d4e5f6g7h8'
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    # Build the hash input
    hash_input = content

    if include_anchor:
        hash_input = f"{CONSTITUTIONAL_HASH}:{hash_input}"

    # Add timestamp for uniqueness
    hash_input = f"{hash_input}:{timestamp.isoformat()}"

    # Generate SHA-256 hash
    hash_bytes = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    return hash_bytes


def verify_hash_integrity(
    content: str,
    expected_hash: str,
    timestamp: datetime
) -> bool:
    """
    Verify that content matches its expected hash.

    Args:
        content: The original content
        expected_hash: The hash to verify against
        timestamp: The timestamp used in original hash

    Returns:
        True if hash matches, False otherwise
    """
    computed_hash = constitutional_hash(content, timestamp)
    return computed_hash == expected_hash


def get_anchor_hash() -> str:
    """
    Get the constitutional anchor hash.

    This hash is immutable and serves as the foundation
    for all governance verification in ACGS-2.

    Returns:
        The constitutional anchor hash: cdd01ef066bc6cf2
    """
    return CONSTITUTIONAL_HASH
