"""
Emergence Agent - THE KEY INNOVATION

This agent synthesizes findings from all other agents to detect
vulnerabilities that EMERGE from their COMBINATION.

Example:
- Identity Agent: User can modify resource ✓
- State Agent: Resource has sensitive state ⚠️
- Trust Agent: User input flows to database ⚠️
= EMERGENT: Critical privilege escalation via mass assignment
"""

from typing import List, Dict, Any
from itertools import combinations
from scanner.agents.base import SecurityAgent, AgentFinding, VulnerabilityDimension
from scanner.detectors.base import Vulnerability, VulnerabilitySeverity
import hashlib


class EmergentVulnerability:
    """
    Vulnerability that emerges from combination of agent findings

    This is what makes CYBRET AI unique - detecting vulnerabilities
    that NO SINGLE AGENT would find alone.
    """

    def __init__(
        self,
        vuln_type: str,
        severity: VulnerabilitySeverity,
        contributing_findings: List[AgentFinding],
        synthesis_description: str,
        exploit_scenario: str,
        remediation: str,
    ):
        self.vuln_type = vuln_type
        self.severity = severity
        self.contributing_findings = contributing_findings
        self.synthesis_description = synthesis_description
        self.exploit_scenario = exploit_scenario
        self.remediation = remediation

        # Generate unique ID from contributing findings
        self.vuln_id = self._generate_id()

        # Calculate confidence as harmonic mean of contributing confidences
        self.confidence = self._calculate_confidence()

    def _generate_id(self) -> str:
        """Generate unique ID for emergent vulnerability"""
        content = f"{self.vuln_type}:"
        for finding in self.contributing_findings:
            content += f"{finding.file_path}:{finding.line_start}"
        return f"EMERGENT-{hashlib.md5(content.encode()).hexdigest()[:12]}"

    def _calculate_confidence(self) -> float:
        """
        Calculate overall confidence from contributing findings

        Uses harmonic mean to be conservative - if any finding has low
        confidence, it drags down the overall confidence.
        """
        if not self.contributing_findings:
            return 0.0

        confidences = [f.confidence for f in self.contributing_findings]
        # Harmonic mean
        n = len(confidences)
        harmonic = n / sum(1 / c for c in confidences if c > 0)
        return min(harmonic, 1.0)

    def to_vulnerability(self) -> Vulnerability:
        """Convert to standard Vulnerability object"""
        # Use location from first finding
        first_finding = self.contributing_findings[0]

        # Build evidence
        evidence = {
            "emergent_type": "multi_dimensional_vulnerability",
            "dimensions_involved": [f.dimension.value for f in self.contributing_findings],
            "agent_findings": [f.to_dict() for f in self.contributing_findings],
            "synthesis": self.synthesis_description,
        }

        return Vulnerability(
            vuln_id=self.vuln_id,
            vuln_type=f"EMERGENT_{self.vuln_type}",
            severity=self.severity,
            file_path=first_finding.file_path,
            line_start=first_finding.line_start,
            line_end=first_finding.line_end,
            title=f"Emergent: {self.vuln_type}",
            description=self.synthesis_description,
            impact=self.exploit_scenario,
            remediation=self.remediation,
            function_name=first_finding.function_name,
            evidence=evidence,
            cwe="CWE-EMERGENT",  # Custom CWE for emergent vulnerabilities
            detector_name="EmergenceAgent",
            confidence=self.confidence,
        )


