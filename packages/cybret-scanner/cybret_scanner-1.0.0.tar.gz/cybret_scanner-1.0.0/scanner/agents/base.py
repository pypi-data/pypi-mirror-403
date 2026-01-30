"""
Base agent interface for multi-agent security intelligence system
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime


class VulnerabilityDimension(Enum):
    """The 4 dimensions of vulnerability analysis"""

    IDENTITY = "identity"  # WHO can exploit
    STATE = "state"  # WHAT state is affected
    TIME = "time"  # WHEN is it exploitable
    TRUST = "trust"  # WHERE does trust break


@dataclass
class AgentFinding:
    """
    Finding from a specialized security agent

    This represents what ONE agent discovered. The Emergence Agent
    will synthesize multiple findings to detect emergent vulnerabilities.
    """

    agent_name: str
    dimension: VulnerabilityDimension
    finding_type: str
    severity: str  # critical, high, medium, low
    confidence: float  # 0.0 to 1.0

    # Location
    file_path: str
    line_start: int
    line_end: Optional[int] = None
    function_name: Optional[str] = None

    # Description
    title: str = ""
    description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    # Evidence from this dimension
    evidence: Dict[str, Any] = field(default_factory=dict)

    # Related graph nodes/paths
    graph_nodes: List[str] = field(default_factory=list)
    graph_paths: List[List[str]] = field(default_factory=list)

    detected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_name": self.agent_name,
            "dimension": self.dimension.value,
            "finding_type": self.finding_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "function_name": self.function_name,
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "evidence": self.evidence,
            "graph_nodes": self.graph_nodes,
            "graph_paths": self.graph_paths,
            "detected_at": self.detected_at.isoformat(),
        }


class SecurityAgent(ABC):
    """
    Abstract base class for specialized security agents

    Each agent focuses on one dimension of security:
    - IdentityAgent: WHO-based vulnerabilities
    - StateAgent: WHAT-based vulnerabilities
    - TemporalAgent: WHEN-based vulnerabilities
    - TrustAgent: WHERE-based vulnerabilities
    - LogicAgent: Business logic flaws
    - EmergenceAgent: Synthesizes findings from all agents
    """

    def __init__(
        self,
        name: str,
        dimension: VulnerabilityDimension,
        driver,
        database: str = "neo4j",
    ):
        """
        Initialize security agent

        Args:
            name: Agent name
            dimension: Primary dimension this agent analyzes
            driver: Neo4j driver for graph queries
            database: Neo4j database name
        """
        self.name = name
        self.dimension = dimension
        self.driver = driver
        self.database = database
        self.findings: List[AgentFinding] = []

    @abstractmethod
    def analyze(self, scan_id: str) -> List[AgentFinding]:
        """
        Analyze the code graph and return findings

        Args:
            scan_id: Scan identifier

        Returns:
            List of agent findings
        """
        pass

    def clear_findings(self):
        """Clear the findings list"""
        self.findings.clear()

    def get_findings_by_severity(self, severity: str) -> List[AgentFinding]:
        """Get findings filtered by severity"""
        return [f for f in self.findings if f.severity == severity]

    def get_critical_findings(self) -> List[AgentFinding]:
        """Get critical severity findings"""
        return self.get_findings_by_severity("critical")

    def get_statistics(self) -> Dict[str, int]:
        """Get agent statistics"""
        stats = {
            "total": len(self.findings),
            "critical": len(self.get_findings_by_severity("critical")),
            "high": len(self.get_findings_by_severity("high")),
            "medium": len(self.get_findings_by_severity("medium")),
            "low": len(self.get_findings_by_severity("low")),
        }
        return stats

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} dimension={self.dimension.value} findings={len(self.findings)}>"
