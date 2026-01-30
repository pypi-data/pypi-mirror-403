"""
Route Graph Extractor for Express.js/TypeScript applications

Extracts:
- Route definitions (method + path)
- Middleware chains
- Handler bindings
- Router mounts
"""

import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from scanner.analyzers.inline_handler_analyzer import InlineHandlerAnalyzer


@dataclass
class HandlerRef:
    """Reference to a route handler or middleware function"""

    kind: str  # "call", "inline", "identifier", "member"
    name: str
    is_call: bool = False

    # For call expressions (middleware/handler calls)
    module_name: Optional[str] = None
    function_name: Optional[str] = None

    # For inline functions and resolved references
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        handler_id = self._generate_id()
        return {
            "handler_id": handler_id,
            "kind": self.kind,
            "name": self.name,
            "is_call": self.is_call,
            "module_name": self.module_name,
            "function_name": self.function_name,
            "file_path": self.file_path,
            "line_start": self.line_start
        }
    
    def _generate_id(self) -> str:
        """Generate stable handler ID"""
        if self.kind == "inline":
            sig = f"inline:{self.file_path}:{self.line_start}"
        else:
            sig = f"{self.module_name}.{self.function_name}" if self.module_name else self.name
        return hashlib.md5(sig.encode()).hexdigest()[:16]


@dataclass
class MiddlewareInfo:
    """Middleware in a route's chain"""
    
    order: int
    handler_ref: HandlerRef
    middleware_type: str  # "auth", "authz", "validation", "other"
    is_auth: bool = False
    classification_confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "order": self.order,
            "handler_ref": self.handler_ref.to_dict(),
            "middleware_type": self.middleware_type,
            "is_auth": self.is_auth,
            "classification_confidence": self.classification_confidence
        }


@dataclass
class RouteSpec:
    """HTTP route specification"""

    method: str  # "GET", "POST", etc.
    path: str
    file_path: str
    line_start: int
    line_end: int

    middleware: List[MiddlewareInfo] = field(default_factory=list)
    handler: Optional[HandlerRef] = None

    framework: str = "express"
    router_name: str = "app"
    mount_prefix: str = ""

    # Inline handler analysis (NEW)
    inline_handler_analysis: Optional[Dict[str, Any]] = None

    @property
    def requires_auth(self) -> bool:
        """Check if route requires authentication based on middleware"""
        return any(mw.is_auth for mw in self.middleware)

    @property
    def auth_middleware_names(self) -> List[str]:
        """Get names of authentication middleware"""
        return [mw.handler_ref.name for mw in self.middleware if mw.is_auth]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        route_id = self._generate_route_id()
        full_path = self.mount_prefix + self.path if self.mount_prefix else self.path

        result = {
            "route_id": route_id,
            "method": self.method,
            "path": self.path,
            "full_path": full_path,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "requires_auth": self.requires_auth,
            "auth_middleware_names": self.auth_middleware_names,
            "framework": self.framework,
            "router_name": self.router_name,
            "mount_prefix": self.mount_prefix
        }

        # Add inline handler analysis if available
        if self.inline_handler_analysis:
            result["inline_handler_analysis"] = self.inline_handler_analysis

        return result
    
    def _generate_route_id(self) -> str:
        """Generate stable route ID"""
        sig = f"{self.method}:{self.path}:{self.file_path}"
        return hashlib.md5(sig.encode()).hexdigest()[:16]


@dataclass
class RouterMount:
    """Router mount point (e.g., app.use('/admin', adminRouter))"""
    
    prefix: str
    router_name: str
    file_path: str
    line_start: int
    
    def to_dict(self) -> Dict[str, Any]:
        mount_id = hashlib.md5(f"{self.prefix}:{self.router_name}:{self.file_path}".encode()).hexdigest()[:16]
        return {
            "mount_id": mount_id,
            "prefix": self.prefix,
            "router_name": self.router_name,
            "file_path": self.file_path,
            "line_start": self.line_start
        }


