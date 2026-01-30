"""
State Security Agent - WHAT Dimension

Detects vulnerabilities related to application state:
- What state is vulnerable?
- What invariants are violated?
- What data is exposed?
- State machine violations
- State corruption risks
"""

from typing import List
from scanner.agents.base import SecurityAgent, AgentFinding, VulnerabilityDimension


class StateSecurityAgent(SecurityAgent):
    """
    Analyzes the WHAT dimension of security

    Focus areas:
    - Sensitive state fields (admin, role, password, etc.)
    - State machine integrity
    - State invariant violations
    - Data exposure
    - State corruption vectors
    """

    def __init__(self, driver, database: str = "neo4j"):
        super().__init__(
            name="StateSecurityAgent",
            dimension=VulnerabilityDimension.STATE,
            driver=driver,
            database=database,
        )

    def analyze(self, scan_id: str) -> List[AgentFinding]:
        """Run state-focused security analysis"""
        self.clear_findings()

        with self.driver.session(database=self.database) as session:
            # Analysis 1: Sensitive state fields without protection
            self._detect_sensitive_state_exposure(session, scan_id)

            # Analysis 2: State modifications without validation
            self._detect_unvalidated_state_changes(session, scan_id)

            # Analysis 3: Non-atomic state operations
            self._detect_non_atomic_operations(session, scan_id)

            # Analysis 4: State accessible without authorization
            self._detect_unprotected_state_access(session, scan_id)

        return self.findings

    def _detect_sensitive_state_exposure(self, session, scan_id: str):
        """Detect objects with sensitive fields that may be exposed"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(cls:Class)
        MATCH (cls)-[:HAS_CHILD]->(field)
        WHERE field.name =~ '(?i).*(password|secret|token|key|admin|role|permission|privilege|ssn|credit|api_key).*'
        OPTIONAL MATCH (cls)<-[:CONTAINS*]-(file:File)
        RETURN cls.name AS class_name,
               field.name AS sensitive_field,
               file.path AS file_path,
               cls.line_start AS line_start,
               cls.line_end AS line_end
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="sensitive_state_field",
                severity="medium",
                confidence=0.70,
                file_path=record["file_path"] or "unknown",
                line_start=record["line_start"] or 0,
                line_end=record["line_end"],
                function_name=record["class_name"],
                title=f"Sensitive state field in {record['class_name']}",
                description=(
                    f"Class '{record['class_name']}' contains sensitive field '{record['sensitive_field']}'. "
                    "This state requires special protection from unauthorized modification or exposure."
                ),
                context={
                    "dimension_analysis": "WHAT state is sensitive",
                    "risk": "Sensitive state may be modified or exposed"
                },
                evidence={
                    "sensitive_field": record["sensitive_field"],
                    "class_name": record["class_name"],
                },
            )
            self.findings.append(finding)

    def _detect_unvalidated_state_changes(self, session, scan_id: str):
        """Detect state changes without validation"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method)
        AND func.handles_user_input = true
        MATCH (func)-[:HAS_CHILD*]->(assign)
        WHERE assign.node_type = 'Assign'
        AND NOT (func)-[:HAS_CHILD*]->(check:IfStatement)
          WHERE check.condition =~ '(?i).*(valid|check|verify|assert|ensure).*'
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               count(assign) AS assignment_count
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            if record["assignment_count"] > 0:
                finding = AgentFinding(
                    agent_name=self.name,
                    dimension=self.dimension,
                    finding_type="unvalidated_state_change",
                    severity="medium",
                    confidence=0.65,
                    file_path=record["file_path"],
                    line_start=record["line_start"],
                    line_end=record["line_end"],
                    function_name=record["name"],
                    title=f"Unvalidated state changes in {record['name']}",
                    description=(
                        f"Function '{record['name']}' modifies state based on user input "
                        f"({record['assignment_count']} assignments) without validation. "
                        "Invalid state may be set."
                    ),
                    context={
                        "dimension_analysis": "WHAT state can be corrupted",
                        "risk": "Invalid or malicious state values"
                    },
                    evidence={
                        "assignment_count": record["assignment_count"],
                        "has_validation": False,
                    },
                )
                self.findings.append(finding)

    def _detect_non_atomic_operations(self, session, scan_id: str):
        """Detect operations that should be atomic but aren't"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method)
        MATCH (func)-[:HAS_CHILD*]->(db1:DatabaseQuery)
        MATCH (func)-[:HAS_CHILD*]->(db2:DatabaseQuery)
        WHERE id(db1) < id(db2)
        AND NOT func.name =~ '(?i).*(transaction|atomic|lock).*'
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               count(DISTINCT db1) + count(DISTINCT db2) AS db_operation_count
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            if record["db_operation_count"] >= 2:
                finding = AgentFinding(
                    agent_name=self.name,
                    dimension=self.dimension,
                    finding_type="non_atomic_operation",
                    severity="high",
                    confidence=0.60,
                    file_path=record["file_path"],
                    line_start=record["line_start"],
                    line_end=record["line_end"],
                    function_name=record["name"],
                    title=f"Non-atomic multi-step operation in {record['name']}",
                    description=(
                        f"Function '{record['name']}' performs multiple database operations "
                        "without transaction protection. State may become inconsistent if operations fail partway."
                    ),
                    context={
                        "dimension_analysis": "WHAT state can be corrupted by partial failure",
                        "risk": "State inconsistency, data corruption"
                    },
                    evidence={
                        "db_operation_count": record["db_operation_count"],
                        "has_transaction": False,
                    },
                )
                self.findings.append(finding)

    def _detect_unprotected_state_access(self, session, scan_id: str):
        """Detect sensitive state access without protection"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method OR func:Endpoint)
        AND func.handles_user_input = true
        MATCH (func)-[:HAS_CHILD*]->(call:Call)
        WHERE call.name =~ '(?i).*(get|fetch|retrieve|read|query).*'
        AND NOT func.performs_authorization = true
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               call.name AS access_call
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="unprotected_state_access",
                severity="medium",
                confidence=0.70,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Unprotected state access in {record['name']}",
                description=(
                    f"Function '{record['name']}' accesses state ({record['access_call']}) "
                    "without authorization. Sensitive state may be exposed."
                ),
                context={
                    "dimension_analysis": "WHAT state is accessible",
                    "risk": "Unauthorized state disclosure"
                },
                evidence={
                    "access_call": record["access_call"],
                    "has_authorization": False,
                },
            )
            self.findings.append(finding)
