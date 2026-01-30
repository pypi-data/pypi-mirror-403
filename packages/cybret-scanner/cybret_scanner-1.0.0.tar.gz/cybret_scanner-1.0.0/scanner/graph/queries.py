"""
Cypher queries for vulnerability detection and graph analysis
"""

from typing import List, Dict, Any, Optional
from neo4j import Session


class GraphQueries:
    """Collection of Cypher queries for security analysis"""

    # ==================== IDOR Detection Queries ====================

    FIND_IDOR_PATTERNS = """
    // Find API endpoints that access database without authorization checks
    MATCH (endpoint:Endpoint)-[:HAS_CHILD*]->(db:DatabaseQuery)
    WHERE endpoint.handles_user_input = true
    AND NOT (endpoint)-[:HAS_CHILD*]->(:IfStatement)
      WHERE any(tag IN (:IfStatement).tags WHERE tag = 'security_check')
    RETURN endpoint.name AS vulnerable_endpoint,
           endpoint.file_path AS file_path,
           endpoint.line_start AS line,
           db.name AS database_operation,
           'IDOR: Direct database access without authorization check' AS description
    """

    FIND_MISSING_OWNERSHIP_CHECKS = """
    // Find functions that query objects by ID without ownership validation
    MATCH (func)-[:HAS_CHILD*]->(db:DatabaseQuery)
    WHERE func.handles_user_input = true
    AND (db.name CONTAINS 'get' OR db.name CONTAINS 'find' OR db.name CONTAINS 'query')
    AND NOT (func)-[:HAS_CHILD*]->(check:IfStatement)
      WHERE any(keyword IN ['user', 'owner', 'permission']
        WHERE check.condition CONTAINS keyword)
    RETURN func.name AS function_name,
           func.file_path AS file_path,
           func.line_start AS line,
           'IDOR: Missing ownership check for resource access' AS description
    """

    # ==================== Authentication Bypass Queries ====================

    FIND_AUTH_BYPASS_PATTERNS = """
    // Find endpoints without authentication decorators/middleware
    MATCH (endpoint:Endpoint)
    WHERE endpoint.handles_user_input = true
    AND NOT endpoint.has_decorators
    AND NOT (endpoint)-[:HAS_CHILD*]->(:Call)
      WHERE (:Call).name CONTAINS 'auth' OR (:Call).name CONTAINS 'verify'
    RETURN endpoint.name AS vulnerable_endpoint,
           endpoint.file_path AS file_path,
           endpoint.line_start AS line,
           'AUTH_BYPASS: Endpoint missing authentication check' AS description
    """

    FIND_DEBUG_BYPASSES = """
    // Find conditional bypasses with debug flags
    MATCH (func:Function)-[:HAS_CHILD*]->(if_stmt:IfStatement)
    WHERE if_stmt.condition CONTAINS 'debug'
      OR if_stmt.condition CONTAINS 'test'
      OR if_stmt.condition CONTAINS 'skip'
    AND (func.handles_user_input = true OR func.performs_authentication = true)
    RETURN func.name AS function_name,
           func.file_path AS file_path,
           if_stmt.line_start AS line,
           if_stmt.condition AS bypass_condition,
           'AUTH_BYPASS: Debug/test bypass in authentication logic' AS description
    """

    # ==================== Privilege Escalation Queries ====================

    FIND_PRIVILEGE_ESCALATION = """
    // Find role assignment without proper authorization
    MATCH (func:Function)-[:HAS_CHILD*]->(call:Call)
    WHERE (call.name CONTAINS 'setRole' OR call.name CONTAINS 'setPermission'
           OR call.name CONTAINS 'grant' OR call.name CONTAINS 'elevate')
    AND NOT func.performs_authorization = true
    AND NOT (func)-[:HAS_CHILD*]->(check:IfStatement)
      WHERE check.condition CONTAINS 'admin' OR check.condition CONTAINS 'permission'
    RETURN func.name AS function_name,
           func.file_path AS file_path,
           func.line_start AS line,
           call.name AS privilege_operation,
           'PRIV_ESC: Role/permission modification without authorization' AS description
    """

    # ==================== Data Flow Queries ====================

    TRACE_USER_INPUT_TO_DATABASE = """
    // Trace user input flow to database queries
    MATCH path = (endpoint:Endpoint {handles_user_input: true})
                -[:CALLS*1..5]->(func:Function)
                -[:HAS_CHILD*]->(db:DatabaseQuery)
    WHERE NOT (func.has_security_check = true)
    RETURN endpoint.name AS entry_point,
           [node in nodes(path) | node.name] AS data_flow_path,
           endpoint.file_path AS file_path,
           'Data flow from user input to database without validation' AS description
    LIMIT 50
    """

    FIND_UNVALIDATED_INPUT_CHAINS = """
    // Find chains of function calls from endpoints without input validation
    MATCH path = (endpoint:Endpoint {handles_user_input: true})
                -[:CALLS*1..3]->(target:Function {accesses_database: true})
    WHERE NOT any(node IN nodes(path) WHERE node.has_security_check = true)
    RETURN endpoint.name AS vulnerable_endpoint,
           target.name AS target_function,
           length(path) AS chain_length,
           endpoint.file_path AS file_path,
           'Unvalidated input chain to sensitive operation' AS description
    """

    # ==================== Graph Statistics ====================

    GET_SCAN_STATISTICS = """
    MATCH (s:Scan {scan_id: $scan_id})
    OPTIONAL MATCH (s)-[:SCANNED]->(f:File)
    OPTIONAL MATCH (s)-[:HAS_ENTITY]->(e)
    WHERE e:Function OR e:Method OR e:Endpoint
    OPTIONAL MATCH (s)-[:FOUND_VULNERABILITY]->(v:Vulnerability)
    RETURN s.scan_id AS scan_id,
           s.timestamp AS timestamp,
           s.status AS status,
           count(DISTINCT f) AS file_count,
           count(DISTINCT e) AS entity_count,
           count(DISTINCT v) AS vulnerability_count
    """

    GET_VULNERABILITY_SUMMARY = """
    MATCH (s:Scan {scan_id: $scan_id})-[:FOUND_VULNERABILITY]->(v:Vulnerability)
    RETURN v.type AS vulnerability_type,
           v.severity AS severity,
           count(*) AS count
    ORDER BY count DESC
    """

    # ==================== Specific File Analysis ====================

    ANALYZE_FILE_SECURITY = """
    MATCH (f:File {path: $file_path})-[:CONTAINS*]->(node)
    WHERE node:Function OR node:Method OR node:Endpoint
    OPTIONAL MATCH (node)-[:HAS_CHILD*]->(db:DatabaseQuery)
    OPTIONAL MATCH (node)-[:HAS_CHILD*]->(check:IfStatement)
      WHERE any(tag IN check.tags WHERE tag = 'security_check')
    RETURN node.name AS entity_name,
           node.entity_type AS entity_type,
           node.line_start AS line,
           node.handles_user_input AS handles_input,
           node.performs_authorization AS has_authz,
           count(DISTINCT db) AS database_operations,
           count(DISTINCT check) AS security_checks
    ORDER BY node.line_start
    """

    @staticmethod
    def execute_idor_detection(session: Session, scan_id: str) -> List[Dict[str, Any]]:
        """Execute IDOR detection queries"""
        results = []

        # Pattern 1: Direct database access
        result = session.run(GraphQueries.FIND_IDOR_PATTERNS)
        for record in result:
            results.append(dict(record))

        # Pattern 2: Missing ownership checks
        result = session.run(GraphQueries.FIND_MISSING_OWNERSHIP_CHECKS)
        for record in result:
            results.append(dict(record))

        return results

    @staticmethod
    def execute_auth_bypass_detection(session: Session, scan_id: str) -> List[Dict[str, Any]]:
        """Execute authentication bypass detection queries"""
        results = []

        # Pattern 1: Missing auth decorators
        result = session.run(GraphQueries.FIND_AUTH_BYPASS_PATTERNS)
        for record in result:
            results.append(dict(record))

        # Pattern 2: Debug bypasses
        result = session.run(GraphQueries.FIND_DEBUG_BYPASSES)
        for record in result:
            results.append(dict(record))

        return results

    @staticmethod
    def execute_privilege_escalation_detection(
        session: Session, scan_id: str
    ) -> List[Dict[str, Any]]:
        """Execute privilege escalation detection queries"""
        result = session.run(GraphQueries.FIND_PRIVILEGE_ESCALATION)
        return [dict(record) for record in result]

    @staticmethod
    def execute_data_flow_analysis(session: Session, scan_id: str) -> List[Dict[str, Any]]:
        """Execute data flow analysis queries"""
        results = []

        # Trace user input to database
        result = session.run(GraphQueries.TRACE_USER_INPUT_TO_DATABASE)
        for record in result:
            results.append(dict(record))

        # Find unvalidated input chains
        result = session.run(GraphQueries.FIND_UNVALIDATED_INPUT_CHAINS)
        for record in result:
            results.append(dict(record))

        return results

    @staticmethod
    def get_scan_statistics(session: Session, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get scan statistics"""
        result = session.run(GraphQueries.GET_SCAN_STATISTICS, scan_id=scan_id)
        record = result.single()
        return dict(record) if record else None

    @staticmethod
    def analyze_file(session: Session, file_path: str) -> List[Dict[str, Any]]:
        """Analyze security properties of a specific file"""
        result = session.run(GraphQueries.ANALYZE_FILE_SECURITY, file_path=file_path)
        return [dict(record) for record in result]
