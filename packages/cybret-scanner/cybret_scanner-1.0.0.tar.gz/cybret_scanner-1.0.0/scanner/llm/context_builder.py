"""
Context Builder for LLM-Enhanced Analysis

Builds rich, comprehensive context from code and static analysis results
to enable deep LLM understanding of vulnerabilities and business logic.

This module bridges the scanner's detection results (RouteSpec, Vulnerability)
with the LLM agent system (VulnerabilityContext, CodeContext).
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re

from scanner.models.route_graph import RouteSpec, HandlerRef, MiddlewareInfo
from scanner.detectors.base import Vulnerability
from scanner.llm.agents import VulnerabilityContext, CodeContext


class ContextBuilder:
    """
    Builds comprehensive context for LLM analysis

    Gathers:
    - Code snippets with surrounding context
    - Database models and schemas
    - Related routes and handlers
    - Call graphs and data flow
    - Business logic patterns
    """

    def __init__(self, codebase_path: str):
        self.codebase_path = Path(codebase_path)
        self.model_cache = {}
        self.route_cache = {}

    def build_from_vulnerability(
        self,
        vulnerability: Vulnerability,
        route: Optional[RouteSpec] = None
    ) -> VulnerabilityContext:
        """
        Build VulnerabilityContext from scanner's Vulnerability + RouteSpec

        This is the main bridge between scanner detection and LLM analysis.

        Args:
            vulnerability: Detected vulnerability from scanner
            route: Optional route specification (if available)

        Returns:
            VulnerabilityContext ready for LLM agent analysis
        """

        # Build code context
        if route:
            code_context = self._build_code_context_from_route(route)
        else:
            # Fallback: build minimal context from vulnerability location
            code_context = self._build_minimal_code_context(vulnerability)

        # Extract evidence as list of strings
        evidence_list = []
        if isinstance(vulnerability.evidence, dict):
            for key, value in vulnerability.evidence.items():
                evidence_list.append(f"{key}: {value}")
        else:
            evidence_list = list(vulnerability.evidence) if vulnerability.evidence else []

        # Extract resource type from route path
        resource_type = self._infer_resource_type(code_context.route_path)

        # Infer user roles from middleware
        user_roles = ["user"]  # Default
        if code_context.authentication_flow == "Authenticated":
            user_roles.append("authenticated_user")

        # Determine access patterns
        access_patterns = self._determine_access_patterns(
            code_context.route_method,
            code_context.route_path,
            code_context.code_snippet
        )

        # Build VulnerabilityContext
        vuln_context = VulnerabilityContext(
            vulnerability_type=vulnerability.vuln_type,
            confidence=vulnerability.confidence,
            evidence=evidence_list,
            code_context=code_context,
            ownership_checks=[],  # Could be extracted from code analysis
            auth_checks=[],  # Could be extracted from middleware
            db_queries=[],  # Could be extracted from code
            resource_type=resource_type,
            user_roles=user_roles,
            access_patterns=access_patterns
        )

        return vuln_context

    def _build_code_context_from_route(self, route: RouteSpec) -> CodeContext:
        """
        Build CodeContext from RouteSpec

        Extracts all necessary information for LLM analysis from a route.
        """

        # Read handler code
        handler_code = ""
        function_def = ""
        class_def = None
        imports = []
        caller_functions = []
        callee_functions = []
        data_flow = []

        if route.handler and route.handler.file_path:
            handler_file = Path(route.handler.file_path)
            if handler_file.exists():
                with open(handler_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Extract handler code
                start_line = max(0, route.handler.line_start - 1)
                end_line = min(len(lines), start_line + 50)
                handler_code = ''.join(lines[start_line:end_line])

                # Extract function definition
                function_def = self._extract_function_definition(lines, route.handler.line_start)

                # Extract class definition (if applicable)
                class_def = self._extract_class_definition(lines, route.handler.line_start)

                # Extract imports
                imports = self._extract_imports(lines)

                # Extract data flow from code
                data_flow = self._extract_data_flow_from_code(handler_code)

        # Extract models accessed
        models_accessed = self._extract_models_from_code(handler_code)

        # Load model schemas
        model_schemas = {}
        for model_name in models_accessed:
            schema = self._load_model_schema(model_name)
            if schema:
                model_schemas[model_name] = schema

        # Extract authentication and authorization flow
        auth_flow = "Authenticated" if route.requires_auth else "No authentication"
        authz_rules = ", ".join(route.auth_middleware_names) if route.auth_middleware_names else "None"

        # Build CodeContext
        code_context = CodeContext(
            file_path=route.file_path,
            line_start=route.line_start,
            line_end=route.line_end,
            code_snippet=handler_code,
            function_definition=function_def,
            class_definition=class_def,
            imports=imports,
            route_method=route.method,
            route_path=route.full_path,
            middleware_chain=[mw.handler_ref.name for mw in route.middleware],
            handler_name=route.handler.name if route.handler else "unknown",
            handler_file=route.handler.file_path if route.handler else "",
            handler_code=handler_code,
            models_accessed=models_accessed,
            model_schemas=model_schemas,
            related_routes=[],  # Could be populated from graph
            authentication_flow=auth_flow,
            authorization_rules=authz_rules,
            caller_functions=caller_functions,
            callee_functions=callee_functions,
            data_flow=data_flow
        )

        return code_context

    def _build_minimal_code_context(self, vulnerability: Vulnerability) -> CodeContext:
        """
        Build minimal CodeContext from vulnerability location only

        Used when RouteSpec is not available.
        """

        # Read code snippet from file
        code_snippet = ""
        function_def = ""
        imports = []

        file_path = Path(vulnerability.file_path)
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            start_line = max(0, vulnerability.line_start - 10)
            end_line = min(len(lines), vulnerability.line_start + 40)
            code_snippet = ''.join(lines[start_line:end_line])

            function_def = self._extract_function_definition(lines, vulnerability.line_start)
            imports = self._extract_imports(lines)

        # Extract models
        models_accessed = self._extract_models_from_code(code_snippet)

        # Load schemas
        model_schemas = {}
        for model_name in models_accessed:
            schema = self._load_model_schema(model_name)
            if schema:
                model_schemas[model_name] = schema

        # Build minimal context
        code_context = CodeContext(
            file_path=vulnerability.file_path,
            line_start=vulnerability.line_start,
            line_end=vulnerability.line_end or vulnerability.line_start,
            code_snippet=code_snippet,
            function_definition=function_def,
            class_definition=None,
            imports=imports,
            route_method="UNKNOWN",
            route_path="UNKNOWN",
            middleware_chain=[],
            handler_name=vulnerability.function_name or "unknown",
            handler_file=vulnerability.file_path,
            handler_code=code_snippet,
            models_accessed=models_accessed,
            model_schemas=model_schemas,
            related_routes=[],
            authentication_flow="Unknown",
            authorization_rules="Unknown",
            caller_functions=[],
            callee_functions=[],
            data_flow=[]
        )

        return code_context

    def build_vulnerability_context(
        self,
        route,
        vulnerability_type: str,
        confidence: float,
        evidence: List[str]
    ) -> Dict[str, Any]:
        """
        Build complete context for vulnerability analysis (LEGACY)

        Note: Use build_from_vulnerability() for new code.
        This method is kept for backward compatibility.
        """

        # Build code context
        code_context = self._build_code_context(route)

        # Extract database information
        db_context = self._build_database_context(route, code_context)

        # Build business logic context
        business_context = self._build_business_context(route, code_context)

        # Build call graph
        call_graph = self._build_call_graph(route)

        return {
            "vulnerability_type": vulnerability_type,
            "confidence": confidence,
            "evidence": evidence,
            "code_context": code_context,
            "database_context": db_context,
            "business_context": business_context,
            "call_graph": call_graph
        }

    def _build_code_context(self, route) -> Dict[str, Any]:
        """
        Extract comprehensive code context
        """

        # Read handler file
        if route.handler and route.handler.file_path:
            handler_file = Path(route.handler.file_path)
            if handler_file.exists():
                with open(handler_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Extract handler function
                start_line = max(0, route.handler.line_start - 1)
                end_line = min(len(lines), start_line + 50)  # Up to 50 lines
                handler_code = ''.join(lines[start_line:end_line])

                # Extract function definition
                function_def = self._extract_function_definition(
                    lines, route.handler.line_start
                )

                # Extract class if inside a class
                class_def = self._extract_class_definition(
                    lines, route.handler.line_start
                )

                # Extract imports
                imports = self._extract_imports(lines)

            else:
                handler_code = "<Handler file not found>"
                function_def = ""
                class_def = None
                imports = []
        else:
            handler_code = "<Handler not resolved>"
            function_def = ""
            class_def = None
            imports = []

        return {
            "file_path": route.file_path,
            "line_start": route.line_start,
            "line_end": route.line_end,
            "route_method": route.method,
            "route_path": route.path,
            "handler_name": route.handler.name if route.handler else "unknown",
            "handler_file": route.handler.file_path if route.handler else "",
            "handler_code": handler_code,
            "function_definition": function_def,
            "class_definition": class_def,
            "imports": imports,
            "middleware_chain": [mw.handler_ref.name for mw in route.middleware]
        }

    def _build_database_context(self, route, code_context: Dict) -> Dict[str, Any]:
        """
        Extract database models and schemas accessed by this route
        """

        # Extract models from code
        models_accessed = self._extract_models_from_code(
            code_context['handler_code']
        )

        # Load model schemas
        model_schemas = {}
        for model_name in models_accessed:
            schema = self._load_model_schema(model_name)
            if schema:
                model_schemas[model_name] = schema

        # Extract query patterns
        query_patterns = self._extract_query_patterns(
            code_context['handler_code']
        )

        return {
            "models_accessed": models_accessed,
            "model_schemas": model_schemas,
            "query_patterns": query_patterns
        }

    def _build_business_context(self, route, code_context: Dict) -> Dict[str, Any]:
        """
        Build business logic context
        """

        # Determine resource type from path
        resource_type = self._infer_resource_type(route.path)

        # Find related routes (same resource)
        related_routes = self._find_related_routes(resource_type)

        # Infer user roles from middleware
        user_roles = self._infer_user_roles(code_context['middleware_chain'])

        # Extract authorization patterns
        auth_patterns = self._extract_auth_patterns(code_context['handler_code'])

        # Determine access patterns
        access_patterns = self._determine_access_patterns(
            route.method,
            route.path,
            code_context['handler_code']
        )

        return {
            "resource_type": resource_type,
            "related_routes": related_routes,
            "user_roles": user_roles,
            "authorization_patterns": auth_patterns,
            "access_patterns": access_patterns
        }

    def _build_call_graph(self, route) -> Dict[str, Any]:
        """
        Build call graph context
        """

        # This would use actual call graph analysis
        # For now, simplified version

        return {
            "caller_functions": [],
            "callee_functions": [],
            "data_flow": []
        }

    def _extract_function_definition(self, lines: List[str], target_line: int) -> str:
        """
        Extract complete function definition
        """

        # Find function start
        start = target_line - 1
        while start > 0:
            line = lines[start].strip()
            if line.startswith('function ') or line.startswith('export function'):
                break
            if line.startswith('async function') or line.startswith('export async function'):
                break
            # Arrow functions
            if '=>' in line and ('const ' in line or 'let ' in line or 'var ' in line):
                break
            start -= 1

        # Find function end (simplified - just take next 30 lines)
        end = min(len(lines), start + 30)

        return ''.join(lines[start:end])

    def _extract_class_definition(self, lines: List[str], target_line: int) -> Optional[str]:
        """
        Extract class definition if function is inside a class
        """

        # Find class start
        start = target_line - 1
        while start > 0:
            line = lines[start].strip()
            if line.startswith('class '):
                # Found class, extract it
                end = min(len(lines), start + 100)
                return ''.join(lines[start:end])
            start -= 1

        return None

    def _extract_imports(self, lines: List[str]) -> List[str]:
        """
        Extract all import statements
        """

        imports = []
        for line in lines[:50]:  # Check first 50 lines
            line = line.strip()
            if line.startswith('import ') or line.startswith('require('):
                imports.append(line)
            if line and not line.startswith('import') and not line.startswith('//'):
                # Stop at first non-import, non-comment line
                if not line.startswith('require'):
                    break

        return imports

    def _extract_models_from_code(self, code: str) -> List[str]:
        """
        Extract database models referenced in code
        """

        models = set()

        # Pattern 1: Model.method() - Sequelize/Mongoose
        pattern1 = r'([A-Z][a-zA-Z0-9_]+)\.(findOne|findAll|create|update|destroy|find|findById)'
        for match in re.finditer(pattern1, code):
            models.add(match.group(1))

        # Pattern 2: models.ModelName
        pattern2 = r'models\.([A-Z][a-zA-Z0-9_]+)'
        for match in re.finditer(pattern2, code):
            models.add(match.group(1))

        # Pattern 3: await Model.
        pattern3 = r'await\s+([A-Z][a-zA-Z0-9_]+)\.'
        for match in re.finditer(pattern3, code):
            models.add(match.group(1))

        return list(models)

    def _load_model_schema(self, model_name: str) -> Optional[Dict[str, str]]:
        """
        Load model schema from model definition file
        """

        # Check cache
        if model_name in self.model_cache:
            return self.model_cache[model_name]

        # Find model file
        model_file = self._find_model_file(model_name)
        if not model_file:
            return None

        # Parse model schema
        schema = self._parse_model_schema(model_file)
        self.model_cache[model_name] = schema

        return schema

    def _find_model_file(self, model_name: str) -> Optional[Path]:
        """
        Find model definition file
        """

        # Common model locations
        search_paths = [
            self.codebase_path / 'models',
            self.codebase_path / 'src' / 'models',
            self.codebase_path / 'app' / 'models',
            self.codebase_path / 'data' / 'models'
        ]

        for search_path in search_paths:
            if not search_path.exists():
                continue

            # Try different naming conventions
            for filename in [
                f"{model_name}.ts",
                f"{model_name}.js",
                f"{model_name.lower()}.ts",
                f"{model_name.lower()}.js"
            ]:
                model_file = search_path / filename
                if model_file.exists():
                    return model_file

        return None

    def _parse_model_schema(self, model_file: Path) -> Dict[str, str]:
        """
        Parse model schema from file
        """

        schema = {}

        try:
            with open(model_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Pattern for Sequelize models
            # field: DataTypes.STRING
            pattern = r'(\w+):\s*(?:DataTypes|Sequelize)\.(\w+)'
            for match in re.finditer(pattern, content):
                field_name = match.group(1)
                field_type = match.group(2)
                schema[field_name] = field_type

            # Pattern for Mongoose models
            # fieldName: { type: String }
            pattern2 = r'(\w+):\s*\{\s*type:\s*(\w+)'
            for match in re.finditer(pattern2, content):
                field_name = match.group(1)
                field_type = match.group(2)
                if field_name not in schema:
                    schema[field_name] = field_type

        except Exception as e:
            print(f"Error parsing model schema: {e}")

        return schema

    def _extract_query_patterns(self, code: str) -> List[str]:
        """
        Extract database query patterns
        """

        patterns = []

        # findOne patterns
        if 'findOne' in code:
            patterns.append("findOne - Fetch single record")

        # findAll/find patterns
        if 'findAll' in code or re.search(r'\.find\(', code):
            patterns.append("find/findAll - Fetch multiple records")

        # create patterns
        if 'create' in code:
            patterns.append("create - Insert new record")

        # update patterns
        if 'update' in code:
            patterns.append("update - Modify existing record")

        # delete patterns
        if 'destroy' in code or 'delete' in code:
            patterns.append("destroy/delete - Remove record")

        return patterns

    def _infer_resource_type(self, path: str) -> str:
        """
        Infer resource type from route path
        """

        # Extract resource from path
        # /api/Users/:id → Users
        # /api/Baskets/:basketId/items → Baskets

        parts = path.split('/')
        for part in parts:
            if part and part[0].isupper() and ':' not in part:
                return part

        return "Unknown"

    def _find_related_routes(self, resource_type: str) -> List[str]:
        """
        Find routes operating on same resource
        """

        # This would query the route cache
        # For now, return empty
        return []

    def _infer_user_roles(self, middleware: List[str]) -> List[str]:
        """
        Infer user roles from middleware
        """

        roles = ["user"]  # Default

        # Check for admin middleware
        if any('admin' in mw.lower() for mw in middleware):
            roles.append("admin")

        # Check for accounting
        if any('accounting' in mw.lower() for mw in middleware):
            roles.append("accountant")

        return roles

    def _extract_auth_patterns(self, code: str) -> List[str]:
        """
        Extract authorization patterns from code
        """

        patterns = []

        # req.user checks
        if 'req.user' in code:
            patterns.append("User authentication check")

        # userId comparison
        if 'userId ===' in code or 'userId !== ' in code:
            patterns.append("User ID comparison")

        # Role checks
        if 'role ===' in code or 'hasRole' in code:
            patterns.append("Role-based access control")

        return patterns

    def _determine_access_patterns(
        self,
        method: str,
        path: str,
        code: str
    ) -> List[str]:
        """
        Determine access patterns
        """

        patterns = []

        # Read vs Write
        if method in ['GET', 'HEAD']:
            patterns.append("READ operation")
        elif method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            patterns.append("WRITE operation")

        # ID-based access
        if ':id' in path or ':userId' in path:
            patterns.append("ID-based resource access")

        # Collection vs Item
        if ':' in path:
            patterns.append("Single item access")
        else:
            patterns.append("Collection access")

        return patterns

    def _extract_data_flow_from_code(self, code: str) -> List[str]:
        """
        Extract data flow steps from code

        Returns sequence of operations: Input → Process → Output
        """

        flow = []

        # Input sources
        if 'req.params' in code or 'req.query' in code:
            flow.append("User Input (req.params/query)")

        if 'req.body' in code:
            flow.append("Request Body")

        if 'req.user' in code:
            flow.append("Authenticated User (req.user)")

        # Processing
        if 'findOne' in code or 'findById' in code:
            flow.append("Database Lookup (single record)")

        if 'findAll' in code or re.search(r'\.find\(', code):
            flow.append("Database Query (multiple records)")

        if 'create' in code:
            flow.append("Database Insert")

        if 'update' in code:
            flow.append("Database Update")

        # Authorization checks
        if 'userId ===' in code or 'user.id' in code:
            flow.append("User ID Comparison")

        if 'role ===' in code or 'hasRole' in code:
            flow.append("Role Check")

        # Output
        if 'res.json' in code or 'res.send' in code:
            flow.append("JSON Response")

        if 'res.status' in code:
            flow.append("HTTP Status Response")

        return flow

    def _extract_data_flow_patterns(self, code_context: CodeContext) -> List[str]:
        """
        Extract high-level data flow patterns for vulnerability analysis
        """

        patterns = []

        # Pattern 1: Direct ID access without ownership check
        if code_context.route_path and ':' in code_context.route_path:
            if 'req.user' not in code_context.code_snippet:
                patterns.append("ID parameter without user context check")

        # Pattern 2: Database query with user input
        if code_context.models_accessed:
            if 'req.params' in code_context.code_snippet or 'req.query' in code_context.code_snippet:
                patterns.append("Database query using user input")

        # Pattern 3: No authorization middleware
        if code_context.authentication_flow == "No authentication":
            patterns.append("No authentication middleware")

        # Pattern 4: Return without filtering
        if 'res.json' in code_context.code_snippet:
            if 'filter' not in code_context.code_snippet.lower():
                patterns.append("Direct response without filtering")

        return patterns

    def _extract_business_logic_patterns(self, code: str) -> List[str]:
        """
        Extract business logic patterns from code
        """

        patterns = []

        # Ownership patterns
        if 'userId' in code and '===' in code:
            patterns.append("Ownership verification pattern")

        # Role-based patterns
        if 'role' in code.lower():
            patterns.append("Role-based access control")

        # State machine patterns
        if 'status' in code and ('if' in code or 'switch' in code):
            patterns.append("State machine pattern")

        # Transaction patterns
        if 'transaction' in code.lower() or 'commit' in code.lower():
            patterns.append("Database transaction pattern")

        # Validation patterns
        if 'validate' in code.lower() or 'check' in code.lower():
            patterns.append("Input validation pattern")

        return patterns


class CodeSnippetExtractor:
    """
    Extracts relevant code snippets for LLM context
    """

    @staticmethod
    def extract_with_context(
        file_path: str,
        target_line: int,
        context_lines_before: int = 10,
        context_lines_after: int = 10
    ) -> Dict[str, Any]:
        """
        Extract code snippet with surrounding context
        """

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            start = max(0, target_line - context_lines_before - 1)
            end = min(len(lines), target_line + context_lines_after)

            snippet = ''.join(lines[start:end])

            return {
                "snippet": snippet,
                "start_line": start + 1,
                "end_line": end,
                "target_line": target_line
            }

        except Exception as e:
            return {
                "snippet": f"<Error reading file: {e}>",
                "start_line": 0,
                "end_line": 0,
                "target_line": target_line
            }

    @staticmethod
    def extract_function(file_path: str, function_name: str) -> Optional[str]:
        """
        Extract complete function definition
        """

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find function definition
            pattern = rf'(?:export\s+)?(?:async\s+)?function\s+{function_name}\s*\([^)]*\)\s*\{{[^}}]*\}}'
            match = re.search(pattern, content, re.DOTALL)

            if match:
                return match.group(0)

            return None

        except Exception as e:
            return None
