"""
Authentication Bypass vulnerability detector
"""

import hashlib
from typing import List
from neo4j import Driver

from scanner.detectors.base import BaseDetector, Vulnerability, VulnerabilitySeverity


class AuthBypassDetector(BaseDetector):
    """
    Detects Authentication Bypass vulnerabilities

    Authentication bypass occurs when security checks can be circumvented,
    allowing unauthorized access to protected resources.

    Detection patterns:
    1. API endpoints without authentication decorators/middleware
    2. Conditional bypasses (debug flags, test modes)
    3. Missing authentication in sensitive operations
    4. Weak authentication logic
    """

    def __init__(self, driver: Driver, database: str = "neo4j"):
        super().__init__(name="AuthBypassDetector", driver=driver, database=database)

    def detect(self, scan_id: str) -> List[Vulnerability]:
        """Run authentication bypass detection"""
        self.clear_vulnerabilities()

        with self.driver.session(database=self.database) as session:
            # Pattern 1: Missing authentication decorators
            self._detect_missing_auth_decorators(session, scan_id)

            # Pattern 2: Debug/test bypasses
            self._detect_debug_bypasses(session, scan_id)

            # Pattern 3: Weak authentication logic
            self._detect_weak_auth_logic(session, scan_id)

        print(
            f"[X] Auth Bypass Detection: Found {len(self.vulnerabilities)} vulnerabilities"
        )
        return self.vulnerabilities

    def _detect_missing_auth_decorators(self, session, scan_id: str):
        """Detect endpoints without authentication"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(endpoint)
        WHERE (endpoint:Endpoint OR endpoint:Function)
        AND endpoint.handles_user_input = true
        AND toLower(endpoint.name) CONTAINS 'admin'
        AND NOT endpoint.performs_authentication = true
        RETURN endpoint.name AS endpoint_name,
               endpoint.file_path AS file_path,
               endpoint.line_start AS line_start,
               endpoint.line_end AS line_end,
               endpoint.is_public AS is_public
        LIMIT 100
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            endpoint_name = record["endpoint_name"]
            file_path = record["file_path"]
            line_start = record["line_start"]
            line_end = record["line_end"]
            is_public = record["is_public"]

            vuln_id = self._generate_vuln_id(file_path, line_start, "AUTH_MISSING")

            severity = (
                VulnerabilitySeverity.CRITICAL
                if not is_public
                else VulnerabilitySeverity.HIGH
            )

            vuln = Vulnerability(
                vuln_id=vuln_id,
                vuln_type="AUTH_BYPASS",
                severity=severity,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                title=f"Authentication Bypass: Missing auth in {endpoint_name}",
                description=(
                    f"The endpoint '{endpoint_name}' handles user input but has no "
                    "authentication decorators or checks. This allows unauthenticated "
                    "users to access the endpoint and potentially perform unauthorized actions."
                ),
                impact=(
                    "Unauthenticated users can access protected functionality. This could "
                    "lead to unauthorized data access, privilege escalation, or system compromise. "
                    "Attackers can invoke the endpoint without providing credentials."
                ),
                remediation=(
                    "1. Add authentication decorator/middleware:\n"
                    "   Python/Flask: @login_required\n"
                    "   Express.js: app.use(authMiddleware)\n"
                    "   Spring: @PreAuthorize(\"isAuthenticated()\")\n\n"
                    "2. Verify authentication at the start of the function:\n"
                    "   if not current_user.is_authenticated:\n"
                    "       raise Unauthorized('Login required')\n\n"
                    "3. Use framework-level authentication guards\n"
                    "4. Implement JWT or session-based authentication"
                ),
                function_name=endpoint_name,
                evidence={
                    "has_decorators": False,
                    "has_auth_calls": False,
                    "is_public_endpoint": is_public,
                },
                cwe="CWE-306",  # Missing Authentication for Critical Function
                detector_name=self.name,
                confidence=0.90,
            )

            self.vulnerabilities.append(vuln)

    def _detect_debug_bypasses(self, session, scan_id: str):
        """Detect debug/test bypasses in authentication logic"""
        # Simplified query - just look for functions with 'login' or 'auth' in name
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(func)
        WHERE (func:Function OR func:Endpoint)
        AND (toLower(func.name) CONTAINS 'login' OR toLower(func.name) CONTAINS 'auth')
        AND func.handles_user_input = true
        RETURN func.name AS function_name,
               func.file_path AS file_path,
               func.line_start AS func_line,
               func.line_start AS condition_line,
               'potential_bypass' AS bypass_condition
        LIMIT 100
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            function_name = record["function_name"]
            file_path = record["file_path"]
            func_line = record["func_line"]
            condition_line = record["condition_line"]
            bypass_condition = record["bypass_condition"]

            vuln_id = self._generate_vuln_id(file_path, condition_line, "AUTH_DEBUG_BYPASS")

            vuln = Vulnerability(
                vuln_id=vuln_id,
                vuln_type="AUTH_BYPASS",
                severity=VulnerabilitySeverity.CRITICAL,
                file_path=file_path,
                line_start=condition_line,
                title=f"Authentication Bypass: Debug backdoor in {function_name}",
                description=(
                    f"The function '{function_name}' contains a debug/test bypass condition: "
                    f"'{bypass_condition}'. This allows authentication to be skipped when "
                    "debug mode is enabled or specific parameters are provided, creating a backdoor."
                ),
                impact=(
                    "CRITICAL: Debug bypasses in production can allow complete authentication "
                    "bypass. Attackers who discover the bypass condition can gain unauthorized "
                    "access to the system without valid credentials. This is often exploited "
                    "by testing query parameters like ?debug=true or ?test=1."
                ),
                remediation=(
                    "1. REMOVE debug bypasses from production code immediately\n"
                    "2. Use environment variables to control debug features, never request parameters\n"
                    "3. Implement proper feature flags with access controls\n"
                    "4. Use separate test environments instead of runtime bypasses\n"
                    "5. Code review checklist should include 'no auth bypasses'\n\n"
                    "Example UNSAFE code:\n"
                    "  if request.args.get('debug') == 'true':\n"
                    "      return allow_access()  # ❌ DANGEROUS\n\n"
                    "Safe alternative:\n"
                    "  if os.environ.get('ENV') == 'development':\n"
                    "      # Only in dev environment, not controllable by requests"
                ),
                function_name=function_name,
                code_snippet=bypass_condition,
                evidence={
                    "bypass_condition": bypass_condition,
                    "condition_line": condition_line,
                    "function_line": func_line,
                },
                cwe="CWE-489",  # Active Debug Code
                detector_name=self.name,
                confidence=0.95,
            )

            self.vulnerabilities.append(vuln)

    def _detect_weak_auth_logic(self, session, scan_id: str):
        """Detect weak or incomplete authentication logic"""
        # Simplified query
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(func)
        WHERE (func:Function OR func:Method OR func:Endpoint)
        AND func.performs_authentication = true
        RETURN func.name AS function_name,
               func.file_path AS file_path,
               func.line_start AS func_line,
               func.line_start AS condition_line,
               'weak_auth' AS auth_condition
        LIMIT 100
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            function_name = record["function_name"]
            file_path = record["file_path"]
            func_line = record["func_line"]
            condition_line = record["condition_line"]
            auth_condition = record["auth_condition"]

            # Check if condition has OR logic that might allow bypass
            if any(
                keyword in auth_condition.lower()
                for keyword in ["true", "1", "null", "none", "undefined"]
            ):
                vuln_id = self._generate_vuln_id(
                    file_path, condition_line, "AUTH_WEAK_LOGIC"
                )

                vuln = Vulnerability(
                    vuln_id=vuln_id,
                    vuln_type="AUTH_BYPASS",
                    severity=VulnerabilitySeverity.HIGH,
                    file_path=file_path,
                    line_start=condition_line,
                    title=f"Authentication Bypass: Weak auth logic in {function_name}",
                    description=(
                        f"The function '{function_name}' has authentication logic with OR "
                        f"conditions that may allow bypass: '{auth_condition}'. OR logic in "
                        "authentication checks can create unintended bypass paths."
                    ),
                    impact=(
                        "Weak authentication logic may allow attackers to bypass security "
                        "checks by exploiting alternative code paths. OR conditions in auth "
                        "checks are particularly dangerous as they provide multiple ways to "
                        "satisfy the condition, potentially including unintended paths."
                    ),
                    remediation=(
                        "1. Use AND logic for authentication requirements, not OR\n"
                        "2. Ensure all conditions must be satisfied for authentication\n"
                        "3. Avoid truthy checks like 'if user or is_admin' - be explicit\n"
                        "4. Review logic carefully:\n"
                        "   BAD:  if token or is_dev:  # ❌\n"
                        "   GOOD: if token and verify_token(token):  # [X]\n\n"
                        "5. Write unit tests for all authentication edge cases"
                    ),
                    function_name=function_name,
                    code_snippet=auth_condition,
                    evidence={
                        "auth_condition": auth_condition,
                        "has_or_logic": True,
                    },
                    cwe="CWE-287",  # Improper Authentication
                    detector_name=self.name,
                    confidence=0.75,
                )

                self.vulnerabilities.append(vuln)

    def _generate_vuln_id(self, file_path: str, line: int, pattern: str) -> str:
        """Generate unique vulnerability ID"""
        content = f"{file_path}:{line}:{pattern}"
        return f"AUTH-{hashlib.md5(content.encode()).hexdigest()[:12]}"
