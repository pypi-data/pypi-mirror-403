"""
Vulnerability detectors for CYBRET AI Scanner
"""

from scanner.detectors.base import BaseDetector, Vulnerability, VulnerabilitySeverity
from scanner.detectors.idor import IDORDetector
from scanner.detectors.auth_bypass import AuthBypassDetector

__all__ = [
    "BaseDetector",
    "Vulnerability",
    "VulnerabilitySeverity",
    "IDORDetector",
    "AuthBypassDetector",
]
