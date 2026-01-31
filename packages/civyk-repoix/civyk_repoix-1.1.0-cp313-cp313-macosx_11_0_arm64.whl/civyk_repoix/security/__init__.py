"""Security module for secret detection and redaction.

This package provides tools for detecting and redacting sensitive data
from code content to prevent accidental exposure of credentials.

Components:
    SecretScanner: Main scanner class with pattern and entropy detection
    SecretMatch: Detected secret with location information
    SecretType: Enumeration of detectable secret types

Supported Secret Types:
    - AWS access keys and secret keys
    - GitHub tokens and Personal Access Tokens
    - Stripe API keys (live and test)
    - JWT tokens
    - Generic API keys, secrets, and passwords
    - Private keys (RSA, EC, DSA, OpenSSH)
    - High-entropy strings (potential unknown secrets)

Features:
    - Pattern-based detection using regex
    - Entropy-based detection for unknown secrets
    - Content redaction for safe logging
    - Symlink-safe file scanning (TOCTOU-resistant)
"""

from civyk_repoix.security.scanner import (
    REDACTED_PLACEHOLDER,
    SecretMatch,
    SecretScanner,
    SecretType,
    calculate_entropy,
)

__all__ = [
    "REDACTED_PLACEHOLDER",
    "SecretMatch",
    "SecretScanner",
    "SecretType",
    "calculate_entropy",
]
