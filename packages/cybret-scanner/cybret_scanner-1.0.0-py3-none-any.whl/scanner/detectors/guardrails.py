"""
Trust Guardrails for BOLA Detector

Validates graph invariants before detection to prevent nonsense runs
"""

from typing import Dict, Any
from neo4j import Session


class DetectorGuardrails:
    """Validates graph state before running detectors"""
    
    @staticmethod
    def validate_graph_invariants(session: Session, scan_id: str) -> Dict[str, Any]:
        """
        Validate graph invariants before detection
        
        Checks:
        - Scan has entities
        - Endpoints with user input exist
        - Endpoints with DB access exist
        - Call relationships exist
        
        Returns: Dict with validation results and counts
        Raises: RuntimeError if critical invariants fail
        """
        results = {}
        
        # Check 1: Scan has entities
        result = session.run("""
            MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(e:Endpoint)
            RETURN count(e) AS endpoint_count
        """, scan_id=scan_id)
        
        record = result.single()
        endpoint_count = record["endpoint_count"]
        results["endpoint_count"] = endpoint_count
        
        if endpoint_count == 0:
            raise RuntimeError(
                f"Graph invariant failed: No endpoints found for scan {scan_id}. "
                "This indicates parsing or graph building issues."
            )
        
        # Check 2: Endpoints with user input
        result = session.run("""
            MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(e:Endpoint)
            WHERE e.handles_user_input = true
            RETURN count(e) AS user_input_count
        """, scan_id=scan_id)
        
        record = result.single()
        user_input_count = record["user_input_count"]
        results["user_input_count"] = user_input_count
        
        if user_input_count == 0:
            raise RuntimeError(
                f"Graph invariant failed: No endpoints with user input found for scan {scan_id}. "
                "This indicates entity extraction issues."
            )
        
        # Check 3: Endpoints with DB access
        result = session.run("""
            MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(e:Endpoint)
            WHERE e.accesses_database = true
            RETURN count(e) AS db_access_count
        """, scan_id=scan_id)
        
        record = result.single()
        db_access_count = record["db_access_count"]
        results["db_access_count"] = db_access_count
        
        if db_access_count == 0:
            print(
                f"Warning: No endpoints with database access found for scan {scan_id}. "
                "BOLA detection may not find vulnerabilities."
            )
        
        # Check 4: Call relationships exist
        result = session.run("""
            MATCH ()-[r:CALLS]->()
            RETURN count(r) AS calls_count
        """)
        
        record = result.single()
        calls_count = record["calls_count"]
        results["calls_count"] = calls_count
        
        # This is a warning, not a failure
        if calls_count == 0:
            print(
                "Warning: No CALLS relationships found. "
                "Reachability analysis will be limited."
            )
        
        print(f"[X] Graph invariants validated:")
        print(f"    Endpoints: {endpoint_count}")
        print(f"    With user input: {user_input_count}")
        print(f"    With DB access: {db_access_count}")
        print(f"    CALLS relationships: {calls_count}")
        
        return results
    
    @staticmethod
    def validate_golden_files(session: Session, scan_id: str) -> bool:
        """
        Validate golden file regression tests
        
        Ensures known Juice Shop files have expected evidence:
        - routes/basket.ts has object_id_signal >= 1
        - routes/wallet.ts has object_id_signal = 2
        - Some route has auth_mw_present = 1
        
        Returns: True if all pass, False otherwise
        """
        all_passed = True
        
        # Test 1: basket.ts has object_id_signal >= 1
        result = session.run("""
            MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(e:Endpoint)
            WHERE e.file_path CONTAINS 'basket.ts'
            AND e.object_id_signal >= 1
            RETURN count(e) AS count
        """, scan_id=scan_id)
        
        record = result.single()
        if record["count"] == 0:
            print("WARNING: Golden file test failed - basket.ts should have object_id_signal >= 1")
            all_passed = False
        
        # Test 2: wallet.ts has object_id_signal = 2
        result = session.run("""
            MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(e:Endpoint)
            WHERE e.file_path CONTAINS 'wallet.ts'
            AND e.object_id_signal = 2
            RETURN count(e) AS count
        """, scan_id=scan_id)
        
        record = result.single()
        if record["count"] == 0:
            print("WARNING: Golden file test failed - wallet.ts should have object_id_signal = 2")
            all_passed = False
        
        # Test 3: Some route has auth_mw_present = 1
        result = session.run("""
            MATCH (s:Scan {scan_id: $scan_id})-[:HAS_ENTITY]->(e:Endpoint)
            WHERE e.has_auth_middleware = true
            RETURN count(e) AS count
        """, scan_id=scan_id)
        
        record = result.single()
        if record["count"] == 0:
            print("WARNING: Golden file test failed - Expected some endpoints with auth_mw_present = 1")
            all_passed = False
        
        if all_passed:
            print("[X] Golden file regression tests passed")
        
        return all_passed
