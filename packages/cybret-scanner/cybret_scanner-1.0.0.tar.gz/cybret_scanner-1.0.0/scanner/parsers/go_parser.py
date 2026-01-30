"""
Go parser using regex-based extraction (simplified implementation)

Note: This is a simplified parser. For production, consider using:
- go/parser package via subprocess
- tree-sitter for proper Go AST parsing
"""

import re
from pathlib import Path
from typing import List, Pattern

from scanner.parsers.base import BaseParser, ASTNode, CodeEntity, EntityType


class GoParser(BaseParser):
    """Simplified parser for Go source code"""

    # Regex patterns for Go code elements
    FUNCTION_PATTERN: Pattern = re.compile(
        r"func\s+(?:\((\w+)\s+\*?(\w+)\)\s+)?(\w+)\s*\((.*?)\)\s*(?:\((.*?)\))?\s*\{",
        re.MULTILINE | re.DOTALL
    )
    STRUCT_PATTERN: Pattern = re.compile(
        r"type\s+(\w+)\s+struct\s*\{",
        re.MULTILINE
    )
    INTERFACE_PATTERN: Pattern = re.compile(
        r"type\s+(\w+)\s+interface\s*\{",
        re.MULTILINE
    )

    def __init__(self):
        super().__init__(language="go")

    def get_file_extension(self) -> List[str]:
        """Supported Go file extensions"""
        return [".go"]

    def _find_source_files(self, directory: Path) -> List[Path]:
        """Find all Go files"""
        return list(directory.rglob("*.go"))

    def parse_file(self, file_path: Path) -> ASTNode:
        """Parse Go file using regex patterns"""
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        # Build root node
        root_node = ASTNode(
            node_type="Package",
            entity_type=EntityType.FILE,
            name=file_path.name,
            source_code=source_code,
        )
        root_node.set_attribute("file_path", str(file_path))

        # Extract structs
        for match in self.STRUCT_PATTERN.finditer(source_code):
            struct_name = match.group(1)
            struct_node = ASTNode(
                node_type="StructDeclaration",
                entity_type=EntityType.CLASS,
                name=struct_name,
                line_start=source_code[:match.start()].count("\n") + 1,
            )
            root_node.add_child(struct_node)

        # Extract interfaces
        for match in self.INTERFACE_PATTERN.finditer(source_code):
            interface_name = match.group(1)
            interface_node = ASTNode(
                node_type="InterfaceDeclaration",
                entity_type=EntityType.CLASS,
                name=interface_name,
                line_start=source_code[:match.start()].count("\n") + 1,
            )
            root_node.add_child(interface_node)

        # Extract functions
        for match in self.FUNCTION_PATTERN.finditer(source_code):
            receiver_var = match.group(1)
            receiver_type = match.group(2)
            func_name = match.group(3)
            params = match.group(4)

            # Determine if it's a method or function
            if receiver_type:
                entity_type = EntityType.METHOD
                full_name = f"{receiver_type}.{func_name}"
            else:
                entity_type = EntityType.FUNCTION
                full_name = func_name

            func_node = ASTNode(
                node_type="FunctionDeclaration",
                entity_type=entity_type,
                name=full_name,
                line_start=source_code[:match.start()].count("\n") + 1,
            )

            # Check if function is exported (starts with capital letter)
            if func_name and func_name[0].isupper():
                func_node.is_public = True

            # Extract parameter names
            param_list = []
            if params:
                # Simple extraction (not handling complex types)
                param_parts = params.split(",")
                for part in param_parts:
                    tokens = part.strip().split()
                    if tokens:
                        param_list.append(tokens[0])
            func_node.set_attribute("parameters", param_list)

            # Tag HTTP handlers
            if "http" in func_name.lower() or "handler" in func_name.lower():
                func_node.add_tag("is_api_endpoint")
                func_node.entity_type = EntityType.API_ENDPOINT

            root_node.add_child(func_node)

        return root_node

    def extract_entities(self, root_node: ASTNode) -> List[CodeEntity]:
        """Extract high-level entities"""
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
            )

            # Check if it's an API endpoint
            if "is_api_endpoint" in func.tags:
                entity.handles_user_input = True

            entities.append(entity)

        return entities
