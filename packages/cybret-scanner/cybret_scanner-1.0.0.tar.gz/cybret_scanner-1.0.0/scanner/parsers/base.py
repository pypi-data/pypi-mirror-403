"""
Base parser interface for language-agnostic AST parsing
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Set
from pathlib import Path


class EntityType(Enum):
    """Types of code entities that can be extracted"""

    # Structural
    FILE = "file"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"

    # Variables & Data
    VARIABLE = "variable"
    PARAMETER = "parameter"
    FIELD = "field"
    CONSTANT = "constant"

    # Flow Control
    IF_STATEMENT = "if_statement"
    LOOP = "loop"
    TRY_CATCH = "try_catch"
    RETURN = "return"

    # API & Network
    API_ENDPOINT = "api_endpoint"
    HTTP_ROUTE = "http_route"
    DATABASE_QUERY = "database_query"
    EXTERNAL_CALL = "external_call"

    # Security-Relevant
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INPUT_VALIDATION = "input_validation"
    SANITIZATION = "sanitization"


@dataclass
class ASTNode:
    """
    Language-agnostic representation of an AST node
    """

    node_type: str  # Language-specific node type (e.g., "FunctionDef", "MethodDeclaration")
    entity_type: EntityType  # Standardized entity type
    name: Optional[str] = None
    line_start: int = 0
    line_end: int = 0
    col_start: int = 0
    col_end: int = 0

    # Code content
    source_code: Optional[str] = None

    # Relationships
    parent: Optional["ASTNode"] = None
    children: List["ASTNode"] = field(default_factory=list)

    # Metadata
    attributes: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)

    # Security-relevant properties
    is_public: bool = False
    is_async: bool = False
    has_decorators: bool = False
    decorators: List[str] = field(default_factory=list)

    def add_child(self, child: "ASTNode"):
        """Add a child node"""
        child.parent = self
        self.children.append(child)

    def add_tag(self, tag: str):
        """Add a security or analysis tag"""
        self.tags.add(tag)

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get attribute value"""
        return self.attributes.get(key, default)

    def set_attribute(self, key: str, value: Any):
        """Set attribute value"""
        self.attributes[key] = value

    def find_children_by_type(self, entity_type: EntityType) -> List["ASTNode"]:
        """Recursively find all children of a given type"""
        results = []
        for child in self.children:
            if child.entity_type == entity_type:
                results.append(child)
            results.extend(child.find_children_by_type(entity_type))
        return results

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "node_type": self.node_type,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "col_start": self.col_start,
            "col_end": self.col_end,
            "source_code": self.source_code,
            "attributes": self.attributes,
            "tags": list(self.tags),
            "is_public": self.is_public,
            "is_async": self.is_async,
            "has_decorators": self.has_decorators,
            "decorators": self.decorators,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass
class CodeEntity:
    """
    High-level code entity extracted from source code
    """

    entity_type: EntityType
    name: str
    file_path: str
    line_start: int
    line_end: int

    # Source code
    source_code: Optional[str] = None

    # Relationships
    depends_on: List[str] = field(default_factory=list)  # Other entity names
    calls: List[str] = field(default_factory=list)  # Function/method calls

    # Security context
    handles_user_input: bool = False
    accesses_database: bool = False
    performs_authentication: bool = False
    performs_authorization: bool = False
    has_security_check: bool = False
    
    # BOLA-specific signals
    object_id_signal: int = 0  # 0-2 score for object ID usage
    has_auth_middleware: bool = False  # Middleware-based auth

    # Data flow
    input_sources: List[str] = field(default_factory=list)
    output_sinks: List[str] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "entity_type": self.entity_type.value,
            "name": self.name,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "source_code": self.source_code,
            "depends_on": self.depends_on,
            "calls": self.calls,
            "handles_user_input": self.handles_user_input,
            "accesses_database": self.accesses_database,
            "performs_authentication": self.performs_authentication,
            "performs_authorization": self.performs_authorization,
            "has_security_check": self.has_security_check,
            "input_sources": self.input_sources,
            "output_sinks": self.output_sinks,
            "metadata": self.metadata,
        }


class BaseParser(ABC):
    """
    Abstract base class for language-specific parsers
    """

    def __init__(self, language: str):
        self.language = language
        self.entities: List[CodeEntity] = []
        self.ast_nodes: List[ASTNode] = []

    @abstractmethod
    def parse_file(self, file_path: Path) -> ASTNode:
        """
        Parse a source file and return the root AST node

        Args:
            file_path: Path to the source file

        Returns:
            Root ASTNode representing the file
        """
        pass

    @abstractmethod
    def extract_entities(self, root_node: ASTNode) -> List[CodeEntity]:
        """
        Extract high-level code entities from AST

        Args:
            root_node: Root AST node

        Returns:
            List of extracted code entities
        """
        pass

    def parse_directory(self, directory: Path) -> List[ASTNode]:
        """
        Parse all supported files in a directory

        Args:
            directory: Directory path

        Returns:
            List of root AST nodes, one per file
        """
        ast_nodes = []
        for file_path in self._find_source_files(directory):
            try:
                root_node = self.parse_file(file_path)
                ast_nodes.append(root_node)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
        return ast_nodes

    @abstractmethod
    def _find_source_files(self, directory: Path) -> List[Path]:
        """
        Find all source files for this language in a directory

        Args:
            directory: Directory to search

        Returns:
            List of source file paths
        """
        pass

    def get_file_extension(self) -> List[str]:
        """Get supported file extensions for this language"""
        return []

    def supports_file(self, file_path: Path) -> bool:
        """Check if this parser supports a given file"""
        return file_path.suffix in self.get_file_extension()
