"""
Identity Security Agent - WHO Dimension

Detects vulnerabilities related to identity, authentication, and authorization:
- Who can access resources?
- Who can perform actions?
- Who owns what?
- Missing authorization checks
- Privilege escalation paths
"""

from typing import List
from scanner.agents.base import SecurityAgent, AgentFinding, VulnerabilityDimension


class IdentitySecurityAgent(SecurityAgent):
    """
    Analyzes the WHO dimension of security

    Focus areas:
    - Authentication presence/absence
    - Authorization checks
    - Ownership validation
    - Privilege boundaries
    - User identity propagation
    """

    def __init__(self, driver, database: str = "neo4j"):
        super().__init__(
            name="IdentitySecurityAgent",
            dimension=VulnerabilityDimension.IDENTITY,
            driver=driver,
            database=database,
        )

    def analyze(self, scan_id: str) -> List[AgentFinding]:
        """Run identity-focused security analysis"""
        self.clear_findings()

        with self.driver.session(database=self.database) as session:
            # Analysis 1: Functions with user input but no auth
            self._detect_missing_authentication(session, scan_id)

            # Analysis 2: Database access without ownership checks
            self._detect_missing_ownership_validation(session, scan_id)

            # Analysis 3: Privilege-sensitive operations without authorization
            self._detect_privilege_operations_without_authz(session, scan_id)

            # Analysis 4: User data modification without identity verification
            self._detect_unverified_user_modifications(session, scan_id)

        return self.findings

    def _detect_missing_authentication(self, session, scan_id: str):
        """Detect endpoints without authentication"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(endpoint)
        WHERE (endpoint:Endpoint OR endpoint:Function)
        AND endpoint.handles_user_input = true
        AND NOT endpoint.has_decorators
        AND endpoint.is_public = true
        RETURN endpoint.name AS name,
               endpoint.file_path AS file_path,
               endpoint.line_start AS line_start,
               endpoint.line_end AS line_end
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="missing_authentication",
                severity="high",
                confidence=0.85,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Missing authentication in {record['name']}",
                description=(
                    f"Function '{record['name']}' handles user input but has no authentication. "
                    "Any anonymous user can access this endpoint."
                ),
                context={
                    "dimension_analysis": "WHO can access",
                    "risk": "Anonymous access to potentially sensitive operations"
                },
                evidence={
                    "has_decorators": False,
                    "handles_user_input": True,
                    "is_public": True,
                },
            )
            self.findings.append(finding)

    def _detect_missing_ownership_validation(self, session, scan_id: str):
        """Detect database queries without ownership checks"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method OR func:Endpoint)
        AND func.handles_user_input = true
        MATCH (func)-[:HAS_CHILD*]->(db:DatabaseQuery)
        WHERE NOT (func)-[:HAS_CHILD*]->(check:IfStatement)
          WHERE exists(check.condition)
          AND (check.condition CONTAINS 'owner'
               OR check.condition CONTAINS 'user.id'
               OR check.condition CONTAINS 'user_id'
               OR check.condition CONTAINS 'belongs_to')
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               db.name AS db_operation
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="missing_ownership_validation",
                severity="high",
                confidence=0.80,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Missing ownership check in {record['name']}",
                description=(
                    f"Function '{record['name']}' queries database ({record['db_operation']}) "
                    "without verifying that the current user owns the requested resource. "
                    "Users may access resources belonging to other users."
                ),
                context={
                    "dimension_analysis": "WHO owns the resource",
                    "risk": "IDOR - Users can access other users' data"
                },
                evidence={
                    "database_operation": record["db_operation"],
                    "has_ownership_check": False,
                },
            )
            self.findings.append(finding)

    def _detect_privilege_operations_without_authz(self, session, scan_id: str):
        """Detect privilege-sensitive operations without authorization"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method)
        MATCH (func)-[:HAS_CHILD*]->(call:Call)
        WHERE call.name =~ '(?i).*(admin|role|permission|privilege|grant|revoke|promote|demote).*'
        AND NOT func.performs_authorization = true
        AND NOT (func)-[:HAS_CHILD*]->(check:IfStatement)
          WHERE check.condition =~ '(?i).*(admin|permission|authorized|can_).*'
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               call.name AS sensitive_operation
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="privilege_operation_without_authorization",
                severity="critical",
                confidence=0.90,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Privilege operation without authorization in {record['name']}",
                description=(
                    f"Function '{record['name']}' performs privilege-sensitive operation "
                    f"({record['sensitive_operation']}) without authorization checks. "
                    "Any user may be able to modify privileges."
                ),
                context={
                    "dimension_analysis": "WHO can modify privileges",
                    "risk": "Privilege escalation - unauthorized role/permission changes"
                },
                evidence={
                    "sensitive_operation": record["sensitive_operation"],
                    "has_authorization": False,
                },
            )
            self.findings.append(finding)

    def _detect_unverified_user_modifications(self, session, scan_id: str):
        """Detect user object modifications without identity verification"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method OR func:Endpoint)
        AND func.handles_user_input = true
        MATCH (func)-[:HAS_CHILD*]->(call:Call)
        WHERE call.name =~ '(?i).*(update|modify|set|save).*'
        AND NOT (func)-[:HAS_CHILD*]->(check:IfStatement)
          WHERE check.condition =~ '(?i).*(current_user|user.id|user_id|authenticated).*'
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               call.name AS modification_call
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="unverified_user_modification",
                severity="high",
                confidence=0.75,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Unverified user modification in {record['name']}",
                description=(
                    f"Function '{record['name']}' modifies user data ({record['modification_call']}) "
                    "without verifying identity. Users may modify data they shouldn't have access to."
                ),
                context={
                    "dimension_analysis": "WHO can modify user data",
                    "risk": "Users can modify other users' data or their own privileges"
                },
                evidence={
                    "modification_call": record["modification_call"],
                    "has_identity_check": False,
                },
            )
            self.findings.append(finding)
