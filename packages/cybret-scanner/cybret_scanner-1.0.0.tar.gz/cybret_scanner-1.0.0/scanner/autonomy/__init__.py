"""
Autonomous Remediation System

Implements graduated autonomy for vulnerability remediation:
- Level 1: Suggest (show fix to developer)
- Level 2: Draft (generate PR for review)
- Level 3: Execute with approval (auto-fix after human review)
- Level 4: Autonomous (auto-fix with monitoring)
"""

from scanner.autonomy.engine import AutonomyEngine, AutonomyLevel, RemediationAction
from scanner.autonomy.trust_scorer import TrustScorer

__all__ = [
    "AutonomyEngine",
    "AutonomyLevel",
    "RemediationAction",
    "TrustScorer",
]
