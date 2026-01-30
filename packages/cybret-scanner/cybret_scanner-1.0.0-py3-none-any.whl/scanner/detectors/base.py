"""
Base vulnerability detector interface
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from neo4j import Driver, Session


class VulnerabilitySeverity(Enum):
    """Vulnerability severity levels"""

    CRITICAL = "critical"  # Immediate exploitation, high impact
    HIGH = "high"  # Easy to exploit, significant impact
    MEDIUM = "medium"  # Requires specific conditions, moderate impact
    LOW = "low"  # Difficult to exploit or low impact
    INFO = "info"  # Informational finding


@dataclass
class Vulnerability:
    """Represents a detected vulnerability"""

    # Identification
    vuln_id: str  # Unique identifier
    vuln_type: str  # IDOR, AUTH_BYPASS, PRIV_ESC, etc.
    severity: VulnerabilitySeverity

    # Location
    file_path: str
    line_start: int
    line_end: Optional[int] = None

    # Description
    title: str = ""
    description: str = ""
    impact: str = ""
    remediation: str = ""

    # Context
    function_name: Optional[str] = None
    code_snippet: Optional[str] = None

    # Evidence
    evidence: Dict[str, Any] = field(default_factory=dict)

    # CWE mapping
    cwe: Optional[str] = None

    # Detection metadata
    detected_at: datetime = field(default_factory=datetime.now)
    detector_name: str = ""
    confidence: float = 1.0  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "vuln_id": self.vuln_id,
            "vuln_type": self.vuln_type,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "title": self.title,
            "description": self.description,
            "impact": self.impact,
            "remediation": self.remediation,
            "function_name": self.function_name,
            "code_snippet": self.code_snippet,
            "evidence": self.evidence,
            "cwe": self.cwe,
            "detected_at": self.detected_at.isoformat(),
            "detector_name": self.detector_name,
            "confidence": self.confidence,
        }


class BaseDetector(ABC):
    """Abstract base class for vulnerability detectors"""

    def __init__(self, name: str, driver: Driver, database: str = "neo4j"):
        """
        Initialize detector

        Args:
            name: Detector name
            driver: Neo4j driver instance
            database: Neo4j database name
        """
        self.name = name
        self.driver = driver
        self.database = database
        self.vulnerabilities: List[Vulnerability] = []

    @abstractmethod
    def detect(self, scan_id: str) -> List[Vulnerability]:
        """
        Run vulnerability detection

        Args:
            scan_id: Scan identifier

        Returns:
            List of detected vulnerabilities
        """
        pass

    def save_vulnerabilities(self, scan_id: str) -> int:
        """
        Save detected vulnerabilities to Neo4j

        Args:
            scan_id: Scan identifier

        Returns:
            Number of vulnerabilities saved
        """
        count = 0

        with self.driver.session(database=self.database) as session:
            for vuln in self.vulnerabilities:
                session.run(
                    """
                    MATCH (s:Scan {scan_id: $scan_id})
                    CREATE (v:Vulnerability {
                        vuln_id: $vuln_id,
                        vuln_type: $vuln_type,
                        severity: $severity,
                        file_path: $file_path,
                        line_start: $line_start,
                        line_end: $line_end,
                        title: $title,
                        description: $description,
                        impact: $impact,
                        remediation: $remediation,
                        function_name: $function_name,
                        code_snippet: $code_snippet,
                        cwe: $cwe,
                        detected_at: datetime($detected_at),
                        detector_name: $detector_name,
                        confidence: $confidence
                    })
                    MERGE (s)-[:FOUND_VULNERABILITY]->(v)
                    """,
                    scan_id=scan_id,
                    vuln_id=vuln.vuln_id,
                    vuln_type=vuln.vuln_type,
                    severity=vuln.severity.value,
                    file_path=vuln.file_path,
                    line_start=vuln.line_start,
                    line_end=vuln.line_end,
                    title=vuln.title,
                    description=vuln.description,
                    impact=vuln.impact,
                    remediation=vuln.remediation,
                    function_name=vuln.function_name,
                    code_snippet=vuln.code_snippet,
                    cwe=vuln.cwe,
                    detected_at=vuln.detected_at.isoformat(),
                    detector_name=vuln.detector_name,
                    confidence=vuln.confidence,
                )
                count += 1

        return count

    def clear_vulnerabilities(self):
        """Clear the vulnerability list"""
        self.vulnerabilities.clear()

    def get_vulnerabilities_by_severity(
        self, severity: VulnerabilitySeverity
    ) -> List[Vulnerability]:
        """Get vulnerabilities filtered by severity"""
        return [v for v in self.vulnerabilities if v.severity == severity]

    def get_critical_vulnerabilities(self) -> List[Vulnerability]:
        """Get critical severity vulnerabilities"""
        return self.get_vulnerabilities_by_severity(VulnerabilitySeverity.CRITICAL)

    def get_statistics(self) -> Dict[str, int]:
        """Get detection statistics"""
        stats = {
            "total": len(self.vulnerabilities),
            "critical": len(self.get_vulnerabilities_by_severity(VulnerabilitySeverity.CRITICAL)),
            "high": len(self.get_vulnerabilities_by_severity(VulnerabilitySeverity.HIGH)),
            "medium": len(self.get_vulnerabilities_by_severity(VulnerabilitySeverity.MEDIUM)),
            "low": len(self.get_vulnerabilities_by_severity(VulnerabilitySeverity.LOW)),
            "info": len(self.get_vulnerabilities_by_severity(VulnerabilitySeverity.INFO)),
        }
        return stats
