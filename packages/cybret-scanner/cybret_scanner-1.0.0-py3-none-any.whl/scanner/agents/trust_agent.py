"""
Trust Boundary Agent - WHERE Dimension

Detects vulnerabilities related to trust boundaries:
- Where does trust break?
- Untrusted data crossing boundaries
- Missing input validation
- Trust escalation
- Boundary violations
"""

from typing import List
from scanner.agents.base import SecurityAgent, AgentFinding, VulnerabilityDimension


class TrustBoundaryAgent(SecurityAgent):
    """
    Analyzes the WHERE dimension of security

    Focus areas:
    - Untrusted input to trusted functions
    - Cross-boundary data flows
    - Missing validation/sanitization
    - Trust domain violations
    - Attack surface boundaries
    """

    def __init__(self, driver, database: str = "neo4j"):
        super().__init__(
            name="TrustBoundaryAgent",
            dimension=VulnerabilityDimension.TRUST,
            driver=driver,
            database=database,
        )

    def analyze(self, scan_id: str) -> List[AgentFinding]:
        """Run trust boundary security analysis"""
        self.clear_findings()

        with self.driver.session(database=self.database) as session:
            # Analysis 1: User input to sensitive operations
            self._detect_untrusted_to_sensitive(session, scan_id)

            # Analysis 2: Missing input validation
            self._detect_unvalidated_input_flows(session, scan_id)

            # Analysis 3: Cross-service trust issues
            self._detect_cross_service_trust(session, scan_id)

            # Analysis 4: Client-side trust issues
            self._detect_client_side_trust(session, scan_id)

        return self.findings

    def _detect_untrusted_to_sensitive(self, session, scan_id: str):
        """Detect untrusted user input flowing to sensitive operations"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(endpoint:Endpoint)
        WHERE endpoint.handles_user_input = true
        MATCH path = (endpoint)-[:CALLS*1..4]->(func)
        WHERE func.accesses_database = true OR func.performs_authorization = true
        AND NOT any(node IN nodes(path) WHERE node.has_security_check = true)
        RETURN endpoint.name AS entry_point,
               endpoint.file_path AS file_path,
               endpoint.line_start AS line_start,
               endpoint.line_end AS line_end,
               func.name AS sensitive_target,
               length(path) AS path_length
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="untrusted_to_sensitive",
                severity="high",
                confidence=0.80,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["entry_point"],
                title=f"Untrusted input flows to sensitive operation",
                description=(
                    f"User input from '{record['entry_point']}' flows through {record['path_length']} "
                    f"function calls to sensitive operation '{record['sensitive_target']}' without validation. "
                    "Trust boundary crossed without verification."
                ),
                context={
                    "dimension_analysis": "WHERE does untrusted data go",
                    "risk": "Untrusted data reaches sensitive operations"
                },
                evidence={
                    "entry_point": record["entry_point"],
                    "sensitive_target": record["sensitive_target"],
                    "path_length": record["path_length"],
                    "has_validation": False,
                },
            )
            self.findings.append(finding)

    def _detect_unvalidated_input_flows(self, session, scan_id: str):
        """Detect input flows without validation"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method OR func:Endpoint)
        AND func.handles_user_input = true
        MATCH (func)-[:HAS_CHILD*]->(call:Call)
        WHERE call.name =~ '(?i).*(query|execute|eval|system|command|file|path).*'
        AND NOT (func)-[:HAS_CHILD*]->(validation)
          WHERE validation.name =~ '(?i).*(validat|sanitiz|escap|clean|filter|check).*'
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               call.name AS dangerous_call
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="unvalidated_input",
                severity="critical",
                confidence=0.85,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Unvalidated input to dangerous operation",
                description=(
                    f"Function '{record['name']}' passes unvalidated user input to "
                    f"dangerous operation '{record['dangerous_call']}'. This crosses trust boundary "
                    "from untrusted (user input) to trusted (system operations) without validation."
                ),
                context={
                    "dimension_analysis": "WHERE trust boundary is violated",
                    "risk": "Injection attacks, system compromise"
                },
                evidence={
                    "dangerous_operation": record["dangerous_call"],
                    "has_validation": False,
                },
            )
            self.findings.append(finding)

    def _detect_cross_service_trust(self, session, scan_id: str):
        """Detect cross-service trust issues"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method)
        MATCH (func)-[:HAS_CHILD*]->(call:Call)
        WHERE call.name =~ '(?i).*(http|request|fetch|post|get|api|call|invoke).*'
        AND NOT (func)-[:HAS_CHILD*]->(auth_call)
          WHERE auth_call.name =~ '(?i).*(auth|token|credential|sign|verify).*'
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               call.name AS external_call
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="cross_service_trust",
                severity="medium",
                confidence=0.65,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Cross-service call without authentication",
                description=(
                    f"Function '{record['name']}' makes external service call "
                    f"({record['external_call']}) without visible authentication. "
                    "Verify trust boundary security between services."
                ),
                context={
                    "dimension_analysis": "WHERE services trust each other",
                    "risk": "Service-to-service trust misconfiguration"
                },
                evidence={
                    "external_call": record["external_call"],
                    "has_authentication": False,
                },
            )
            self.findings.append(finding)

    def _detect_client_side_trust(self, session, scan_id: str):
        """Detect inappropriate trust in client-side data"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method OR func:Endpoint)
        AND func.handles_user_input = true
        MATCH (func)-[:HAS_CHILD*]->(call:Call)
        WHERE call.name =~ '(?i).*(update|set|modify|change).*'
        AND NOT (func)-[:HAS_CHILD*]->(check:IfStatement)
          WHERE check.condition =~ '(?i).*(server|backend|valid|authorized|verified).*'
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               count(call) AS modification_count
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            if record["modification_count"] > 0:
                finding = AgentFinding(
                    agent_name=self.name,
                    dimension=self.dimension,
                    finding_type="client_side_trust",
                    severity="medium",
                    confidence=0.70,
                    file_path=record["file_path"],
                    line_start=record["line_start"],
                    line_end=record["line_end"],
                    function_name=record["name"],
                    title=f"Potential client-side trust issue",
                    description=(
                        f"Function '{record['name']}' accepts and uses client-provided data for "
                        f"{record['modification_count']} modifications without server-side verification. "
                        "Never trust client-side data - always verify on server."
                    ),
                    context={
                        "dimension_analysis": "WHERE client data is trusted",
                        "risk": "Client-side manipulation, parameter tampering"
                    },
                    evidence={
                        "modification_count": record["modification_count"],
                        "has_server_verification": False,
                    },
                )
                self.findings.append(finding)
