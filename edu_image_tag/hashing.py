from __future__ import annotations

import hashlib


def sha256_hex(data: bytes) -> str:
    """Full SHA-256 hex digest of the given bytes (64 chars)."""
    return hashlib.sha256(data).hexdigest()


def short_hash(full_hex: str, length: int = 8) -> str:
    """First `length` characters of a hex digest, for compact ids."""
    return full_hex[:length]
