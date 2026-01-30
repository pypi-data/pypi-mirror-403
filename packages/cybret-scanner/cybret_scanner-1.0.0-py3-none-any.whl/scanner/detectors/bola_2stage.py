"""
2-Stage BOLA (Broken Object Level Authorization) Detector

Stage A: Surface detection (broad, high recall)
Stage B: Evidence scoring (precision + explainability) with sigmoid model
"""

import hashlib
import math
from typing import List, Dict, Any, Optional
from neo4j import Driver

from scanner.detectors.base import BaseDetector, Vulnerability, VulnerabilitySeverity
from scanner.detectors.guardrails import DetectorGuardrails


class BOLA2StageDetector(BaseDetector):
    """
    2-Stage BOLA Detector
    
    Stage A: Identifies potential BOLA surfaces (endpoints with user input + DB access)
    Stage B: Scores findings based on evidence (authz checks, guards, sensitive resources)
    
    Output:
    - POSSIBLE_BOLA_SURFACE (confidence 0.40-0.65): Stage A candidates
    - LIKELY_BOLA (confidence 0.70+): Stage B high-confidence findings
    """

    def __init__(self, driver: Driver, database: str = "neo4j"):
        super().__init__(name="BOLA2StageDetector", driver=driver, database=database)

    def detect(self, scan_id: str) -> List[Vulnerability]:
        """Run 2-stage BOLA detection with guardrails"""
        self.clear_vulnerabilities()

        with self.driver.session(database=self.database) as session:
            # Validate graph invariants
            try:
                DetectorGuardrails.validate_graph_invariants(session, scan_id)
                DetectorGuardrails.validate_golden_files(session, scan_id)
            except RuntimeError as e:
                print(f"[!] Guardrail check failed: {e}")
                raise
            
            # Stage A: Surface detection
            stage_a_findings = self._stage_a_surface_detection(session, scan_id)
            
            # Stage B: Evidence scoring
            stage_b_findings = self._stage_b_evidence_scoring(session, scan_id)
            
            # Combine findings (Stage B overrides Stage A for same endpoints)
            self._merge_findings(stage_a_findings, stage_b_findings)

        print(f"[X] BOLA 2-Stage Detection: Found {len(self.vulnerabilities)} vulnerabilities")
        print(f"    Stage A (POSSIBLE_BOLA_SURFACE): {sum(1 for v in self.vulnerabilities if v.vuln_type == 'POSSIBLE_BOLA_SURFACE')}")
        print(f"    Stage B (LIKELY_BOLA): {sum(1 for v in self.vulnerabilities if v.vuln_type == 'LIKELY_BOLA')}")
        
        return self.vulnerabilities

    def _stage_a_surface_detection(self, session, scan_id: str) -> List[Dict[str, Any]]:
        """
        Stage A: Surface detection (broad, high recall)
        
        Goal: Which endpoints look like they could be BOLA surfaces?
        
        Criteria:
        - Endpoint handles user input
        - Endpoint accesses database
        - Optionally: has_security_check = false
        
        Output: POSSIBLE_BOLA_SURFACE with baseline confidence ~0.40-0.65
        """
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(e:Endpoint)
        WHERE coalesce(e.handles_user_input, false) = true
          AND coalesce(e.accesses_database, false) = true
        RETURN
          e.name        AS endpoint_name,
          e.file_path   AS file_path,
          e.line_start  AS line_start,
          e.line_end    AS line_end,
          0.55          AS base_confidence,
          'POSSIBLE_BOLA_SURFACE' AS finding_type
        ORDER BY e.file_path, e.line_start
        """

        result = session.run(query, scan_id=scan_id)
        return [dict(record) for record in result]

    def _stage_b_evidence_scoring(self, session, scan_id: str) -> List[Dict[str, Any]]:
        """
        Stage B: Evidence scoring (precision + explainability)
        
        Goal: Is there evidence of missing authz/ownership checks?
        
        Scores based on:
        - Negative evidence (reduces risk): authz guards, middleware, ownership checks
        - Positive evidence (increases risk): no guards, sensitive resources, DB access patterns
        
        Output: LIKELY_BOLA when score >= 0.70
        """
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(e:Endpoint)
        WHERE coalesce(e.handles_user_input, false) = true
          AND coalesce(e.accesses_database, false) = true

        // Reachable nodes (endpoint + functions it calls)
        OPTIONAL MATCH p=(e)-[:CALLS*0..6]->(f)
        WITH e, collect(DISTINCT f) AS reachable, collect(DISTINCT p) AS paths

        WITH e, reachable,
          // Evidence counts
          size([x IN reachable WHERE coalesce(x.performs_authorization, false) = true]) AS authz_hits,
          size([x IN reachable WHERE coalesce(x.performs_authentication, false) = true]) AS authn_hits,
          size([x IN reachable WHERE coalesce(x.has_security_check, false) = true]) AS guard_hits,
          size([x IN reachable WHERE coalesce(x.accesses_database, false) = true]) AS db_hits,
          // Object ID signal (0-2)
          coalesce(e.object_id_signal, 0) AS object_id_signal,
          // Middleware auth
          CASE WHEN coalesce(e.has_auth_middleware, false) THEN 1 ELSE 0 END AS auth_mw_present,
          // Simple heuristic: sensitive naming
          CASE WHEN toLower(e.file_path) CONTAINS 'wallet' OR toLower(e.name) CONTAINS 'wallet' THEN 1 ELSE 0 END AS sensitive_wallet,
          CASE WHEN toLower(e.file_path) CONTAINS 'admin'  OR toLower(e.name) CONTAINS 'admin'  THEN 1 ELSE 0 END AS sensitive_admin,
          CASE WHEN toLower(e.file_path) CONTAINS 'payment' OR toLower(e.name) CONTAINS 'payment' THEN 1 ELSE 0 END AS sensitive_payment,
          CASE WHEN toLower(e.file_path) CONTAINS 'basket' OR toLower(e.name) CONTAINS 'basket' THEN 1 ELSE 0 END AS sensitive_basket

        // Convert to binary features for sigmoid model
        WITH e, reachable,
          CASE WHEN authz_hits = 0 THEN 1 ELSE 0 END AS authz_missing,
          CASE WHEN authn_hits = 0 THEN 1 ELSE 0 END AS authn_missing,
          CASE WHEN guard_hits = 0 THEN 1 ELSE 0 END AS guard_missing,
          CASE WHEN db_hits > 0 THEN 1 ELSE 0 END AS db_present,
          object_id_signal,
          auth_mw_present,
          sensitive_wallet,
          sensitive_admin,
          sensitive_payment,
          sensitive_basket

        RETURN
          e.name AS endpoint_name,
          e.file_path AS file_path,
          e.line_start AS line_start,
          e.line_end AS line_end,
          {
            authz_missing: authz_missing,
            authn_missing: authn_missing,
            guard_missing: guard_missing,
            db_present: db_present,
            object_id_signal: object_id_signal,
            auth_mw_present: auth_mw_present,
            sensitive_wallet: sensitive_wallet,
            sensitive_admin: sensitive_admin,
            sensitive_payment: sensitive_payment,
            sensitive_basket: sensitive_basket
          } AS evidence
        ORDER BY file_path, line_start
        """

        result = session.run(query, scan_id=scan_id)
        return [dict(record) for record in result]

    def _get_evidence_paths(self, session, scan_id: str, endpoint_name: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Get evidence paths showing call chain from endpoint to DB access
        
        Returns up to 3 shortest paths when no authz hits exist
        """
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(e:Endpoint)
        WHERE e.name = $endpoint_name
          AND e.file_path = $file_path
          AND coalesce(e.handles_user_input, false) = true
          AND coalesce(e.accesses_database, false) = true

        // Only focus on cases with no authz evidence in reachable graph
        OPTIONAL MATCH (e)-[:CALLS*0..6]->(f_authz)
        WHERE coalesce(f_authz.performs_authorization, false) = true
        WITH e, count(DISTINCT f_authz) AS authz_count
        WHERE authz_count = 0

        MATCH p=shortestPath((e)-[:CALLS*0..6]->(f_db))
        WHERE coalesce(f_db.accesses_database, false) = true

        RETURN
          [n IN nodes(p) | {
            type: labels(n)[0], 
            name: coalesce(n.name, ''), 
            line: coalesce(n.line_start, null)
          }] AS path_nodes,
          [r IN relationships(p) | type(r)] AS path_edges
        LIMIT 3
        """

        result = session.run(query, scan_id=scan_id, endpoint_name=endpoint_name, file_path=file_path)
        return [dict(record) for record in result]

    def _compute_sigmoid_confidence(self, evidence: Dict[str, Any]) -> float:
        """
        Compute confidence using sigmoid model
        
        confidence = 1 / (1 + exp(-x))
        where x = b + Σ(w_i * feature_i)
        
        Weights tuned for Juice Shop data distribution
        """
        # Bias
        b = -1.1
        
        # Weights (tuned for discrimination)
        w_authz_missing = 1.0
        w_authn_missing = 0.4
        w_guard_missing = 0.7
        w_db_present = 0.3
        w_object_id_signal = 0.6  # per point (0-2)
        w_auth_mw_present = -1.3  # negative = reduces risk (strong)
        w_sensitive_wallet = 0.25
        w_sensitive_payment = 0.35
        w_sensitive_admin = 0.20
        w_sensitive_basket = 0.15
        
        # Compute linear combination
        x = b
        x += w_authz_missing * evidence.get("authz_missing", 0)
        x += w_authn_missing * evidence.get("authn_missing", 0)
        x += w_guard_missing * evidence.get("guard_missing", 0)
        x += w_db_present * evidence.get("db_present", 0)
        x += w_object_id_signal * evidence.get("object_id_signal", 0)
        x += w_auth_mw_present * evidence.get("auth_mw_present", 0)
        x += w_sensitive_wallet * evidence.get("sensitive_wallet", 0)
        x += w_sensitive_payment * evidence.get("sensitive_payment", 0)
        x += w_sensitive_admin * evidence.get("sensitive_admin", 0)
        x += w_sensitive_basket * evidence.get("sensitive_basket", 0)
        
        # Sigmoid
        confidence = 1.0 / (1.0 + math.exp(-x))
        
        return confidence
    
    def _merge_findings(self, stage_a: List[Dict], stage_b: List[Dict]):
        """
        Merge Stage A and Stage B findings
        
        Stage B overrides Stage A for the same endpoint
        Compute confidence using sigmoid model in Python
        """
        # Index Stage B findings by (file_path, line_start)
        stage_b_index = {
            (f["file_path"], f["line_start"]): f
            for f in stage_b
        }

        # Process all findings
        all_findings = {}
        
        # Add Stage B findings first (higher priority)
        for finding in stage_b:
            key = (finding["file_path"], finding["line_start"])
            # Compute confidence using sigmoid
            evidence = finding["evidence"]
            confidence = self._compute_sigmoid_confidence(evidence)
            finding["confidence"] = confidence
            finding["finding_type"] = "LIKELY_BOLA" if confidence >= 0.78 else "POSSIBLE_BOLA_SURFACE"
            all_findings[key] = finding
        
        # Add Stage A findings only if not already in Stage B
        for finding in stage_a:
            key = (finding["file_path"], finding["line_start"])
            if key not in all_findings:
                all_findings[key] = finding

        # Sort by confidence (descending)
        sorted_findings = sorted(all_findings.values(), key=lambda f: f.get("confidence", 0.55), reverse=True)

        # Convert to Vulnerability objects
        for finding in sorted_findings:
            self._create_vulnerability_from_finding(finding)

    def _create_vulnerability_from_finding(self, finding: Dict[str, Any]):
        """Create Vulnerability object from finding dict"""
        endpoint_name = finding["endpoint_name"]
        file_path = finding["file_path"]
        line_start = finding["line_start"]
        line_end = finding.get("line_end", line_start)
        confidence = finding.get("confidence", finding.get("base_confidence", 0.55))
        finding_type = finding["finding_type"]
        evidence = finding.get("evidence", {})

        vuln_id = self._generate_vuln_id(file_path, line_start, finding_type)

        # Determine priority bucket and severity
        if confidence >= 0.92:
            priority_bucket = "Critical"
            severity = VulnerabilitySeverity.CRITICAL
        elif confidence >= 0.78:
            priority_bucket = "Likely"
            severity = VulnerabilitySeverity.HIGH
        elif confidence >= 0.70:
            priority_bucket = "Review"
            severity = VulnerabilitySeverity.MEDIUM
        else:
            priority_bucket = "Low"
            severity = VulnerabilitySeverity.MEDIUM

        # Build description and "why" explanation
        why_explanation = self._generate_why_explanation(evidence)
        
        if finding_type == "LIKELY_BOLA":
            description = self._build_stage_b_description(endpoint_name, evidence)
            title = f"BOLA: {priority_bucket} - Authorization bypass in {endpoint_name}"
        else:
            description = self._build_stage_a_description(endpoint_name)
            title = f"BOLA: {priority_bucket} - Possible authorization bypass in {endpoint_name}"
        
        # Add priority bucket and why to evidence
        evidence["priority_bucket"] = priority_bucket
        evidence["why"] = why_explanation

        vuln = Vulnerability(
            vuln_id=vuln_id,
            vuln_type=finding_type,
            severity=severity,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            title=title,
            description=description,
            impact=(
                "An attacker could access, modify, or delete resources belonging "
                "to other users by manipulating resource identifiers (IDs) in requests. "
                "This could lead to data breaches, privacy violations, or data integrity issues."
            ),
            remediation=(
                "1. Add authorization checks before database operations\n"
                "2. Verify that the authenticated user owns or has permission to access the resource\n"
                "3. Implement ownership validation (e.g., WHERE userId = currentUser.id)\n"
                "4. Use middleware for consistent authorization enforcement\n"
                "Example:\n"
                "  if (!await canAccessResource(req.user.id, resourceId)) {\n"
                "    return res.status(403).json({error: 'Forbidden'});\n"
                "  }"
            ),
            function_name=endpoint_name,
            code_snippet=None,
            evidence=evidence,
            cwe="CWE-639",
            detector_name=self.name,
            confidence=confidence,
        )

        self.vulnerabilities.append(vuln)

    def _build_stage_a_description(self, endpoint_name: str) -> str:
        """Build description for Stage A finding"""
        return (
            f"The endpoint '{endpoint_name}' handles user input and performs database operations. "
            f"Stage A surface detection identified this as a potential BOLA vulnerability. "
            f"Further analysis (Stage B) is needed to confirm the presence of authorization checks."
        )

    def _build_stage_b_description(self, endpoint_name: str, evidence: Dict[str, Any]) -> str:
        """Build description for Stage B finding with evidence"""
        desc_parts = [
            f"The endpoint '{endpoint_name}' performs database operations without proper authorization checks."
        ]

        # Add evidence details
        if evidence.get("authz_hits", 0) == 0:
            desc_parts.append("No authorization checks were found in the reachable call graph.")
        
        if evidence.get("guard_hits", 0) == 0:
            desc_parts.append("No security guard functions were detected.")
        
        if evidence.get("authn_hits", 0) == 0:
            desc_parts.append("No authentication checks were found.")

        # Mention sensitive resources
        sensitive = []
        if evidence.get("sensitive_wallet"):
            sensitive.append("wallet")
        if evidence.get("sensitive_admin"):
            sensitive.append("admin")
        if evidence.get("sensitive_payment"):
            sensitive.append("payment")
        if evidence.get("sensitive_basket"):
            sensitive.append("basket")
        
        if sensitive:
            desc_parts.append(f"This endpoint handles sensitive resources: {', '.join(sensitive)}.")

        return " ".join(desc_parts)

    def _generate_why_explanation(self, evidence: Dict[str, Any]) -> str:
        """
        Generate deterministic "why" explanation from evidence
        
        Makes findings explainable and non-black-box
        """
        parts = []
        
        # Object ID signal
        obj_id = evidence.get("object_id_signal", 0)
        if obj_id == 2:
            parts.append("Endpoint accesses object identifiers from request (req.params/query/body.*id)")
        elif obj_id == 1:
            parts.append("Endpoint shows medium object-ID patterns")
        
        # Database access
        if evidence.get("db_present", 0):
            parts.append("performs database operations")
        
        # Missing guards
        missing = []
        if evidence.get("authz_missing", 0):
            missing.append("authorization")
        if evidence.get("guard_missing", 0):
            missing.append("security guards")
        if evidence.get("authn_missing", 0):
            missing.append("authentication")
        
        if missing:
            parts.append(f"without detected {' or '.join(missing)}")
        
        # Middleware
        if evidence.get("auth_mw_present", 0):
            parts.append("but appears protected by middleware")
        else:
            parts.append("and no auth middleware detected")
        
        # Sensitive resources
        sensitive = []
        if evidence.get("sensitive_wallet"):
            sensitive.append("wallet")
        if evidence.get("sensitive_payment"):
            sensitive.append("payment")
        if evidence.get("sensitive_basket"):
            sensitive.append("basket")
        if evidence.get("sensitive_admin"):
            sensitive.append("admin")
        
        if sensitive:
            parts.append(f"on sensitive resource ({', '.join(sensitive)})")
        
        # Combine
        explanation = "; ".join(parts).capitalize() + "."
        return explanation
    
    def _generate_vuln_id(self, file_path: str, line: int, pattern: str) -> str:
        """Generate unique vulnerability ID"""
        content = f"{file_path}:{line}:{pattern}"
        return f"BOLA-{hashlib.md5(content.encode()).hexdigest()[:12]}"
