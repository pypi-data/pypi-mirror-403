"""
SoulEyez Licensing System

Provides offline license validation using Ed25519 cryptographic signatures.
License keys are signed JSON payloads that can be validated without internet.
"""

from souleyez.licensing.validator import (
    LicenseValidator,
    LicenseInfo,
    validate_license,
    activate_license,
    get_active_license,
    deactivate_license,
)

__all__ = [
    "LicenseValidator",
    "LicenseInfo",
    "validate_license",
    "activate_license",
    "get_active_license",
    "deactivate_license",
]
