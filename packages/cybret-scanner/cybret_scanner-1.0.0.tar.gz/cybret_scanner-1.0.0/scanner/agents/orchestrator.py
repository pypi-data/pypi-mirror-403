"""
Security Agent Orchestrator

Coordinates all specialized security agents and synthesizes their findings
through the Emergence Agent to detect complex vulnerabilities.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

from scanner.agents.base import SecurityAgent, AgentFinding, VulnerabilityDimension
from scanner.agents.identity_agent import IdentitySecurityAgent
from scanner.agents.state_agent import StateSecurityAgent
from scanner.agents.temporal_agent import TemporalSecurityAgent
from scanner.agents.trust_agent import TrustBoundaryAgent
from scanner.agents.logic_agent import BusinessLogicAgent
from scanner.agents.emergence_agent import EmergenceAgent, EmergentVulnerability


logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResult:
    """
    Complete security analysis result from all agents

    Contains:
    - Individual agent findings
    - Emergent vulnerabilities synthesized across agents
    - Statistics and metrics
    """

    scan_id: str
    started_at: datetime
    completed_at: datetime

    # Individual agent findings by dimension
    agent_findings: Dict[str, List[AgentFinding]] = field(default_factory=dict)

    # Emergent vulnerabilities (THE INNOVATION)
    emergent_vulnerabilities: List[EmergentVulnerability] = field(default_factory=list)

    # Statistics
    total_findings: int = 0
    total_emergent_vulns: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Agent execution times
    agent_durations: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "scan_id": self.scan_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": (self.completed_at - self.started_at).total_seconds(),
            "statistics": {
                "total_findings": self.total_findings,
                "total_emergent_vulnerabilities": self.total_emergent_vulns,
                "by_severity": {
                    "critical": self.critical_count,
                    "high": self.high_count,
                    "medium": self.medium_count,
                    "low": self.low_count,
                }
            },
            "agent_findings": {
                agent: [f.to_dict() for f in findings]
                for agent, findings in self.agent_findings.items()
            },
            "emergent_vulnerabilities": [
                v.to_dict() for v in self.emergent_vulnerabilities
            ],
            "performance": {
                "agent_durations": self.agent_durations,
                "total_agents": len(self.agent_durations),
            }
        }


class SecurityAgentOrchestrator:
    """
    Orchestrates the multi-agent security analysis system

    Coordinates 5 specialized agents + 1 synthesis agent:
    1. IdentitySecurityAgent (WHO dimension)
    2. StateSecurityAgent (WHAT dimension)
    3. TemporalSecurityAgent (WHEN dimension)
    4. TrustBoundaryAgent (WHERE dimension)
    5. BusinessLogicAgent (Logic flaws)
    6. EmergenceAgent (Synthesis - THE INNOVATION)

    Execution Flow:
    1. Run all specialized agents in parallel/sequence
    2. Collect findings from each dimension
    3. Pass findings to Emergence Agent
    4. Synthesize emergent vulnerabilities
    5. Return complete analysis
    """

    def __init__(self, driver, database: str = "neo4j"):
        """
        Initialize orchestrator with all security agents

        Args:
            driver: Neo4j driver for graph queries
            database: Neo4j database name
        """
        self.driver = driver
        self.database = database

        # Initialize specialized agents
        self.agents: List[SecurityAgent] = [
            IdentitySecurityAgent(driver, database),
            StateSecurityAgent(driver, database),
            TemporalSecurityAgent(driver, database),
            TrustBoundaryAgent(driver, database),
            BusinessLogicAgent(driver, database),
        ]

        # Initialize emergence agent for synthesis
        self.emergence_agent = EmergenceAgent(driver, database)

        logger.info(f"Initialized SecurityAgentOrchestrator with {len(self.agents)} agents")

    def run_analysis(self, scan_id: str) -> OrchestrationResult:
        """
        Run complete multi-agent security analysis

        Args:
            scan_id: Scan identifier

        Returns:
            OrchestrationResult with all findings and emergent vulnerabilities
        """
        started_at = datetime.now()
        logger.info(f"Starting multi-agent analysis for scan {scan_id}")

        result = OrchestrationResult(
            scan_id=scan_id,
            started_at=started_at,
            completed_at=started_at,  # Updated at end
        )

        # Phase 1: Run all specialized agents
        logger.info("Phase 1: Running specialized agents")
        agent_findings = self._run_specialized_agents(scan_id, result)

        # Phase 2: Synthesize emergent vulnerabilities
        logger.info("Phase 2: Synthesizing emergent vulnerabilities")
        emergent_vulns = self._synthesize_emergent_vulnerabilities(agent_findings)

        # Phase 3: Compile results
        result.agent_findings = agent_findings
        result.emergent_vulnerabilities = emergent_vulns
        result.completed_at = datetime.now()

        # Calculate statistics
        self._calculate_statistics(result)

        logger.info(
            f"Analysis complete: {result.total_findings} findings, "
            f"{result.total_emergent_vulns} emergent vulnerabilities"
        )

        return result

    def _run_specialized_agents(
        self,
        scan_id: str,
        result: OrchestrationResult
    ) -> Dict[str, List[AgentFinding]]:
        """
        Run all specialized security agents

        Args:
            scan_id: Scan identifier
            result: Result object to store timings

        Returns:
            Dictionary mapping agent name to findings
        """
        agent_findings = {}

        for agent in self.agents:
            agent_start = datetime.now()
            logger.info(f"Running {agent.name} ({agent.dimension.value} dimension)")

            try:
                findings = agent.analyze(scan_id)
                agent_findings[agent.name] = findings

                duration = (datetime.now() - agent_start).total_seconds()
                result.agent_durations[agent.name] = duration

                logger.info(
                    f"{agent.name} complete: {len(findings)} findings "
                    f"in {duration:.2f}s"
                )

            except Exception as e:
                logger.error(f"Error running {agent.name}: {e}")
                agent_findings[agent.name] = []
                result.agent_durations[agent.name] = 0.0

        return agent_findings

    def _synthesize_emergent_vulnerabilities(
        self,
        agent_findings: Dict[str, List[AgentFinding]]
    ) -> List[EmergentVulnerability]:
        """
        Use Emergence Agent to synthesize findings

        This is THE INNOVATION - detecting vulnerabilities that emerge
        from the COMBINATION of findings across multiple agents.

        Args:
            agent_findings: Findings from all specialized agents

        Returns:
            List of emergent vulnerabilities
        """
        synthesis_start = datetime.now()
        logger.info("Starting emergence synthesis")

        try:
            emergent_vulns = self.emergence_agent.synthesize(agent_findings)

            duration = (datetime.now() - synthesis_start).total_seconds()
            logger.info(
                f"Emergence synthesis complete: {len(emergent_vulns)} "
                f"emergent vulnerabilities detected in {duration:.2f}s"
            )

            return emergent_vulns

        except Exception as e:
            logger.error(f"Error in emergence synthesis: {e}")
            return []

    def _calculate_statistics(self, result: OrchestrationResult):
        """Calculate statistics for the orchestration result"""

        # Count individual findings by severity
        for findings in result.agent_findings.values():
            result.total_findings += len(findings)
            for finding in findings:
                if finding.severity == "critical":
                    result.critical_count += 1
                elif finding.severity == "high":
                    result.high_count += 1
                elif finding.severity == "medium":
                    result.medium_count += 1
                elif finding.severity == "low":
                    result.low_count += 1

        # Count emergent vulnerabilities by severity
        result.total_emergent_vulns = len(result.emergent_vulnerabilities)
        for vuln in result.emergent_vulnerabilities:
            if vuln.severity == "critical":
                result.critical_count += 1
            elif vuln.severity == "high":
                result.high_count += 1
            elif vuln.severity == "medium":
                result.medium_count += 1

    def get_critical_vulnerabilities(
        self,
        result: OrchestrationResult
    ) -> List[Dict]:
        """
        Get all critical vulnerabilities (individual + emergent)

        Args:
            result: Orchestration result

        Returns:
            List of critical vulnerabilities with metadata
        """
        critical_vulns = []

        # Individual critical findings
        for agent_name, findings in result.agent_findings.items():
            for finding in findings:
                if finding.severity == "critical":
                    critical_vulns.append({
                        "type": "individual_finding",
                        "agent": agent_name,
                        "data": finding.to_dict(),
                    })

        # Emergent critical vulnerabilities
        for vuln in result.emergent_vulnerabilities:
            if vuln.severity == "critical":
                critical_vulns.append({
                    "type": "emergent_vulnerability",
                    "data": vuln.to_dict(),
                })

        return critical_vulns

    def get_findings_by_dimension(
        self,
        result: OrchestrationResult,
        dimension: VulnerabilityDimension
    ) -> List[AgentFinding]:
        """
        Get all findings for a specific dimension

        Args:
            result: Orchestration result
            dimension: Vulnerability dimension to filter by

        Returns:
            List of findings for that dimension
        """
        dimension_findings = []

        for findings in result.agent_findings.values():
            for finding in findings:
                if finding.dimension == dimension:
                    dimension_findings.append(finding)

        return dimension_findings

    def get_findings_by_file(
        self,
        result: OrchestrationResult,
        file_path: str
    ) -> Dict[str, List]:
        """
        Get all findings and vulnerabilities for a specific file

        Args:
            result: Orchestration result
            file_path: File path to filter by

        Returns:
            Dictionary with individual findings and emergent vulnerabilities
        """
        file_findings = []
        file_emergent = []

        # Individual findings
        for findings in result.agent_findings.values():
            for finding in findings:
                if finding.file_path == file_path:
                    file_findings.append(finding)

        # Emergent vulnerabilities
        for vuln in result.emergent_vulnerabilities:
            # Check if any contributing finding is from this file
            for finding in vuln.contributing_findings:
                if finding.file_path == file_path:
                    file_emergent.append(vuln)
                    break

        return {
            "individual_findings": [f.to_dict() for f in file_findings],
            "emergent_vulnerabilities": [v.to_dict() for v in file_emergent],
            "total_issues": len(file_findings) + len(file_emergent),
        }

    def generate_executive_summary(
        self,
        result: OrchestrationResult
    ) -> Dict[str, Any]:
        """
        Generate executive summary of security analysis

        Args:
            result: Orchestration result

        Returns:
            Executive summary with key metrics and insights
        """
        critical_vulns = self.get_critical_vulnerabilities(result)

        # Calculate risk score (0-100)
        risk_score = min(100, (
            result.critical_count * 25 +
            result.high_count * 10 +
            result.medium_count * 3 +
            result.low_count * 1
        ))

        # Determine risk level
        if risk_score >= 75:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "scan_id": result.scan_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "summary": {
                "total_issues": result.total_findings + result.total_emergent_vulns,
                "critical": result.critical_count,
                "high": result.high_count,
                "medium": result.medium_count,
                "low": result.low_count,
            },
            "innovation_metrics": {
                "emergent_vulnerabilities_detected": result.total_emergent_vulns,
                "individual_findings": result.total_findings,
                "synthesis_advantage": (
                    f"{result.total_emergent_vulns} vulnerabilities found through "
                    "multi-agent synthesis that individual agents missed"
                ),
            },
            "top_critical_issues": [
                {
                    "title": vuln["data"].get("title"),
                    "file": vuln["data"].get("file_path") or vuln["data"].get("primary_location"),
                    "type": vuln["type"],
                }
                for vuln in critical_vulns[:5]  # Top 5
            ],
            "dimension_coverage": {
                "identity_who": len(self.get_findings_by_dimension(result, VulnerabilityDimension.IDENTITY)),
                "state_what": len(self.get_findings_by_dimension(result, VulnerabilityDimension.STATE)),
                "time_when": len(self.get_findings_by_dimension(result, VulnerabilityDimension.TIME)),
                "trust_where": len(self.get_findings_by_dimension(result, VulnerabilityDimension.TRUST)),
            },
            "analysis_duration": (result.completed_at - result.started_at).total_seconds(),
        }