class RouteGraphExtractor:
    """Extract route graph from Express.js/TypeScript AST"""

    # Known auth middleware patterns
    AUTH_PATTERNS = [
        "isauthenticated", "authenticate", "verifytoken", "jwt",
        "requireauth", "ensureloggedin", "appenduserid", "isauthorized",
        "authorize", "checkpermission", "isadmin", "isaccounting",
        "requirerole", "denyall"
    ]

    def __init__(self, symbol_table=None):
        """
        Initialize extractor with optional symbol table for cross-file resolution

        Args:
            symbol_table: SymbolTable instance for resolving imports/exports
        """
        self.symbol_table = symbol_table
        self.inline_analyzer = InlineHandlerAnalyzer()

    def extract_routes_from_ast(self, ast: Dict[str, Any], file_path: str) -> Tuple[List[RouteSpec], List[RouterMount]]:
        """
        Extract routes and mounts from ESTree AST

        Args:
            ast: ESTree AST from typescript-estree
            file_path: Source file path

        Returns:
            (routes, mounts) tuple
        """
        routes = []
        mounts = []

        # Walk AST and find route registrations
        for node in ast.get("body", []):
            self._visit_node(node, routes, mounts, file_path)

        return routes, mounts
    
    def _visit_node(self, node: Dict, routes: List, mounts: List, file_path: str):
        """Recursively visit AST nodes"""
        if not isinstance(node, dict):
            return

        node_type = node.get("type")

        if node_type == "ExpressionStatement":
            expr = node.get("expression")
            if expr:
                self._visit_node(expr, routes, mounts, file_path)

        elif node_type == "CallExpression":
            # Check if it's a route registration
            route = self._extract_route_from_call(node, file_path)
            if route:
                routes.append(route)

            # Check if it's a router mount
            mount = self._extract_mount_from_call(node, file_path)
            if mount:
                mounts.append(mount)

            # Always recurse into CallExpression arguments (for .then() callbacks, etc.)
            arguments = node.get("arguments", [])
            for arg in arguments:
                if isinstance(arg, dict):
                    self._visit_node(arg, routes, mounts, file_path)

            # Visit callee in case it's complex
            callee = node.get("callee")
            if isinstance(callee, dict):
                self._visit_node(callee, routes, mounts, file_path)

        elif node_type in ["FunctionDeclaration", "FunctionExpression", "ArrowFunctionExpression"]:
            # Visit function body
            body = node.get("body")
            if body:
                self._visit_node(body, routes, mounts, file_path)

        elif node_type == "BlockStatement":
            # Visit block statements
            body = node.get("body", [])
            for stmt in body:
                self._visit_node(stmt, routes, mounts, file_path)

        elif node_type == "ExportNamedDeclaration":
            # Visit exported declarations (like export async function start())
            declaration = node.get("declaration")
            if declaration:
                self._visit_node(declaration, routes, mounts, file_path)

        else:
            # For all other node types, use generic recursion
            # This handles IfStatement, TryStatement, loops, and any other structures
            for key, value in node.items():
                # Skip metadata keys
                if key in ["type", "loc", "range", "start", "end"]:
                    continue

                if isinstance(value, dict):
                    self._visit_node(value, routes, mounts, file_path)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            self._visit_node(item, routes, mounts, file_path)

    def _extract_route_from_call(self, node: Dict, file_path: str) -> Optional[RouteSpec]:
        """
        Extract route from CallExpression
        
        Patterns:
        - app.get(path, ...middleware, handler)
        - router.post(path, ...middleware, handler)
        """
        callee = node.get("callee", {})
        
        # Must be MemberExpression (app.get, router.post, etc.)
        if callee.get("type") != "MemberExpression":
            return None
        
        obj = callee.get("object", {})
        prop = callee.get("property", {})
        
        obj_name = obj.get("name", "")
        method_name = prop.get("name", "")
        
        # Check if it's a routing call
        if obj_name not in ["app", "router"]:
            return None
        
        if method_name not in ["get", "post", "put", "delete", "patch", "all"]:
            return None
        
        # Extract arguments
        args = node.get("arguments", [])
        if len(args) < 1:
            return None
        
        # First arg should be path
        path_arg = args[0]
        path = self._extract_path(path_arg)
        if not path:
            return None
        
        # Get location
        loc = node.get("loc", {})
        line_start = loc.get("start", {}).get("line", 0)
        line_end = loc.get("end", {}).get("line", line_start)
        
        # Extract middleware and handler
        middleware_list = []
        handler = None
        
        if len(args) > 1:
            # All args except first (path) and last (handler) are middleware
            # Last arg is handler
            middleware_args = args[1:-1] if len(args) > 2 else []
            handler_arg = args[-1]
            
            # Extract middleware
            for idx, mw_arg in enumerate(middleware_args):
                handler_ref = self._extract_handler_ref(mw_arg, file_path)
                if handler_ref:
                    mw_type, is_auth = self._classify_middleware(handler_ref.name)
                    middleware_list.append(MiddlewareInfo(
                        order=idx,
                        handler_ref=handler_ref,
                        middleware_type=mw_type,
                        is_auth=is_auth
                    ))
            
            # Extract handler
            handler = self._extract_handler_ref(handler_arg, file_path)

            # Analyze inline handler if applicable
            inline_analysis = None
            if handler and handler.kind == "inline":
                # Analyze the inline handler AST node
                inline_analysis = self._analyze_inline_handler(
                    handler_arg,
                    method_name.upper(),
                    path,
                    file_path
                )

        return RouteSpec(
            method=method_name.upper(),
            path=path,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            middleware=middleware_list,
            handler=handler,
            router_name=obj_name,
            inline_handler_analysis=inline_analysis
        )
    
    def _extract_mount_from_call(self, node: Dict, file_path: str) -> Optional[RouterMount]:
        """
        Extract router mount from app.use(path, router)
        
        Pattern: app.use('/admin', adminRouter)
        """
        callee = node.get("callee", {})
        
        if callee.get("type") != "MemberExpression":
            return None
        
        obj = callee.get("object", {})
        prop = callee.get("property", {})
        
        obj_name = obj.get("name", "")
        method_name = prop.get("name", "")
        
        # Must be app.use or router.use
        if obj_name not in ["app", "router"] or method_name != "use":
            return None
        
        args = node.get("arguments", [])
        if len(args) < 2:
            return None
        
        # Check if second arg is a router (Identifier, not a function)
        router_arg = args[1]
        if router_arg.get("type") != "Identifier":
            return None
        
        # First arg should be path prefix
        path_arg = args[0]
        prefix = self._extract_path(path_arg)
        if not prefix:
            return None
        
        router_name = router_arg.get("name", "")
        line_start = node.get("loc", {}).get("start", {}).get("line", 0)
        
        return RouterMount(
            prefix=prefix,
            router_name=router_name,
            file_path=file_path,
            line_start=line_start
        )
    
    def _extract_path(self, node: Dict) -> Optional[str]:
        """Extract path from Literal or TemplateLiteral"""
        node_type = node.get("type")
        
        if node_type == "Literal":
            return node.get("value", "")
        elif node_type == "TemplateLiteral":
            # Simple case: no expressions
            quasis = node.get("quasis", [])
            if quasis and len(quasis) == 1:
                return quasis[0].get("value", {}).get("raw", "")
        
        return None
    
    def _extract_handler_ref(self, node: Dict, file_path: str) -> Optional[HandlerRef]:
        """Extract handler reference from AST node with symbol table resolution"""
        if not node:
            return None

        node_type = node.get("type")

        if node_type == "MemberExpression":
            # Handler reference: twoFactorAuth.verify
            # This is the key pattern for Juice Shop!
            obj = node.get("object", {})
            prop = node.get("property", {})

            obj_name = obj.get("name", "")
            prop_name = prop.get("name", "")

            # Try to resolve using symbol table
            resolved_path = None
            if self.symbol_table:
                resolved_path = self.symbol_table.resolve_member_expression(
                    obj_name, prop_name, file_path
                )

            handler_ref = HandlerRef(
                kind="member",
                name=f"{obj_name}.{prop_name}",
                is_call=False,
                module_name=obj_name,
                function_name=prop_name,
                file_path=file_path,
                line_start=node.get("loc", {}).get("start", {}).get("line", 0)
            )

            # Store resolved path as attribute if available
            if resolved_path:
                # resolved_path format: "path:function:line" (handle Windows paths)
                parts = resolved_path.rsplit(":", 2)
                if len(parts) == 3:
                    handler_ref.file_path = parts[0]
                    handler_ref.function_name = parts[1]
                    try:
                        handler_ref.line_start = int(parts[2])
                    except ValueError:
                        pass

            return handler_ref

        elif node_type == "CallExpression":
            # Middleware/handler call: security.appendUserId()
            callee = node.get("callee", {})
            name = self._extract_callee_name(callee)

            # Extract module and function names
            if callee.get("type") == "MemberExpression":
                module_name = callee.get("object", {}).get("name", "")
                function_name = callee.get("property", {}).get("name", "")

                # Try to resolve
                resolved_path = None
                if self.symbol_table:
                    resolved_path = self.symbol_table.resolve_member_expression(
                        module_name, function_name, file_path
                    )

                handler_ref = HandlerRef(
                    kind="call",
                    name=name,
                    is_call=True,
                    module_name=module_name,
                    function_name=function_name
                )

                if resolved_path:
                    # Handle Windows paths with drive letters (C:\...)
                    # Format: path:function:line where path may contain ':'
                    parts = resolved_path.rsplit(":", 2)  # Split from right, max 2 splits
                    if len(parts) == 3:
                        handler_ref.file_path = parts[0]
                        handler_ref.function_name = parts[1]
                        try:
                            handler_ref.line_start = int(parts[2])
                        except ValueError:
                            pass  # Keep default if parse fails

                return handler_ref
            else:
                module_name = None
                function_name = name

            return HandlerRef(
                kind="call",
                name=name,
                is_call=True,
                module_name=module_name,
                function_name=function_name
            )

        elif node_type == "Identifier":
            # Direct function reference
            name = node.get("name", "")

            # Try to resolve
            resolved_path = None
            if self.symbol_table:
                resolved_path = self.symbol_table.resolve_identifier(name, file_path)

            handler_ref = HandlerRef(
                kind="identifier",
                name=name,
                is_call=False
            )

            if resolved_path:
                parts = resolved_path.rsplit(":", 2)
                if len(parts) == 3:
                    handler_ref.file_path = parts[0]
                    handler_ref.function_name = parts[1]
                    try:
                        handler_ref.line_start = int(parts[2])
                    except ValueError:
                        pass

            return handler_ref

        elif node_type in ["ArrowFunctionExpression", "FunctionExpression"]:
            # Inline handler
            line = node.get("loc", {}).get("start", {}).get("line", 0)
            return HandlerRef(
                kind="inline",
                name=f"<inline>@{line}",
                is_call=False,
                file_path=file_path,
                line_start=line
            )

        return None

    def _analyze_inline_handler(
        self,
        handler_node: Dict[str, Any],
        route_method: str,
        route_path: str,
        file_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze an inline handler for security patterns

        Returns analysis dict with ownership checks, risk level, etc.
        """
        try:
            analysis = self.inline_analyzer.analyze_inline_handler(
                handler_node,
                route_method,
                route_path,
                file_path
            )

            # Convert to dict for storage
            return {
                "file_path": analysis.file_path,
                "line_start": analysis.line_start,
                "line_end": analysis.line_end,
                "has_id_parameter": analysis.has_id_parameter,
                "ownership_checks": [
                    {
                        "check_type": check.check_type,
                        "user_property": check.user_property,
                        "resource_property": check.resource_property,
                        "line_number": check.line_number,
                        "confidence": check.confidence
                    }
                    for check in analysis.ownership_checks
                ],
                "has_auth_check": analysis.has_auth_check,
                "database_queries": [
                    {
                        "query_type": query.query_type,
                        "model_name": query.model_name,
                        "line_number": query.line_number
                    }
                    for query in analysis.database_queries
                ],
                "risk_level": analysis.risk_level,
                "missing_checks": analysis.missing_checks
            }
        except Exception as e:
            # Log error but don't fail route extraction
            return None

    def _extract_callee_name(self, callee: Dict) -> str:
        """Extract full name from callee"""
        callee_type = callee.get("type")
        
        if callee_type == "MemberExpression":
            obj = callee.get("object", {}).get("name", "")
            prop = callee.get("property", {}).get("name", "")
            return f"{obj}.{prop}"
        elif callee_type == "Identifier":
            return callee.get("name", "")
        else:
            return "<complex>"
    
    def _classify_middleware(self, name: str) -> Tuple[str, bool]:
        """
        Classify middleware by type
        
        Returns: (type, is_auth) tuple
        """
        name_lower = name.lower()
        
        # Check auth patterns
        for pattern in self.AUTH_PATTERNS:
            if pattern in name_lower:
                # Determine if it's auth or authz
                if any(p in name_lower for p in ["authorize", "permission", "admin", "accounting", "role"]):
                    return "authz", True
                else:
                    return "auth", True
        
        # Check validation patterns
        if any(p in name_lower for p in ["validate", "check", "verify", "ensure"]):
            return "validation", False
        
        return "other", False
