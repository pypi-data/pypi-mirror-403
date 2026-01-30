"""
Intent Inference Engine

Automatically infers security intent from code patterns:
- Ownership invariants (statistical analysis)
- State transitions (semantic analysis)
- Trust boundaries (data flow analysis)

This is the foundation for next-level detection.
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
from scanner.intent.graph_schema import OwnershipInvariant, Resource, State
import re


@dataclass
class InferenceResult:
    """Result of intent inference"""
    ownership_invariants: List[OwnershipInvariant]
    resources: List[Resource]
    states: List[State]
    confidence_stats: Dict[str, float]


class IntentInferenceEngine:
    """
    Infers security intent from code

    Uses statistical and semantic analysis to discover:
    1. Ownership patterns (95% of endpoints check user_id == owner_id)
    2. State transitions (order.status: pending → paid → shipped)
    3. Trust boundaries (user input → database)
    """

    def __init__(self, driver, database: str = "neo4j"):
        self.driver = driver
        self.database = database

    def infer_all(self, scan_id: str) -> InferenceResult:
        """
        Run all inference analyses

        Args:
            scan_id: Scan identifier

        Returns:
            InferenceResult with all inferred intent
        """
        ownership_invariants = self.infer_ownership_invariants(scan_id)
        resources = self.infer_resources(scan_id)
        states = self.infer_states(scan_id)

        confidence_stats = {
            "ownership_patterns": len(ownership_invariants),
            "resources_discovered": len(resources),
            "state_machines_found": len(states),
        }

        return InferenceResult(
            ownership_invariants=ownership_invariants,
            resources=resources,
            states=states,
            confidence_stats=confidence_stats,
        )

    def infer_ownership_invariants(self, scan_id: str) -> List[OwnershipInvariant]:
        """
        Infer ownership invariants using statistical analysis

        Strategy:
        1. Find all endpoints with database access
        2. Analyze authorization check patterns
        3. If >80% use same pattern → inferred invariant

        Example:
        - 95% of endpoints check: if user_id == current_user.id
        - Inferred invariant: "Users can only access their own resources"
        """
        invariants = []

        with self.driver.session(database=self.database) as session:
            # Find endpoints with ownership checks
            result = session.run("""
                MATCH (endpoint:Endpoint)-[:HAS_CHILD*]->(check:IfStatement)
                WHERE endpoint.handles_user_input = true
                AND (check.condition CONTAINS 'user_id'
                     OR check.condition CONTAINS 'owner'
                     OR check.condition CONTAINS 'current_user')
                RETURN endpoint.name as endpoint,
                       endpoint.file_path as file,
                       check.condition as condition,
                       check.line_start as line
                LIMIT 50
            """)

            ownership_checks = list(result)

            # Find endpoints without ownership checks (for comparison)
            result = session.run("""
                MATCH (endpoint:Endpoint)
                WHERE endpoint.handles_user_input = true
                AND EXISTS {
                    MATCH (endpoint)-[:HAS_CHILD*]->(db:DatabaseQuery)
                }
                RETURN count(*) as total_endpoints
            """)

            record = result.single()
            total_endpoints = record["total_endpoints"] if record else 0

            if total_endpoints > 0:
                # Calculate confidence based on how many endpoints have checks
                coverage = len(ownership_checks) / total_endpoints

                # Group by pattern
                pattern_counts = {}
                for check in ownership_checks:
                    condition = check["condition"]
                    # Normalize the pattern
                    pattern = self._normalize_ownership_pattern(condition)
                    if pattern not in pattern_counts:
                        pattern_counts[pattern] = []
                    pattern_counts[pattern].append(check)

                # Create invariants for common patterns
                for pattern, examples in pattern_counts.items():
                    if len(examples) >= 2:  # Pattern appears at least twice
                        confidence = min(0.95, len(examples) / total_endpoints)

                        invariants.append(OwnershipInvariant(
                            resource="Resource",
                            actor="User",
                            condition=pattern,
                            confidence=confidence,
                            examples=[f"{e['file']}:{e['line']}" for e in examples[:5]]
                        ))

        return invariants

    def _normalize_ownership_pattern(self, condition: str) -> str:
        """
        Normalize ownership check patterns for comparison

        Examples:
        - "user_id == current_user.id" → "user_id == owner_id"
        - "order.user_id != user.id" → "resource.owner_id != actor.id"
        """
        # Simple pattern normalization
        if "user_id" in condition.lower() and ("==" in condition or "!=" in condition):
            return "actor.id == resource.owner_id"
        if "owner" in condition.lower():
            return "actor.id == resource.owner_id"
        return condition

    def infer_resources(self, scan_id: str) -> List[Resource]:
        """
        Infer resources from database queries

        Strategy:
        1. Find database query patterns (session.query(Model))
        2. Extract model names
        3. Identify sensitive fields (password, ssn, etc.)
        4. Identify owner fields (user_id, owner_id)
        """
        resources = []

        with self.driver.session(database=self.database) as session:
            # Find database queries to identify resources
            result = session.run("""
                MATCH (db:DatabaseQuery)
                WHERE db.name CONTAINS 'query' OR db.name CONTAINS 'get'
                RETURN DISTINCT db.name as query_name,
                                db.file_path as file
                LIMIT 20
            """)

            seen_resources = set()

            for record in result:
                query_name = record["query_name"]

                # Extract resource name from query patterns
                # Pattern: session.query(User), User.query(), etc.
                resource_match = re.search(r'query\((\w+)\)', query_name)
                if resource_match:
                    resource_name = resource_match.group(1)
                elif "." in query_name:
                    parts = query_name.split(".")
                    resource_name = parts[0] if parts[0][0].isupper() else parts[-1]
                else:
                    continue

                if resource_name in seen_resources:
                    continue

                seen_resources.add(resource_name)

                # Infer properties based on name
                from scanner.intent.graph_schema import ResourceType, Sensitivity

                sensitive_fields = []
                sensitivity = Sensitivity.INTERNAL

                # Check if resource has sensitive data
                resource_lower = resource_name.lower()
                if any(word in resource_lower for word in ["user", "account", "profile"]):
                    sensitive_fields = ["password", "email", "ssn", "address"]
                    sensitivity = Sensitivity.CONFIDENTIAL
                elif any(word in resource_lower for word in ["order", "payment", "transaction"]):
                    sensitive_fields = ["total", "credit_card", "payment_method"]
                    sensitivity = Sensitivity.CONFIDENTIAL
                elif any(word in resource_lower for word in ["document", "file"]):
                    sensitive_fields = ["content"]
                    sensitivity = Sensitivity.INTERNAL

                # Infer owner field
                owner_field = None
                if resource_name != "User":
                    owner_field = "user_id"  # Default assumption

                resources.append(Resource(
                    id=resource_name,
                    type=ResourceType.ENTITY,
                    owner_field=owner_field,
                    sensitive_fields=sensitive_fields,
                    sensitivity=sensitivity
                ))

        return resources

    def infer_states(self, scan_id: str) -> List[State]:
        """
        Infer state machines from code

        Strategy:
        1. Find field assignments (order.status = "paid")
        2. Track state transitions
        3. Identify monotonic states (can't go backward)
        """
        states = []

        with self.driver.session(database=self.database) as session:
            # Find variable assignments that look like state changes
            result = session.run("""
                MATCH (func:Function)-[:HAS_CHILD*]->(node)
                WHERE node.node_type = 'Assign' OR node.node_type = 'Assignment'
                RETURN func.name as function,
                       func.file_path as file,
                       node.line_start as line
                LIMIT 20
            """)

            for record in result:
                # In a real implementation, we'd analyze the AST
                # For demo, we'll identify common state patterns
                function = record["function"]

                # Common state field names
                if any(word in function.lower() for word in ["status", "state", "role"]):
                    # Infer a state machine
                    if "order" in function.lower():
                        states.append(State(
                            id="order.status",
                            resource_id="Order",
                            field_name="status",
                            transitions=["pending", "paid", "shipped", "delivered"],
                            is_sensitive=False,
                            is_monotonic=True
                        ))
                    elif "role" in function.lower() or "admin" in function.lower():
                        states.append(State(
                            id="user.role",
                            resource_id="User",
                            field_name="role",
                            transitions=["user", "admin"],
                            is_sensitive=True,
                            is_monotonic=False
                        ))

        # Remove duplicates
        unique_states = {s.id: s for s in states}
        return list(unique_states.values())

    def store_inference_results(self, scan_id: str, results: InferenceResult):
        """
        Store inferred intent in Neo4j

        Args:
            scan_id: Scan identifier
            results: Inference results to store
        """
        from scanner.intent.graph_schema import IntentGraphSchema

        with self.driver.session(database=self.database) as session:
            # Create constraints
            for query in IntentGraphSchema.get_constraint_queries():
                try:
                    session.run(query)
                except Exception:
                    pass  # Constraints may already exist

            # Store resources
            for resource in results.resources:
                session.run(
                    IntentGraphSchema.create_resource_node_query(),
                    id=resource.id,
                    type=resource.type.value,
                    owner_field=resource.owner_field,
                    sensitive_fields=resource.sensitive_fields,
                    sensitivity=resource.sensitivity.value
                )

            # Store states
            for state in results.states:
                session.run(
                    IntentGraphSchema.create_state_node_query(),
                    id=state.id,
                    resource_id=state.resource_id,
                    field_name=state.field_name,
                    transitions=state.transitions,
                    is_sensitive=state.is_sensitive,
                    is_monotonic=state.is_monotonic
                )

            # Store ownership invariants
            for inv in results.ownership_invariants:
                session.run("""
                    MERGE (i:OwnershipInvariant {
                        id: $id
                    })
                    SET i.resource = $resource,
                        i.actor = $actor,
                        i.condition = $condition,
                        i.confidence = $confidence,
                        i.examples = $examples
                """,
                    id=f"inv_{inv.resource}_{hash(inv.condition) % 10000}",
                    resource=inv.resource,
                    actor=inv.actor,
                    condition=inv.condition,
                    confidence=inv.confidence,
                    examples=inv.examples
                )
