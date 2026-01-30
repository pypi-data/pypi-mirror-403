"""
Temporal Security Agent - WHEN Dimension

Detects vulnerabilities related to time and temporal ordering:
- When is it exploitable?
- TOCTOU (Time-of-Check-Time-of-Use)
- Race conditions
- Expiration enforcement
- Timing attacks
"""

from typing import List
from scanner.agents.base import SecurityAgent, AgentFinding, VulnerabilityDimension


class TemporalSecurityAgent(SecurityAgent):
    """
    Analyzes the WHEN dimension of security

    Focus areas:
    - TOCTOU race conditions
    - Token/session expiration
    - Time-based bypasses
    - Concurrent access issues
    - Temporal ordering violations
    """

    def __init__(self, driver, database: str = "neo4j"):
        super().__init__(
            name="TemporalSecurityAgent",
            dimension=VulnerabilityDimension.TIME,
            driver=driver,
            database=database,
        )

    def analyze(self, scan_id: str) -> List[AgentFinding]:
        """Run temporal security analysis"""
        self.clear_findings()

        with self.driver.session(database=self.database) as session:
            # Analysis 1: TOCTOU patterns (check then use)
            self._detect_toctou_patterns(session, scan_id)

            # Analysis 2: Missing expiration checks
            self._detect_missing_expiration_checks(session, scan_id)

            # Analysis 3: Race condition vulnerabilities
            self._detect_race_conditions(session, scan_id)

            # Analysis 4: Time-based bypass conditions
            self._detect_time_based_bypasses(session, scan_id)

        return self.findings

    def _detect_toctou_patterns(self, session, scan_id: str):
        """Detect Time-of-Check-Time-of-Use patterns"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method)
        MATCH (func)-[:HAS_CHILD]->(check:IfStatement)
        WHERE check.condition =~ '(?i).*(balance|quantity|count|available|exists|can_).*'
        MATCH (func)-[:HAS_CHILD]->(operation)
        WHERE operation.line_start > check.line_start
        AND operation.node_type IN ['Call', 'Assign']
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               check.condition AS check_condition,
               check.line_start AS check_line
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="toctou_pattern",
                severity="high",
                confidence=0.65,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Potential TOCTOU in {record['name']}",
                description=(
                    f"Function '{record['name']}' has check-then-use pattern for condition "
                    f"'{record['check_condition']}'. There's a race window between check and use "
                    "where state could change, leading to inconsistent operations."
                ),
                context={
                    "dimension_analysis": "WHEN can race occur",
                    "risk": "Concurrent requests can exploit race window"
                },
                evidence={
                    "check_condition": record["check_condition"],
                    "check_line": record["check_line"],
                    "pattern": "check_then_use",
                },
            )
            self.findings.append(finding)

    def _detect_missing_expiration_checks(self, session, scan_id: str):
        """Detect token/session usage without expiration checks"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method)
        AND func.performs_authentication = true
        MATCH (func)-[:HAS_CHILD*]->(var)
        WHERE var.name =~ '(?i).*(token|session|jwt|cookie|auth).*'
        AND NOT (func)-[:HAS_CHILD*]->(check:IfStatement)
          WHERE check.condition =~ '(?i).*(expir|ttl|timeout|valid_until|expires_at).*'
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               var.name AS credential_var
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="missing_expiration_check",
                severity="high",
                confidence=0.75,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Missing expiration check in {record['name']}",
                description=(
                    f"Function '{record['name']}' uses credentials ({record['credential_var']}) "
                    "without checking expiration. Expired tokens may be accepted."
                ),
                context={
                    "dimension_analysis": "WHEN should credentials expire",
                    "risk": "Expired credentials remain valid indefinitely"
                },
                evidence={
                    "credential_variable": record["credential_var"],
                    "has_expiration_check": False,
                },
            )
            self.findings.append(finding)

    def _detect_race_conditions(self, session, scan_id: str):
        """Detect potential race condition vulnerabilities"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method)
        MATCH (func)-[:HAS_CHILD*]->(read:Call)
        WHERE read.name =~ '(?i).*(get|fetch|read|query).*'
        MATCH (func)-[:HAS_CHILD*]->(write:Call)
        WHERE write.name =~ '(?i).*(set|update|save|write|modify).*'
        AND write.line_start > read.line_start
        AND NOT func.name =~ '(?i).*(lock|synchronized|atomic|transaction).*'
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               read.name AS read_operation,
               write.name AS write_operation
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="race_condition",
                severity="medium",
                confidence=0.60,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Potential race condition in {record['name']}",
                description=(
                    f"Function '{record['name']}' has read-modify-write pattern "
                    f"({record['read_operation']} then {record['write_operation']}) without locking. "
                    "Concurrent executions may cause data corruption."
                ),
                context={
                    "dimension_analysis": "WHEN can concurrent access cause issues",
                    "risk": "Data corruption from concurrent modifications"
                },
                evidence={
                    "read_operation": record["read_operation"],
                    "write_operation": record["write_operation"],
                    "has_locking": False,
                },
            )
            self.findings.append(finding)

    def _detect_time_based_bypasses(self, session, scan_id: str):
        """Detect time-based security bypasses"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method)
        AND (func.performs_authentication = true OR func.performs_authorization = true)
        MATCH (func)-[:HAS_CHILD*]->(check:IfStatement)
        WHERE check.condition =~ '(?i).*(time|date|now|today|hour|minute|expired|valid_until).*'
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               check.condition AS time_condition
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="time_based_security_logic",
                severity="medium",
                confidence=0.70,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Time-based security logic in {record['name']}",
                description=(
                    f"Function '{record['name']}' has time-based condition in security logic: "
                    f"'{record['time_condition']}'. Verify this cannot be bypassed by timing or time manipulation."
                ),
                context={
                    "dimension_analysis": "WHEN is security active",
                    "risk": "Time-based bypass or weakened security windows"
                },
                evidence={
                    "time_condition": record["time_condition"],
                    "security_function": True,
                },
            )
            self.findings.append(finding)
