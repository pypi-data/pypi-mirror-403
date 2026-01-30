"""
Intent Graph Schema - Semantic Nodes and Relationships

Extends the basic call graph with semantic understanding of:
- Actors (WHO)
- Resources (WHAT)
- States (state transitions)
- Capabilities (actions)
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


class ActorType(Enum):
    """Type of actor in the system"""
    USER = "user"
    ADMIN = "admin"
    SERVICE = "service"
    ANONYMOUS = "anonymous"


class ResourceType(Enum):
    """Type of resource"""
    ENTITY = "entity"        # Database entity (User, Order, etc.)
    FILE = "file"            # File or document
    DATA = "data"            # Generic data
    SENSITIVE = "sensitive"  # Sensitive information


class Sensitivity(Enum):
    """Data sensitivity level"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"


class ActionType(Enum):
    """Type of capability/action"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    MODIFY = "modify"


@dataclass
class Actor:
    """
    Represents an actor (WHO) in the system

    Examples:
    - Actor(id="authenticated_user", type=USER)
    - Actor(id="admin", type=ADMIN, capabilities=["approve", "delete"])
    """
    id: str
    type: ActorType
    capabilities: List[str] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


@dataclass
class Resource:
    """
    Represents a resource (WHAT) in the system

    Examples:
    - Resource(id="Order", type=ENTITY, owner_field="user_id", sensitivity=CONFIDENTIAL)
    - Resource(id="User", type=ENTITY, sensitive_fields=["ssn", "password"])
    """
    id: str
    type: ResourceType
    owner_field: Optional[str] = None  # Field that indicates ownership (user_id, owner_id)
    sensitive_fields: List[str] = None  # Fields that are sensitive
    sensitivity: Sensitivity = Sensitivity.INTERNAL

    def __post_init__(self):
        if self.sensitive_fields is None:
            self.sensitive_fields = []


@dataclass
class State:
    """
    Represents a state field (state machine)

    Examples:
    - State(id="order.status", transitions=["pending", "paid", "shipped"], is_monotonic=True)
    - State(id="user.is_admin", is_sensitive=True)
    """
    id: str
    resource_id: str
    field_name: str
    transitions: List[str] = None  # Valid state transitions
    is_sensitive: bool = False     # Is this a sensitive field (role, admin, balance)?
    is_monotonic: bool = False     # Can only move forward, not backward

    def __post_init__(self):
        if self.transitions is None:
            self.transitions = []


@dataclass
class Capability:
    """
    Represents a capability/action in the system

    Examples:
    - Capability(id="cancel_order", action=DELETE, requires_role=["admin", "owner"])
    - Capability(id="approve_order", action=MODIFY, requires_role=["admin"])
    """
    id: str
    action: ActionType
    requires_role: List[str] = None  # Roles required to perform this action
    affects_state: List[str] = None  # Which states does this modify
    function_name: str = None        # Source code function

    def __post_init__(self):
        if self.requires_role is None:
            self.requires_role = []
        if self.affects_state is None:
            self.affects_state = []


@dataclass
class OwnershipInvariant:
    """
    Represents an ownership invariant

    Example:
    - "Users can only access their own orders"
    - "Only admins can modify roles"
    """
    resource: str
    actor: str
    condition: str  # "actor.id == resource.user_id"
    confidence: float = 0.0  # Statistical confidence (0-1)
    examples: List[str] = None  # Code examples where this pattern appears

    def __post_init__(self):
        if self.examples is None:
            self.examples = []


class IntentGraphSchema:
    """
    Manages the intent graph schema in Neo4j
    """

    @staticmethod
    def get_constraint_queries() -> List[str]:
        """Get Cypher queries to create constraints for intent nodes"""
        return [
            # Actor constraints
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Actor) REQUIRE a.id IS UNIQUE",

            # Resource constraints
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Resource) REQUIRE r.id IS UNIQUE",

            # State constraints
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:State) REQUIRE s.id IS UNIQUE",

            # Capability constraints
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Capability) REQUIRE c.id IS UNIQUE",

            # Invariant constraints
            "CREATE CONSTRAINT IF NOT EXISTS FOR (i:OwnershipInvariant) REQUIRE i.id IS UNIQUE",

            # Indexes
            "CREATE INDEX IF NOT EXISTS FOR (a:Actor) ON (a.type)",
            "CREATE INDEX IF NOT EXISTS FOR (r:Resource) ON (r.sensitivity)",
            "CREATE INDEX IF NOT EXISTS FOR (s:State) ON (s.is_sensitive)",
        ]

    @staticmethod
    def create_actor_node_query() -> str:
        """Cypher query to create Actor node"""
        return """
        MERGE (a:Actor {id: $id})
        SET a.type = $type,
            a.capabilities = $capabilities
        RETURN a
        """

    @staticmethod
    def create_resource_node_query() -> str:
        """Cypher query to create Resource node"""
        return """
        MERGE (r:Resource {id: $id})
        SET r.type = $type,
            r.owner_field = $owner_field,
            r.sensitive_fields = $sensitive_fields,
            r.sensitivity = $sensitivity
        RETURN r
        """

    @staticmethod
    def create_state_node_query() -> str:
        """Cypher query to create State node"""
        return """
        MERGE (s:State {id: $id})
        SET s.resource_id = $resource_id,
            s.field_name = $field_name,
            s.transitions = $transitions,
            s.is_sensitive = $is_sensitive,
            s.is_monotonic = $is_monotonic
        RETURN s
        """

    @staticmethod
    def create_capability_node_query() -> str:
        """Cypher query to create Capability node"""
        return """
        MERGE (c:Capability {id: $id})
        SET c.action = $action,
            c.requires_role = $requires_role,
            c.affects_state = $affects_state,
            c.function_name = $function_name
        RETURN c
        """

    @staticmethod
    def create_ownership_relationship_query() -> str:
        """Cypher query to create OWNS relationship"""
        return """
        MATCH (actor:Actor {id: $actor_id})
        MATCH (resource:Resource {id: $resource_id})
        MERGE (actor)-[:OWNS]->(resource)
        """

    @staticmethod
    def create_initiates_relationship_query() -> str:
        """Cypher query to create INITIATES relationship"""
        return """
        MATCH (actor:Actor {id: $actor_id})
        MATCH (capability:Capability {id: $capability_id})
        MERGE (actor)-[:INITIATES]->(capability)
        """

    @staticmethod
    def create_modifies_relationship_query() -> str:
        """Cypher query to create MODIFIES relationship"""
        return """
        MATCH (capability:Capability {id: $capability_id})
        MATCH (state:State {id: $state_id})
        MERGE (capability)-[:MODIFIES]->(state)
        """
