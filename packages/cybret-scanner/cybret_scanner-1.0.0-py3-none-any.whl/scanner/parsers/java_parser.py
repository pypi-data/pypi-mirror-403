"""
Java parser using javalang library for AST extraction
"""

from pathlib import Path
from typing import List, Optional
import javalang

from scanner.parsers.base import BaseParser, ASTNode, CodeEntity, EntityType


class JavaParser(BaseParser):
    """Parser for Java source code"""

    def __init__(self):
        super().__init__(language="java")

    def get_file_extension(self) -> List[str]:
        """Supported Java file extensions"""
        return [".java"]

    def _find_source_files(self, directory: Path) -> List[Path]:
        """Find all Java files"""
        return list(directory.rglob("*.java"))

    def parse_file(self, file_path: Path) -> ASTNode:
        """Parse Java file using javalang"""
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        try:
            tree = javalang.parse.parse(source_code)
        except Exception as e:
            raise ValueError(f"Error parsing {file_path}: {e}")

        # Build language-agnostic AST
        root_node = ASTNode(
            node_type="CompilationUnit",
            entity_type=EntityType.FILE,
            name=file_path.name,
            source_code=source_code,
        )
        root_node.set_attribute("file_path", str(file_path))

        # Visit Java AST nodes
        for path, node in tree:
            self._visit_node(node, root_node)

        return root_node

    def _visit_node(self, java_node, parent_node: ASTNode) -> None:
        """Visit javalang AST node"""
        ast_node = None

        if isinstance(java_node, javalang.tree.ClassDeclaration):
            ast_node = self._handle_class(java_node)
        elif isinstance(java_node, javalang.tree.MethodDeclaration):
            ast_node = self._handle_method(java_node)
        elif isinstance(java_node, javalang.tree.MethodInvocation):
            ast_node = self._handle_method_invocation(java_node)

        if ast_node:
            parent_node.add_child(ast_node)

    def _handle_class(self, java_node) -> ASTNode:
        """Handle Java class"""
        node = ASTNode(
            node_type="ClassDeclaration",
            entity_type=EntityType.CLASS,
            name=java_node.name,
        )

        # Extract modifiers
        if java_node.modifiers:
            if "public" in java_node.modifiers:
                node.is_public = True
            node.set_attribute("modifiers", list(java_node.modifiers))

        # Extract extends
        if java_node.extends:
            node.set_attribute("extends", java_node.extends.name)

        return node

    def _handle_method(self, java_node) -> ASTNode:
        """Handle Java method"""
        node = ASTNode(
            node_type="MethodDeclaration",
            entity_type=EntityType.METHOD,
            name=java_node.name,
        )

        # Extract modifiers
        if java_node.modifiers:
            if "public" in java_node.modifiers:
                node.is_public = True
            node.set_attribute("modifiers", list(java_node.modifiers))

        # Extract parameters
        params = []
        if java_node.parameters:
            for param in java_node.parameters:
                params.append(param.name)
        node.set_attribute("parameters", params)

        # Extract annotations (similar to decorators)
        if java_node.annotations:
            node.has_decorators = True
            annotations = []
            for annotation in java_node.annotations:
                annotations.append(annotation.name)
            node.decorators = annotations

            # Check for security annotations
            for ann in annotations:
                if any(keyword in ann.lower() for keyword in ["secured", "authorized", "permission"]):
                    node.add_tag("has_authorization")
                if "requestmapping" in ann.lower() or "getmapping" in ann.lower() or "postmapping" in ann.lower():
                    node.add_tag("is_api_endpoint")
                    node.entity_type = EntityType.API_ENDPOINT

        return node

    def _handle_method_invocation(self, java_node) -> ASTNode:
        """Handle Java method call"""
        method_name = java_node.member if hasattr(java_node, "member") else "<unknown>"

        node = ASTNode(
            node_type="MethodInvocation",
            entity_type=EntityType.EXTERNAL_CALL,
            name=method_name,
        )

        # Tag database operations
        if any(keyword in method_name.lower() for keyword in ["query", "execute", "find", "save"]):
            node.add_tag("database_operation")
            node.entity_type = EntityType.DATABASE_QUERY

        return node

    def extract_entities(self, root_node: ASTNode) -> List[CodeEntity]:
        """Extract high-level entities"""
        entities = []

        # Find all methods
        methods = root_node.find_children_by_type(EntityType.METHOD)

        for method in methods:
            entity = CodeEntity(
                entity_type=method.entity_type,
                name=method.name or "<anonymous>",
                file_path=root_node.get_attribute("file_path", ""),
                line_start=method.line_start,
                line_end=method.line_end,
            )

            # Check security annotations
            if "has_authorization" in method.tags:
                entity.performs_authorization = True
            if "is_api_endpoint" in method.tags:
                entity.handles_user_input = True

            # Find database operations
            db_ops = [child for child in method.find_children_by_type(EntityType.DATABASE_QUERY)]
            if db_ops:
                entity.accesses_database = True

            # Extract method calls
            calls = [child for child in method.find_children_by_type(EntityType.EXTERNAL_CALL)]
            entity.calls = [call.name for call in calls if call.name]

            entities.append(entity)

        return entities
