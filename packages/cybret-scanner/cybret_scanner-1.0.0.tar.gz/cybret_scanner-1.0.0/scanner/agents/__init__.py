"""
Multi-Agent Security Intelligence System for CYBRET AI

Specialized agents collaborate to detect emergent vulnerabilities
across identity, state, time, and trust dimensions.
"""

from scanner.agents.base import SecurityAgent, AgentFinding
from scanner.agents.orchestrator import SecurityAgentOrchestrator
from scanner.agents.identity_agent import IdentitySecurityAgent
from scanner.agents.state_agent import StateSecurityAgent
from scanner.agents.temporal_agent import TemporalSecurityAgent
from scanner.agents.trust_agent import TrustBoundaryAgent
from scanner.agents.logic_agent import BusinessLogicAgent
from scanner.agents.emergence_agent import EmergenceAgent

__all__ = [
    "SecurityAgent",
    "AgentFinding",
    "SecurityAgentOrchestrator",
    "IdentitySecurityAgent",
    "StateSecurityAgent",
    "TemporalSecurityAgent",
    "TrustBoundaryAgent",
    "BusinessLogicAgent",
    "EmergenceAgent",
]
