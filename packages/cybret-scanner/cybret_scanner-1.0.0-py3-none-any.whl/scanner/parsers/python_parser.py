"""
Python AST parser for extracting code structure and security-relevant patterns
"""

import ast
from pathlib import Path
from typing import List, Optional, Set, Any

from scanner.parsers.base import BaseParser, ASTNode, CodeEntity, EntityType


class PythonParser(BaseParser):
    """Parser for Python source code"""

    def __init__(self):
        super().__init__(language="python")

    def get_file_extension(self) -> List[str]:
        """Supported Python file extensions"""
        return [".py", ".pyi"]

    def _find_source_files(self, directory: Path) -> List[Path]:
        """Find all Python files in directory"""
        python_files = []
        for ext in self.get_file_extension():
            python_files.extend(directory.rglob(f"*{ext}"))
        return python_files

    def parse_file(self, file_path: Path) -> ASTNode:
        """Parse Python file and build AST"""
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        try:
            tree = ast.parse(source_code, filename=str(file_path))
        except SyntaxError as e:
            raise ValueError(f"Syntax error in {file_path}: {e}")

        # Build language-agnostic AST
        root_node = ASTNode(
            node_type="Module",
            entity_type=EntityType.FILE,
            name=file_path.name,
            source_code=source_code,
        )
        root_node.set_attribute("file_path", str(file_path))

        # Visit all nodes in Python AST
        self._visit_node(tree, root_node, source_code)

        return root_node

    def _visit_node(
        self, py_node: ast.AST, parent_node: ASTNode, source_code: str
    ) -> None:
        """Visit Python AST node and convert to language-agnostic format"""

        # Extract line numbers
        line_start = getattr(py_node, "lineno", 0)
        line_end = getattr(py_node, "end_lineno", line_start)
        col_start = getattr(py_node, "col_offset", 0)
        col_end = getattr(py_node, "end_col_offset", 0)

        # Map Python AST node types to our EntityType
        ast_node = None

        if isinstance(py_node, ast.ClassDef):
            ast_node = self._handle_class(py_node, line_start, line_end, col_start, col_end)
        elif isinstance(py_node, ast.FunctionDef) or isinstance(py_node, ast.AsyncFunctionDef):
            ast_node = self._handle_function(py_node, line_start, line_end, col_start, col_end)
        elif isinstance(py_node, ast.If):
            ast_node = self._handle_if(py_node, line_start, line_end, col_start, col_end)
        elif isinstance(py_node, (ast.For, ast.While)):
            ast_node = self._handle_loop(py_node, line_start, line_end, col_start, col_end)
        elif isinstance(py_node, ast.Try):
            ast_node = self._handle_try(py_node, line_start, line_end, col_start, col_end)
        elif isinstance(py_node, ast.Return):
            ast_node = self._handle_return(py_node, line_start, line_end, col_start, col_end)
        elif isinstance(py_node, ast.Assign):
            ast_node = self._handle_assign(py_node, line_start, line_end, col_start, col_end)
        elif isinstance(py_node, ast.Call):
            ast_node = self._handle_call(py_node, line_start, line_end, col_start, col_end)

        # Add node to parent if we created one
        if ast_node:
            parent_node.add_child(ast_node)
            current_parent = ast_node
        else:
            current_parent = parent_node

        # Recursively visit children
        for child in ast.iter_child_nodes(py_node):
            self._visit_node(child, current_parent, source_code)

    def _handle_class(
        self, py_node: ast.ClassDef, line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle class definition"""
        node = ASTNode(
            node_type="ClassDef",
            entity_type=EntityType.CLASS,
            name=py_node.name,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )

        # Extract base classes
        bases = [self._get_name(base) for base in py_node.bases]
        node.set_attribute("bases", bases)

        # Extract decorators
        if py_node.decorator_list:
            node.has_decorators = True
            node.decorators = [self._get_name(dec) for dec in py_node.decorator_list]

        return node

    def _handle_function(
        self, py_node: ast.FunctionDef | ast.AsyncFunctionDef, line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle function/method definition"""
        is_async = isinstance(py_node, ast.AsyncFunctionDef)

        node = ASTNode(
            node_type="FunctionDef" if not is_async else "AsyncFunctionDef",
            entity_type=EntityType.FUNCTION,
            name=py_node.name,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
            is_async=is_async,
        )

        # Extract parameters
        params = []
        for arg in py_node.args.args:
            params.append(arg.arg)
        node.set_attribute("parameters", params)

        # Extract decorators
        if py_node.decorator_list:
            node.has_decorators = True
            node.decorators = [self._get_name(dec) for dec in py_node.decorator_list]

            # Check for common security decorators
            for dec_name in node.decorators:
                dec_lower = dec_name.lower()

                # Authentication decorators
                if "auth" in dec_lower or "login" in dec_lower:
                    node.add_tag("has_authentication")

                # Authorization decorators
                if "permission" in dec_lower or "authorize" in dec_lower:
                    node.add_tag("has_authorization")

                # API endpoint decorators (Flask, FastAPI, Django, etc.)
                if any(keyword in dec_lower for keyword in ["route", "endpoint", "get", "post", "put", "delete", "patch", "api"]):
                    node.add_tag("is_api_endpoint")
                    node.entity_type = EntityType.API_ENDPOINT

                # Specifically mark Flask/FastAPI routes as handling user input
                if "app.route" in dec_lower or "router." in dec_lower or "@route" in dec_lower:
                    node.add_tag("is_api_endpoint")
                    node.add_tag("handles_user_input")
                    node.entity_type = EntityType.API_ENDPOINT

        # Check if it's a method (has 'self' or 'cls' as first param)
        if params and params[0] in ["self", "cls"]:
            node.entity_type = EntityType.METHOD

        return node

    def _handle_if(
        self, py_node: ast.If, line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle if statement"""
        node = ASTNode(
            node_type="If",
            entity_type=EntityType.IF_STATEMENT,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )

        # Try to extract condition as string
        try:
            condition = ast.unparse(py_node.test)
            node.set_attribute("condition", condition)

            # Check for security-relevant conditions
            if any(keyword in condition.lower() for keyword in ["user", "auth", "permission", "role"]):
                node.add_tag("security_check")
        except Exception:
            pass

        return node

    def _handle_loop(
        self, py_node: ast.For | ast.While, line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle loop statement"""
        node = ASTNode(
            node_type="For" if isinstance(py_node, ast.For) else "While",
            entity_type=EntityType.LOOP,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )
        return node

    def _handle_try(
        self, py_node: ast.Try, line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle try-except block"""
        node = ASTNode(
            node_type="Try",
            entity_type=EntityType.TRY_CATCH,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )

        # Extract exception types
        exception_types = []
        for handler in py_node.handlers:
            if handler.type:
                exception_types.append(self._get_name(handler.type))
        node.set_attribute("exceptions", exception_types)

        return node

    def _handle_return(
        self, py_node: ast.Return, line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle return statement"""
        node = ASTNode(
            node_type="Return",
            entity_type=EntityType.RETURN,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )
        return node

    def _handle_assign(
        self, py_node: ast.Assign, line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle variable assignment"""
        node = ASTNode(
            node_type="Assign",
            entity_type=EntityType.VARIABLE,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )

        # Extract variable names
        targets = []
        for target in py_node.targets:
            targets.append(self._get_name(target))
        node.set_attribute("targets", targets)

        return node

    def _handle_call(
        self, py_node: ast.Call, line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle function call"""
        func_name = self._get_name(py_node.func)

        node = ASTNode(
            node_type="Call",
            entity_type=EntityType.EXTERNAL_CALL,
            name=func_name,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )

        # Extract arguments
        args = []
        for arg in py_node.args:
            try:
                args.append(ast.unparse(arg))
            except Exception:
                args.append("<complex_arg>")
        node.set_attribute("arguments", args)

        # Tag security-relevant calls
        if "query" in func_name.lower() or "execute" in func_name.lower():
            node.add_tag("database_operation")
            node.entity_type = EntityType.DATABASE_QUERY
        if "get" in func_name.lower() or "filter" in func_name.lower() or "find" in func_name.lower():
            node.add_tag("data_access")

        return node

    def _get_name(self, node: ast.AST) -> str:
        """Extract name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            try:
                return ast.unparse(node)
            except Exception:
                return "<unknown>"

    def extract_entities(self, root_node: ASTNode) -> List[CodeEntity]:
        """Extract high-level entities from AST"""
        entities = []

        # Find all functions and methods
        functions = root_node.find_children_by_type(EntityType.FUNCTION)
        functions.extend(root_node.find_children_by_type(EntityType.METHOD))

        for func in functions:
            entity = CodeEntity(
                entity_type=func.entity_type,
                name=func.name or "<anonymous>",
                file_path=root_node.get_attribute("file_path", ""),
                line_start=func.line_start,
                line_end=func.line_end,
                source_code=func.source_code,
            )

            # Analyze security properties
            if "has_authentication" in func.tags:
                entity.performs_authentication = True
            if "has_authorization" in func.tags:
                entity.performs_authorization = True

            # Mark API endpoints as handling user input
            if "is_api_endpoint" in func.tags or "handles_user_input" in func.tags:
                entity.handles_user_input = True
                # Update entity type to API_ENDPOINT
                entity.entity_type = EntityType.API_ENDPOINT

            # Find database queries in function
            db_queries = [child for child in func.find_children_by_type(EntityType.DATABASE_QUERY)]
            if db_queries:
                entity.accesses_database = True

            # Find security checks (if statements with security conditions)
            security_checks = [child for child in func.children if "security_check" in child.tags]
            if security_checks:
                entity.has_security_check = True

            # Extract function calls
            calls = [child for child in func.find_children_by_type(EntityType.EXTERNAL_CALL)]
            entity.calls = [call.name for call in calls if call.name]

            entities.append(entity)

        return entities
