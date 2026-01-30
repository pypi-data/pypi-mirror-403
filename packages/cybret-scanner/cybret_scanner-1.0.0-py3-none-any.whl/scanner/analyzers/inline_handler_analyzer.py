"""
Inline Handler Analyzer

Analyzes inline arrow function handlers to detect:
- Ownership checks (req.user.id vs resource.userId)
- Authentication checks
- Authorization patterns
- Database queries
- Parameter usage
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set


@dataclass
class OwnershipCheck:
    """Detected ownership check pattern"""
    check_type: str  # "comparison", "guard_function", "middleware"
    user_property: str  # "req.user.id", "userId", etc.
    resource_property: str  # "basket.userId", "item.ownerId", etc.
    line_number: int
    confidence: float  # 0.0 - 1.0


@dataclass
class DatabaseAccess:
    """Database query detected in handler"""
    model_name: str  # "BasketModel", "UserModel", etc.
    operation: str  # "findOne", "findByPk", "create", "update"
    parameter_used: str  # "req.params.id", "req.body.basketId"
    line_number: int


@dataclass
class InlineHandlerAnalysis:
    """Analysis results for an inline handler"""

    # Handler location
    file_path: str
    line_start: int
    line_end: int

    # Route context
    route_method: str  # "GET", "POST", etc.
    route_path: str  # "/api/BasketItems/:id"

    # Parameters
    has_id_parameter: bool
    parameter_names: List[str]

    # Security checks
    ownership_checks: List[OwnershipCheck]
    has_auth_check: bool

    # Database access
    database_queries: List[DatabaseAccess]

    # Risk assessment
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    missing_checks: List[str]

    def has_ownership_check(self) -> bool:
        """Check if handler has any ownership validation"""
        return len(self.ownership_checks) > 0


class InlineHandlerAnalyzer:
    """Analyzes inline arrow function handlers for security patterns"""

    # Common ownership check patterns
    OWNERSHIP_PATTERNS = [
        "req.user.id",
        "req.userId",
        "userId",
        "user.id",
        "currentUser.id"
    ]

    # Common resource ownership properties
    RESOURCE_OWNER_PATTERNS = [
        "userId",
        "ownerId",
        "createdBy",
        "UserId",
        "OwnerId"
    ]

    # Database models and methods
    DB_MODELS = [
        "Model", "findOne", "findByPk", "findAll",
        "create", "update", "destroy", "save"
    ]

    def analyze_inline_handler(
        self,
        handler_node: Dict[str, Any],
        route_method: str,
        route_path: str,
        file_path: str
    ) -> InlineHandlerAnalysis:
        """
        Analyze an inline arrow function handler

        Args:
            handler_node: AST node (ArrowFunctionExpression or FunctionExpression)
            route_method: HTTP method (GET, POST, etc.)
            route_path: Route path (/api/Users/:id)
            file_path: Source file path

        Returns:
            InlineHandlerAnalysis with detected patterns
        """

        # Extract handler body
        body = handler_node.get("body", {})
        params = handler_node.get("params", [])
        loc = handler_node.get("loc", {})

        line_start = loc.get("start", {}).get("line", 0)
        line_end = loc.get("end", {}).get("line", 0)

        # Check if route has ID parameter
        has_id_param = ":id" in route_path or "/:id" in route_path
        param_names = self._extract_route_params(route_path)

        # Analyze handler body
        ownership_checks = self._find_ownership_checks(body)
        has_auth_check = self._find_auth_checks(body)
        db_queries = self._find_database_queries(body)

        # Assess risk
        risk_level, missing_checks = self._assess_risk(
            route_method,
            has_id_param,
            ownership_checks,
            has_auth_check,
            db_queries
        )

        return InlineHandlerAnalysis(
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            route_method=route_method,
            route_path=route_path,
            has_id_parameter=has_id_param,
            parameter_names=param_names,
            ownership_checks=ownership_checks,
            has_auth_check=has_auth_check,
            database_queries=db_queries,
            risk_level=risk_level,
            missing_checks=missing_checks
        )

    def _extract_route_params(self, route_path: str) -> List[str]:
        """Extract parameter names from route path"""
        import re
        params = re.findall(r':(\w+)', route_path)
        return params

    def _find_ownership_checks(self, body_node: Dict) -> List[OwnershipCheck]:
        """Find ownership validation patterns in handler body"""
        checks = []

        # Recursively search for comparison patterns
        def search_comparisons(node: Dict, depth: int = 0):
            if not isinstance(node, dict) or depth > 20:
                return

            node_type = node.get("type")

            # Binary comparison: a === b or a !== b
            if node_type == "BinaryExpression":
                operator = node.get("operator")
                if operator in ["===", "!==", "==", "!="]:
                    left = node.get("left", {})
                    right = node.get("right", {})

                    # Check if comparing user ID to resource ID
                    left_str = self._expr_to_string(left)
                    right_str = self._expr_to_string(right)

                    # Detect ownership pattern
                    if self._is_ownership_comparison(left_str, right_str):
                        loc = node.get("loc", {})
                        checks.append(OwnershipCheck(
                            check_type="comparison",
                            user_property=left_str if "user" in left_str.lower() else right_str,
                            resource_property=right_str if "user" in left_str.lower() else left_str,
                            line_number=loc.get("start", {}).get("line", 0),
                            confidence=0.9
                        ))

            # Recurse
            for key, value in node.items():
                if isinstance(value, dict):
                    search_comparisons(value, depth + 1)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            search_comparisons(item, depth + 1)

        search_comparisons(body_node)
        return checks

    def _find_auth_checks(self, body_node: Dict) -> bool:
        """Check if handler validates authentication"""
        # Look for req.user, req.userId, etc.
        body_str = str(body_node)
        return "req.user" in body_str or "req.userId" in body_str

    def _find_database_queries(self, body_node: Dict) -> List[DatabaseAccess]:
        """Find database query patterns"""
        queries = []

        def search_db_calls(node: Dict, depth: int = 0):
            if not isinstance(node, dict) or depth > 20:
                return

            node_type = node.get("type")

            # Look for Model.findOne, Model.findByPk, etc.
            if node_type == "CallExpression":
                callee = node.get("callee", {})
                if callee.get("type") == "MemberExpression":
                    obj = callee.get("object", {})
                    prop = callee.get("property", {})

                    model_name = obj.get("name", "")
                    method_name = prop.get("name", "")

                    # Check if it's a DB query
                    if "Model" in model_name or method_name in self.DB_MODELS:
                        loc = node.get("loc", {})
                        queries.append(DatabaseAccess(
                            model_name=model_name,
                            operation=method_name,
                            parameter_used="unknown",  # TODO: extract parameter
                            line_number=loc.get("start", {}).get("line", 0)
                        ))

            # Recurse
            for key, value in node.items():
                if isinstance(value, dict):
                    search_db_calls(value, depth + 1)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            search_db_calls(item, depth + 1)

        search_db_calls(body_node)
        return queries

    def _expr_to_string(self, expr: Dict) -> str:
        """Convert expression AST to string representation"""
        if not isinstance(expr, dict):
            return ""

        expr_type = expr.get("type")

        if expr_type == "Identifier":
            return expr.get("name", "")

        elif expr_type == "MemberExpression":
            obj = self._expr_to_string(expr.get("object", {}))
            prop = self._expr_to_string(expr.get("property", {}))
            return f"{obj}.{prop}" if obj and prop else ""

        elif expr_type == "Literal":
            return str(expr.get("value", ""))

        return ""

    def _is_ownership_comparison(self, left: str, right: str) -> bool:
        """Check if comparison is an ownership check"""
        # One side should be user ID, other should be resource owner
        has_user = any(pattern in left.lower() or pattern in right.lower()
                      for pattern in ["user.id", "userid", "currentuser"])

        has_resource_owner = any(pattern in left.lower() or pattern in right.lower()
                                for pattern in ["userid", "ownerid", "createdby"])

        return has_user and has_resource_owner and left != right

    def _assess_risk(
        self,
        method: str,
        has_id_param: bool,
        ownership_checks: List[OwnershipCheck],
        has_auth_check: bool,
        db_queries: List[DatabaseAccess]
    ) -> tuple[str, List[str]]:
        """Assess security risk level"""

        missing_checks = []

        # High risk: ID parameter + DB query + no ownership check
        if has_id_param and db_queries and not ownership_checks:
            if method in ["GET", "PUT", "DELETE"]:
                missing_checks.append("ownership_check")
                return "CRITICAL", missing_checks

        # Medium risk: ID parameter but no clear checks
        if has_id_param and not ownership_checks:
            missing_checks.append("ownership_validation")
            return "HIGH", missing_checks

        # Low risk: Has ownership checks
        if ownership_checks:
            return "LOW", []

        # Medium risk: DB queries without validation
        if db_queries:
            missing_checks.append("data_validation")
            return "MEDIUM", missing_checks

        return "LOW", []