class EmergenceAgent(SecurityAgent):
    """
    THE INNOVATION: Detects emergent vulnerabilities

    This agent synthesizes findings from all other agents to discover
    vulnerabilities that emerge from their COMBINATION.

    Patterns detected:
    1. Privilege Escalation via Mass Assignment
    2. State Corruption via Race Condition
    3. Time-based Authentication Bypass
    4. Cross-boundary Data Leakage
    5. Complex Business Logic Flaws
    """

    def __init__(self, driver, database: str = "neo4j"):
        super().__init__(
            name="EmergenceAgent",
            dimension=VulnerabilityDimension.TRUST,  # Synthesis across all dimensions
            driver=driver,
            database=database,
        )

    def analyze(self, scan_id: str) -> List[AgentFinding]:
        """
        This agent doesn't analyze the graph directly.
        Instead, it synthesizes findings from other agents.

        Call synthesize() after other agents have run.
        """
        return []

    def synthesize(
        self, agent_findings: Dict[str, List[AgentFinding]]
    ) -> List[EmergentVulnerability]:
        """
        Synthesize findings from all agents to detect emergent vulnerabilities

        Args:
            agent_findings: Dict mapping agent name to their findings

        Returns:
            List of emergent vulnerabilities
        """
        emergent_vulns = []

        # Pattern 1: Privilege Escalation via Mass Assignment
        emergent_vulns.extend(self._detect_mass_assignment_privilege_escalation(agent_findings))

        # Pattern 2: State Corruption via Race Condition
        emergent_vulns.extend(self._detect_race_condition_state_corruption(agent_findings))

        # Pattern 3: Time-based Authentication Bypass
        emergent_vulns.extend(self._detect_temporal_auth_bypass(agent_findings))

        # Pattern 4: Cross-boundary Data Leakage
        emergent_vulns.extend(self._detect_cross_boundary_leakage(agent_findings))

        # Pattern 5: Complex Business Logic Flaws
        emergent_vulns.extend(self._detect_complex_logic_flaws(agent_findings))

        return emergent_vulns

    def _detect_mass_assignment_privilege_escalation(
        self, agent_findings: Dict[str, List[AgentFinding]]
    ) -> List[EmergentVulnerability]:
        """
        EMERGENT PATTERN: Privilege Escalation via Mass Assignment

        Combination:
        - Identity: User authenticated (can modify data)
        - State: Object has sensitive field (like is_admin)
        - Trust: User input flows to object update without filtering
        - Logic: No field whitelist/blacklist

        Result: User can escalate privileges by setting sensitive fields
        """
        emergent = []

        identity_findings = agent_findings.get("IdentitySecurityAgent", [])
        state_findings = agent_findings.get("StateSecurityAgent", [])
        trust_findings = agent_findings.get("TrustBoundaryAgent", [])
        logic_findings = agent_findings.get("BusinessLogicAgent", [])

        # Group findings by file and function
        by_location = {}
        for finding_list in [identity_findings, state_findings, trust_findings, logic_findings]:
            for finding in finding_list:
                key = (finding.file_path, finding.function_name)
                if key not in by_location:
                    by_location[key] = []
                by_location[key].append(finding)

        # Look for combinations
        for location, findings_at_location in by_location.items():
            # Need at least 2 dimensions to be emergent
            if len(findings_at_location) < 2:
                continue

            # Check for the pattern
            has_auth = any(
                f.dimension == VulnerabilityDimension.IDENTITY and "authenticated" in f.description.lower()
                for f in findings_at_location
            )
            has_sensitive_state = any(
                f.dimension == VulnerabilityDimension.STATE
                and any(
                    keyword in f.description.lower()
                    for keyword in ["admin", "role", "privilege", "permission", "sensitive"]
                )
                for f in findings_at_location
            )
            has_unfiltered_input = any(
                f.dimension == VulnerabilityDimension.TRUST
                and "unfiltered" in f.description.lower()
                or "mass assignment" in f.description.lower()
                for f in findings_at_location
            )

            if has_auth and has_sensitive_state and has_unfiltered_input:
                emergent.append(
                    EmergentVulnerability(
                        vuln_type="PRIVILEGE_ESCALATION_MASS_ASSIGNMENT",
                        severity=VulnerabilitySeverity.CRITICAL,
                        contributing_findings=findings_at_location,
                        synthesis_description=(
                            f"Emergent privilege escalation vulnerability detected at {location[0]}:{location[1]}. "
                            "Authenticated user can modify sensitive object fields without validation, "
                            "allowing privilege escalation by setting admin/role fields via mass assignment."
                        ),
                        exploit_scenario=(
                            "Attacker can escalate privileges by:\n"
                            "1. Authenticate as normal user\n"
                            "2. Send request with {'is_admin': true} or {'role': 'admin'}\n"
                            "3. Mass assignment updates sensitive field\n"
                            "4. Attacker gains elevated privileges\n"
                            "Impact: Complete compromise of authorization model"
                        ),
                        remediation=(
                            "1. Implement field whitelist for user updates\n"
                            "2. Never allow users to modify sensitive fields (is_admin, role, permissions)\n"
                            "3. Use separate endpoints for privilege modification with strict authorization\n"
                            "4. Example:\n"
                            "   allowed_fields = ['name', 'email', 'profile_picture']\n"
                            "   filtered_data = {k: v for k, v in user_data.items() if k in allowed_fields}\n"
                            "   user.update(filtered_data)"
                        ),
                    )
                )

        return emergent

    def _detect_race_condition_state_corruption(
        self, agent_findings: Dict[str, List[AgentFinding]]
    ) -> List[EmergentVulnerability]:
        """
        EMERGENT PATTERN: State Corruption via Race Condition

        Combination:
        - State: Critical state (like account balance)
        - Time: TOCTOU race window
        - Logic: Non-atomic operations

        Result: Concurrent requests can corrupt state
        """
        emergent = []

        state_findings = agent_findings.get("StateSecurityAgent", [])
        temporal_findings = agent_findings.get("TemporalSecurityAgent", [])
        logic_findings = agent_findings.get("BusinessLogicAgent", [])

        # Find co-located findings
        by_location = {}
        for finding_list in [state_findings, temporal_findings, logic_findings]:
            for finding in finding_list:
                key = (finding.file_path, finding.function_name)
                if key not in by_location:
                    by_location[key] = []
                by_location[key].append(finding)

        for location, findings_at_location in by_location.items():
            if len(findings_at_location) < 2:
                continue

            has_critical_state = any(
                f.dimension == VulnerabilityDimension.STATE
                and any(keyword in f.description.lower() for keyword in ["balance", "inventory", "quantity", "count"])
                for f in findings_at_location
            )
            has_race_window = any(
                f.dimension == VulnerabilityDimension.TIME and "race" in f.description.lower()
                for f in findings_at_location
            )
            has_non_atomic = any(
                "atomic" in f.description.lower() or "transaction" in f.description.lower()
                for f in findings_at_location
            )

            if has_critical_state and (has_race_window or has_non_atomic):
                emergent.append(
                    EmergentVulnerability(
                        vuln_type="STATE_CORRUPTION_RACE_CONDITION",
                        severity=VulnerabilitySeverity.HIGH,
                        contributing_findings=findings_at_location,
                        synthesis_description=(
                            f"Emergent state corruption vulnerability via race condition at {location[0]}:{location[1]}. "
                            "Critical state operations are not atomic, allowing concurrent requests to corrupt data."
                        ),
                        exploit_scenario=(
                            "Attacker can corrupt state by:\n"
                            "1. Send multiple concurrent requests\n"
                            "2. Exploit TOCTOU window between check and use\n"
                            "3. Cause state inconsistency (overdraw account, oversell inventory)\n"
                            "Impact: Financial loss, data integrity violations"
                        ),
                        remediation=(
                            "1. Use database transactions with proper isolation\n"
                            "2. Implement optimistic locking (version numbers)\n"
                            "3. Use atomic operations (e.g., UPDATE balance = balance - amount WHERE id = ? AND balance >= amount)\n"
                            "4. Add row-level locks for critical operations"
                        ),
                    )
                )

        return emergent

    def _detect_temporal_auth_bypass(
        self, agent_findings: Dict[str, List[AgentFinding]]
    ) -> List[EmergentVulnerability]:
        """
        EMERGENT PATTERN: Time-based Authentication Bypass

        Combination:
        - Identity: Authentication check exists
        - Time: Token/session has expiration
        - Logic: Expiration not enforced

        Result: Expired credentials still work
        """
        emergent = []

        identity_findings = agent_findings.get("IdentitySecurityAgent", [])
        temporal_findings = agent_findings.get("TemporalSecurityAgent", [])

        by_location = {}
        for finding in identity_findings + temporal_findings:
            key = (finding.file_path, finding.function_name)
            if key not in by_location:
                by_location[key] = []
            by_location[key].append(finding)

        for location, findings_at_location in by_location.items():
            if len(findings_at_location) < 2:
                continue

            has_auth = any(f.dimension == VulnerabilityDimension.IDENTITY for f in findings_at_location)
            has_temporal_issue = any(
                f.dimension == VulnerabilityDimension.TIME
                and any(keyword in f.description.lower() for keyword in ["expired", "expiration", "ttl", "timeout"])
                for f in findings_at_location
            )

            if has_auth and has_temporal_issue:
                emergent.append(
                    EmergentVulnerability(
                        vuln_type="TEMPORAL_AUTH_BYPASS",
                        severity=VulnerabilitySeverity.HIGH,
                        contributing_findings=findings_at_location,
                        synthesis_description=(
                            f"Emergent time-based authentication bypass at {location[0]}:{location[1]}. "
                            "Authentication mechanism exists but expiration is not properly enforced."
                        ),
                        exploit_scenario=(
                            "Attacker can bypass time-based security by:\n"
                            "1. Obtain valid token/session\n"
                            "2. Wait for expiration time\n"
                            "3. Continue using expired credentials\n"
                            "Impact: Unauthorized access persists beyond intended timeframe"
                        ),
                        remediation=(
                            "1. Always check token/session expiration before use\n"
                            "2. Invalidate expired tokens server-side\n"
                            "3. Implement token refresh mechanism\n"
                            "4. Use short-lived tokens with refresh tokens"
                        ),
                    )
                )

        return emergent

    def _detect_cross_boundary_leakage(
        self, agent_findings: Dict[str, List[AgentFinding]]
    ) -> List[EmergentVulnerability]:
        """
        EMERGENT PATTERN: Cross-boundary Data Leakage

        Combination:
        - Trust: Data crosses trust boundary
        - Identity: No access control at boundary
        - State: Data contains sensitive information

        Result: Sensitive data leaks across boundaries
        """
        emergent = []

        trust_findings = agent_findings.get("TrustBoundaryAgent", [])
        identity_findings = agent_findings.get("IdentitySecurityAgent", [])
        state_findings = agent_findings.get("StateSecurityAgent", [])

        by_location = {}
        for finding in trust_findings + identity_findings + state_findings:
            key = (finding.file_path, finding.function_name)
            if key not in by_location:
                by_location[key] = []
            by_location[key].append(finding)

        for location, findings_at_location in by_location.items():
            if len(findings_at_location) < 2:
                continue

            has_boundary_crossing = any(
                f.dimension == VulnerabilityDimension.TRUST and "boundary" in f.description.lower()
                for f in findings_at_location
            )
            has_missing_access_control = any(
                f.dimension == VulnerabilityDimension.IDENTITY and "missing" in f.description.lower()
                for f in findings_at_location
            )
            has_sensitive_data = any(
                f.dimension == VulnerabilityDimension.STATE
                and any(
                    keyword in f.description.lower()
                    for keyword in ["sensitive", "private", "confidential", "secret", "password"]
                )
                for f in findings_at_location
            )

            if has_boundary_crossing and (has_missing_access_control or has_sensitive_data):
                emergent.append(
                    EmergentVulnerability(
                        vuln_type="CROSS_BOUNDARY_DATA_LEAKAGE",
                        severity=VulnerabilitySeverity.HIGH,
                        contributing_findings=findings_at_location,
                        synthesis_description=(
                            f"Emergent cross-boundary data leakage at {location[0]}:{location[1]}. "
                            "Sensitive data crosses trust boundaries without proper access control."
                        ),
                        exploit_scenario=(
                            "Attacker can leak sensitive data by:\n"
                            "1. Access endpoint that crosses boundaries\n"
                            "2. Receive sensitive data without authorization\n"
                            "3. Data exposure to untrusted context\n"
                            "Impact: Privacy breach, data exposure"
                        ),
                        remediation=(
                            "1. Implement access control at trust boundaries\n"
                            "2. Filter sensitive fields before crossing boundaries\n"
                            "3. Use DTOs (Data Transfer Objects) to control exposed data\n"
                            "4. Apply principle of least privilege"
                        ),
                    )
                )

        return emergent

    def _detect_complex_logic_flaws(
        self, agent_findings: Dict[str, List[AgentFinding]]
    ) -> List[EmergentVulnerability]:
        """
        EMERGENT PATTERN: Complex Business Logic Flaws

        Combination of findings from multiple dimensions that together
        indicate a business logic vulnerability.
        """
        emergent = []

        # This is a catch-all for complex patterns
        # Look for 3+ dimensional findings in same location

        all_findings = []
        for findings_list in agent_findings.values():
            all_findings.extend(findings_list)

        by_location = {}
        for finding in all_findings:
            key = (finding.file_path, finding.function_name)
            if key not in by_location:
                by_location[key] = []
            by_location[key].append(finding)

        for location, findings_at_location in by_location.items():
            # Need 3+ dimensions for complex logic flaw
            if len(findings_at_location) < 3:
                continue

            # Count unique dimensions
            dimensions = set(f.dimension for f in findings_at_location)
            if len(dimensions) >= 3:
                # This is a complex multi-dimensional issue
                emergent.append(
                    EmergentVulnerability(
                        vuln_type="COMPLEX_LOGIC_FLAW",
                        severity=VulnerabilitySeverity.MEDIUM,
                        contributing_findings=findings_at_location,
                        synthesis_description=(
                            f"Complex business logic vulnerability detected at {location[0]}:{location[1]}. "
                            f"Multiple security dimensions ({len(dimensions)}) have issues that compound into a logic flaw."
                        ),
                        exploit_scenario=(
                            "Multiple security weaknesses combine to create exploitable logic flaw. "
                            "Manual review recommended to assess full impact."
                        ),
                        remediation=(
                            "Review the combination of findings from multiple agents. "
                            "Address each individual finding and verify no emergent vulnerability remains."
                        ),
                    )
                )

        return emergent
