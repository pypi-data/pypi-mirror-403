"""
Insecure Direct Object Reference (IDOR) vulnerability detector
"""

import hashlib
from typing import List
from neo4j import Driver

from scanner.detectors.base import BaseDetector, Vulnerability, VulnerabilitySeverity


class IDORDetector(BaseDetector):
    """
    Detects Insecure Direct Object Reference (IDOR) vulnerabilities

    IDOR occurs when an application provides direct access to objects based on
    user-supplied input without proper authorization checks.

    Detection patterns:
    1. API endpoints that query database directly without auth checks
    2. Functions that access resources by ID without ownership validation
    3. Direct object access patterns in data retrieval
    """

    def __init__(self, driver: Driver, database: str = "neo4j"):
        super().__init__(name="IDORDetector", driver=driver, database=database)

    def detect(self, scan_id: str) -> List[Vulnerability]:
        """Run IDOR detection"""
        self.clear_vulnerabilities()

        with self.driver.session(database=self.database) as session:
            # Pattern 1: Direct database access without authorization
            self._detect_direct_db_access(session, scan_id)

            # Pattern 2: Missing ownership checks
            self._detect_missing_ownership_checks(session, scan_id)

            # Pattern 3: Unprotected resource access
            self._detect_unprotected_resource_access(session, scan_id)

        print(f"[X] IDOR Detection: Found {len(self.vulnerabilities)} vulnerabilities")
        return self.vulnerabilities

    def _detect_direct_db_access(self, session, scan_id: str):
        """Detect API endpoints with direct database access without auth"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(endpoint:Endpoint)
        WHERE endpoint.handles_user_input = true
        AND endpoint.accesses_database = true
        AND NOT endpoint.performs_authorization = true
        RETURN endpoint.name AS endpoint_name,
               endpoint.file_path AS file_path,
               endpoint.line_start AS line_start,
               endpoint.line_end AS line_end,
               endpoint.name AS db_operation,
               endpoint.decorators AS decorators
        LIMIT 100
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            endpoint_name = record["endpoint_name"]
            file_path = record["file_path"]
            line_start = record["line_start"]
            line_end = record["line_end"]
            db_operation = record["db_operation"]
            decorators = record["decorators"] or []

            # Check if there's any auth decorator
            has_auth_decorator = any(
                keyword in str(dec).lower()
                for dec in decorators
                for keyword in ["auth", "login", "permission", "require"]
            )

            if not has_auth_decorator:
                vuln_id = self._generate_vuln_id(file_path, line_start, "IDOR_DIRECT_DB")

                vuln = Vulnerability(
                    vuln_id=vuln_id,
                    vuln_type="IDOR",
                    severity=VulnerabilitySeverity.HIGH,
                    file_path=file_path,
                    line_start=line_start,
                    line_end=line_end,
                    title=f"IDOR: Direct database access in {endpoint_name}",
                    description=(
                        f"The endpoint '{endpoint_name}' performs database operations "
                        f"({db_operation}) without authorization checks. This may allow "
                        "unauthorized users to access or modify data belonging to other users."
                    ),
                    impact=(
                        "An attacker could access, modify, or delete resources belonging "
                        "to other users by manipulating resource identifiers (IDs) in requests. "
                        "This could lead to data breaches, privacy violations, or data integrity issues."
                    ),
                    remediation=(
                        "1. Add authorization checks before database operations\n"
                        "2. Verify that the authenticated user owns or has permission to access the resource\n"
                        "3. Use parameterized queries to prevent SQL injection\n"
                        "4. Implement role-based access control (RBAC)\n"
                        "Example:\n"
                        "  if not user.can_access(resource):\n"
                        "      raise PermissionDenied()"
                    ),
                    function_name=endpoint_name,
                    evidence={
                        "database_operation": db_operation,
                        "has_auth_decorator": False,
                        "has_security_check": False,
                    },
                    cwe="CWE-639",  # Authorization Bypass Through User-Controlled Key
                    detector_name=self.name,
                    confidence=0.85,
                )

                self.vulnerabilities.append(vuln)

    def _detect_missing_ownership_checks(self, session, scan_id: str):
        """Detect resource access by ID without ownership validation"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(func)
        WHERE (func:Function OR func:Method OR func:Endpoint)
        AND func.handles_user_input = true
        AND func.accesses_database = true
        AND NOT func.performs_authorization = true
        RETURN func.name AS function_name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               func.name AS query_operation,
               func.has_security_check AS has_security_check
        LIMIT 100
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            function_name = record["function_name"]
            file_path = record["file_path"]
            line_start = record["line_start"]
            line_end = record["line_end"]
            query_operation = record["query_operation"]

            vuln_id = self._generate_vuln_id(file_path, line_start, "IDOR_MISSING_OWNER")

            vuln = Vulnerability(
                vuln_id=vuln_id,
                vuln_type="IDOR",
                severity=VulnerabilitySeverity.HIGH,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                title=f"IDOR: Missing ownership check in {function_name}",
                description=(
                    f"The function '{function_name}' retrieves resources ({query_operation}) "
                    "based on user input without verifying ownership. Users may be able to "
                    "access resources belonging to other users by guessing or enumerating IDs."
                ),
                impact=(
                    "Unauthorized access to sensitive user data. Attackers can view, modify, "
                    "or delete resources by manipulating object identifiers, leading to "
                    "privacy breaches and potential data loss."
                ),
                remediation=(
                    "1. Always verify resource ownership before retrieval:\n"
                    "   resource = get_resource(resource_id)\n"
                    "   if resource.owner_id != current_user.id:\n"
                    "       raise Forbidden('Access denied')\n\n"
                    "2. Use indirect object references (map user-specific IDs)\n"
                    "3. Implement access control lists (ACLs)\n"
                    "4. Filter queries by user: query.filter(owner=current_user)"
                ),
                function_name=function_name,
                evidence={
                    "query_operation": query_operation,
                    "missing_ownership_check": True,
                },
                cwe="CWE-639",
                detector_name=self.name,
                confidence=0.80,
            )

            self.vulnerabilities.append(vuln)

    def _detect_unprotected_resource_access(self, session, scan_id: str):
        """Detect data flow from user input to database without validation"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(endpoint:Endpoint)
        WHERE endpoint.handles_user_input = true
        MATCH path = (endpoint)-[:CALLS*1..4]->(func)
        WHERE func.accesses_database = true
        AND NOT any(node IN nodes(path) WHERE node.has_security_check = true)
        RETURN endpoint.name AS endpoint_name,
               endpoint.file_path AS file_path,
               endpoint.line_start AS line_start,
               func.name AS target_function,
               length(path) AS path_length
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            endpoint_name = record["endpoint_name"]
            file_path = record["file_path"]
            line_start = record["line_start"]
            target_function = record["target_function"]
            path_length = record["path_length"]

            vuln_id = self._generate_vuln_id(
                file_path, line_start, "IDOR_UNPROTECTED_FLOW"
            )

            vuln = Vulnerability(
                vuln_id=vuln_id,
                vuln_type="IDOR",
                severity=VulnerabilitySeverity.MEDIUM,
                file_path=file_path,
                line_start=line_start,
                title=f"IDOR: Unvalidated data flow from {endpoint_name}",
                description=(
                    f"User input from '{endpoint_name}' flows through {path_length} "
                    f"function calls to '{target_function}' which accesses the database, "
                    "without security checks along the way. This may allow unauthorized "
                    "resource access."
                ),
                impact=(
                    "Potential unauthorized access to database resources. The lack of "
                    "security checks in the call chain means user-supplied identifiers "
                    "reach database operations without validation."
                ),
                remediation=(
                    "1. Add authorization checks at the entry point (endpoint)\n"
                    "2. Validate user permissions in the database access function\n"
                    "3. Implement defense in depth with checks at multiple layers\n"
                    "4. Use a middleware/decorator pattern for consistent auth checks"
                ),
                function_name=endpoint_name,
                evidence={
                    "target_function": target_function,
                    "call_chain_length": path_length,
                    "has_intermediate_checks": False,
                },
                cwe="CWE-639",
                detector_name=self.name,
                confidence=0.70,
            )

            self.vulnerabilities.append(vuln)

    def _generate_vuln_id(self, file_path: str, line: int, pattern: str) -> str:
        """Generate unique vulnerability ID"""
        content = f"{file_path}:{line}:{pattern}"
        return f"IDOR-{hashlib.md5(content.encode()).hexdigest()[:12]}"
