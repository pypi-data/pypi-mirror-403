# SoulEyez Detection Validation
# Correlates attacks with SIEM detections

from .validator import DetectionValidator
from .attack_signatures import ATTACK_SIGNATURES

__all__ = ["DetectionValidator", "ATTACK_SIGNATURES"]
