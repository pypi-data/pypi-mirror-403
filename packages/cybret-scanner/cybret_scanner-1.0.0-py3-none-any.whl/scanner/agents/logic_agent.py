"""
Business Logic Agent - Logic Flaw Detection

Detects business logic vulnerabilities:
- Negative prices/quantities
- Invalid state transitions
- Invariant violations
- Mathematical logic errors
- Business rule violations
"""

from typing import List
from scanner.agents.base import SecurityAgent, AgentFinding, VulnerabilityDimension


class BusinessLogicAgent(SecurityAgent):
    """
    Analyzes business logic flaws across all dimensions

    Focus areas:
    - Negative value handling
    - State transition validation
    - Business invariant enforcement
    - Mathematical operation safety
    - Rule consistency
    """

    def __init__(self, driver, database: str = "neo4j"):
        super().__init__(
            name="BusinessLogicAgent",
            dimension=VulnerabilityDimension.STATE,  # Primary dimension
            driver=driver,
            database=database,
        )

    def analyze(self, scan_id: str) -> List[AgentFinding]:
        """Run business logic security analysis"""
        self.clear_findings()

        with self.driver.session(database=self.database) as session:
            # Analysis 1: Negative value vulnerabilities
            self._detect_negative_value_issues(session, scan_id)

            # Analysis 2: Invalid state transitions
            self._detect_invalid_state_transitions(session, scan_id)

            # Analysis 3: Mathematical logic errors
            self._detect_math_logic_errors(session, scan_id)

            # Analysis 4: Business invariant violations
            self._detect_invariant_violations(session, scan_id)

            # Analysis 5: Price manipulation
            self._detect_price_manipulation(session, scan_id)

        return self.findings

    def _detect_negative_value_issues(self, session, scan_id: str):
        """Detect functions accepting negative values without validation"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method)
        AND (func.name =~ '(?i).*(price|amount|quantity|balance|total|payment).*'
             OR any(param IN func.parameters WHERE param =~ '(?i).*(price|amount|quantity|balance|total).*'))
        AND NOT (func)-[:HAS_CHILD*]->(check:IfStatement)
          WHERE check.condition =~ '(?i).*(>=|>).*0.*'
             OR check.condition =~ '(?i).*positive.*'
             OR check.condition =~ '(?i).*negative.*'
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               func.parameters AS parameters
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="negative_value_handling",
                severity="high",
                confidence=0.75,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Missing negative value validation",
                description=(
                    f"Function '{record['name']}' handles financial/quantity values "
                    "without checking for negative inputs. This can lead to: "
                    "negative pricing attacks, inventory manipulation, balance underflow."
                ),
                context={
                    "business_logic": "Financial/quantity value handling",
                    "risk": "Negative value exploitation, financial loss"
                },
                evidence={
                    "parameters": record["parameters"],
                    "has_negative_check": False,
                },
            )
            self.findings.append(finding)

    def _detect_invalid_state_transitions(self, session, scan_id: str):
        """Detect invalid state transitions in business workflows"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method)
        AND func.name =~ '(?i).*(update|change|set|transition).*status.*'
        AND NOT (func)-[:HAS_CHILD*]->(check:IfStatement)
          WHERE check.condition =~ '(?i).*(current|previous|valid|allowed).*state.*'
             OR check.condition =~ '(?i).*status.*'
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="invalid_state_transition",
                severity="high",
                confidence=0.70,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Missing state transition validation",
                description=(
                    f"Function '{record['name']}' changes status/state without validating "
                    "the current state or checking if the transition is valid. "
                    "This can allow: order status manipulation, workflow bypassing, "
                    "invalid state combinations."
                ),
                context={
                    "business_logic": "State machine/workflow transitions",
                    "risk": "Business process bypass, invalid states"
                },
                evidence={
                    "validates_current_state": False,
                    "checks_valid_transitions": False,
                },
            )
            self.findings.append(finding)

    def _detect_math_logic_errors(self, session, scan_id: str):
        """Detect mathematical operations without proper validation"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method)
        MATCH (func)-[:HAS_CHILD*]->(expr)
        WHERE expr.operator IN ['/', '%', '*', '+', '-']
        AND NOT (func)-[:HAS_CHILD*]->(check)
          WHERE check.condition =~ '(?i).*(zero|divide|overflow|underflow).*'
        WITH func, count(expr) as math_ops
        WHERE math_ops > 2
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               math_ops
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="math_logic_error",
                severity="medium",
                confidence=0.65,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Mathematical operations without validation",
                description=(
                    f"Function '{record['name']}' performs {record['math_ops']} mathematical "
                    "operations without checking for: division by zero, integer overflow/underflow, "
                    "or invalid operands. This can cause crashes or logic bypasses."
                ),
                context={
                    "business_logic": "Mathematical calculations",
                    "risk": "Division by zero, overflow, calculation errors"
                },
                evidence={
                    "math_operation_count": record["math_ops"],
                    "has_validation": False,
                },
            )
            self.findings.append(finding)

    def _detect_invariant_violations(self, session, scan_id: str):
        """Detect business invariant violations"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method)
        AND func.handles_user_input = true
        MATCH (func)-[:HAS_CHILD*]->(call:Call)
        WHERE call.name =~ '(?i).*(save|update|insert|create|set).*'
        AND NOT (func)-[:HAS_CHILD*]->(check:IfStatement)
          WHERE check.condition =~ '(?i).*(validate|verify|check|ensure|invariant).*'
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end,
               call.name AS operation
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="invariant_violation",
                severity="medium",
                confidence=0.60,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Missing business invariant checks",
                description=(
                    f"Function '{record['name']}' performs data modification "
                    f"({record['operation']}) from user input without enforcing "
                    "business invariants. Examples: total = sum(items), "
                    "start_date < end_date, stock >= reserved."
                ),
                context={
                    "business_logic": "Business rule enforcement",
                    "risk": "Data inconsistency, business rule bypass"
                },
                evidence={
                    "operation": record["operation"],
                    "has_invariant_checks": False,
                },
            )
            self.findings.append(finding)

    def _detect_price_manipulation(self, session, scan_id: str):
        """Detect price manipulation vulnerabilities"""
        query = """
        MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(func)
        WHERE (func:Function OR func:Method OR func:Endpoint)
        AND func.name =~ '(?i).*(checkout|order|purchase|payment|calculate.*total).*'
        AND func.handles_user_input = true
        MATCH (func)-[:HAS_CHILD*]->(call:Call)
        WHERE call.name =~ '(?i).*(price|amount|total).*'
        AND NOT (func)-[:HAS_CHILD*]->(validation)
          WHERE validation.name =~ '(?i).*(verify|validate|check).*price.*'
             OR validation.name =~ '(?i).*recalculate.*'
        RETURN func.name AS name,
               func.file_path AS file_path,
               func.line_start AS line_start,
               func.line_end AS line_end
        LIMIT 50
        """

        result = session.run(query, scan_id=scan_id)

        for record in result:
            finding = AgentFinding(
                agent_name=self.name,
                dimension=self.dimension,
                finding_type="price_manipulation",
                severity="critical",
                confidence=0.80,
                file_path=record["file_path"],
                line_start=record["line_start"],
                line_end=record["line_end"],
                function_name=record["name"],
                title=f"Price manipulation vulnerability",
                description=(
                    f"Function '{record['name']}' processes checkout/payment with user input "
                    "but doesn't verify prices against server-side source of truth. "
                    "Users may be able to: modify prices, change quantities after calculation, "
                    "manipulate totals."
                ),
                context={
                    "business_logic": "Price calculation and payment",
                    "risk": "Financial loss, free purchases, price tampering"
                },
                evidence={
                    "accepts_user_input": True,
                    "verifies_prices": False,
                    "recalculates_total": False,
                },
            )
            self.findings.append(finding)
