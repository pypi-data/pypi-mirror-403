"""
Route Graph Models - Production-ready route analysis for Express/FastAPI/Flask

This module defines the data structures for representing HTTP routes,
middleware chains, and their relationships in a knowledge graph.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import hashlib


class HandlerKind(Enum):
    """Type of route handler/middleware reference"""
    CALL = "call"  # security.appendUserId()
    MEMBER = "member"  # payment.getPaymentMethods
    IDENTIFIER = "identifier"  # isAuthenticated
    INLINE = "inline"  # (req, res) => {...}
    DYNAMIC = "dynamic"  # Complex expression


class MiddlewareType(Enum):
    """Classification of middleware purpose"""
    AUTH = "auth"  # Authentication (login_required, jwt, etc.)
    AUTHZ = "authz"  # Authorization (admin_required, permission check)
    ENRICHMENT = "enrichment"  # Data enrichment (appendUserId, addMetadata)
    VALIDATION = "validation"  # Input validation
    RATE_LIMIT = "rate_limit"  # Rate limiting
    CORS = "cors"  # CORS handling
    LOGGING = "logging"  # Request logging
    ERROR_HANDLER = "error_handler"  # Error handling
    UNKNOWN = "unknown"  # Unclassified


@dataclass
class HandlerRef:
    """
    Reference to a route handler or middleware

    Provides stable identification across different handler types
    """
    kind: HandlerKind
    name: str
    is_call: bool  # True if handler is invoked (has parentheses)
    file_path: str
    line_start: int
    line_end: int = 0

    # Optional metadata
    module_name: Optional[str] = None  # e.g., "security" from security.appendUserId
    function_name: Optional[str] = None  # e.g., "appendUserId"

    def __post_init__(self):
        if self.line_end == 0:
            self.line_end = self.line_start

    @property
    def handler_id(self) -> str:
        """Generate stable ID for this handler"""
        content = f"{self.file_path}:{self.line_start}:{self.name}"
        return hashlib.sha1(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handler_id": self.handler_id,
            "kind": self.kind.value,
            "name": self.name,
            "is_call": self.is_call,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "module_name": self.module_name,
            "function_name": self.function_name
        }


@dataclass
class MiddlewareInfo:
    """
    Middleware in a route's execution chain
    """
    handler_ref: HandlerRef
    order: int  # Position in middleware chain (0 = first)
    middleware_type: MiddlewareType = MiddlewareType.UNKNOWN

    # Classification confidence
    classification_confidence: float = 0.0
    classification_reason: str = ""

    @property
    def is_auth_middleware(self) -> bool:
        """Check if this is authentication middleware"""
        return self.middleware_type in {MiddlewareType.AUTH, MiddlewareType.AUTHZ}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handler_ref": self.handler_ref.to_dict(),
            "order": self.order,
            "middleware_type": self.middleware_type.value,
            "is_auth": self.is_auth_middleware,
            "classification_confidence": self.classification_confidence,
            "classification_reason": self.classification_reason
        }


@dataclass
class RouteSpec:
    """
    Complete specification of an HTTP route

    Represents a single route with its middleware chain and handler
    """
    # Route identification
    method: str  # GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD, ALL, USE
    path: str  # /api/users/:id

    # Source location
    file_path: str
    line_start: int
    line_end: int

    # Middleware chain (in execution order)
    middleware: List[MiddlewareInfo] = field(default_factory=list)

    # Final route handler
    handler: Optional[HandlerRef] = None

    # Router mounting context
    mount_prefix: str = ""  # If mounted under a prefix
    router_name: Optional[str] = None  # Name of router if from router.get(...)

    # Security analysis
    requires_auth: bool = False
    auth_middleware_names: List[str] = field(default_factory=list)

    # Framework-specific metadata
    framework: str = "express"  # express, flask, fastapi

    def __post_init__(self):
        self.method = self.method.upper()

        # Classify middleware and determine auth requirements
        self._analyze_middleware()

    @property
    def route_id(self) -> str:
        """Generate stable ID for this route"""
        content = f"{self.file_path}:{self.line_start}:{self.method}:{self.path}"
        return hashlib.sha1(content.encode()).hexdigest()[:16]

    @property
    def full_path(self) -> str:
        """Get complete path including mount prefix"""
        if self.mount_prefix:
            return f"{self.mount_prefix.rstrip('/')}/{self.path.lstrip('/')}"
        return self.path

    @property
    def handler_name(self) -> str:
        """Get handler name for display"""
        if self.handler:
            return self.handler.name
        return "<no_handler>"

    def _analyze_middleware(self):
        """Analyze middleware chain to determine auth requirements"""
        auth_mw = []
        for mw in self.middleware:
            if mw.is_auth_middleware:
                auth_mw.append(mw.handler_ref.name)

        self.requires_auth = len(auth_mw) > 0
        self.auth_middleware_names = auth_mw

    def add_middleware(self, handler_ref: HandlerRef, middleware_type: MiddlewareType = MiddlewareType.UNKNOWN):
        """Add middleware to the chain"""
        mw_info = MiddlewareInfo(
            handler_ref=handler_ref,
            order=len(self.middleware),
            middleware_type=middleware_type
        )
        self.middleware.append(mw_info)
        self._analyze_middleware()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "route_id": self.route_id,
            "method": self.method,
            "path": self.path,
            "full_path": self.full_path,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "middleware": [mw.to_dict() for mw in self.middleware],
            "handler": self.handler.to_dict() if self.handler else None,
            "mount_prefix": self.mount_prefix,
            "router_name": self.router_name,
            "requires_auth": self.requires_auth,
            "auth_middleware_names": self.auth_middleware_names,
            "framework": self.framework
        }


@dataclass
class RouterMount:
    """
    Represents a router being mounted at a prefix

    Example: app.use('/api', apiRouter)
    """
    prefix: str
    router_name: str
    file_path: str
    line_start: int

    # Middleware applied to all routes in this mount
    middleware: List[MiddlewareInfo] = field(default_factory=list)

    @property
    def mount_id(self) -> str:
        """Generate stable ID for this mount"""
        content = f"{self.file_path}:{self.line_start}:{self.prefix}:{self.router_name}"
        return hashlib.sha1(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mount_id": self.mount_id,
            "prefix": self.prefix,
            "router_name": self.router_name,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "middleware": [mw.to_dict() for mw in self.middleware]
        }


class MiddlewareClassifier:
    """
    Rule-based classifier for middleware type detection

    Classifies middleware based on naming patterns and known libraries
    """

    # Auth-related patterns (case-insensitive)
    AUTH_PATTERNS = [
        'auth', 'authenticate', 'authenticated', 'jwt', 'token',
        'verify', 'login', 'loggedin', 'ensure', 'require',
        'session', 'passport', 'oauth'
    ]

    AUTHZ_PATTERNS = [
        'authz', 'authorize', 'authorized', 'permission', 'access',
        'admin', 'role', 'acl', 'can', 'ability', 'grant'
    ]

    ENRICHMENT_PATTERNS = [
        'append', 'add', 'attach', 'inject', 'enrich',
        'populate', 'load', 'fetch', 'get'
    ]

    VALIDATION_PATTERNS = [
        'validate', 'check', 'verify', 'sanitize', 'clean',
        'parse', 'schema', 'validator'
    ]

    RATE_LIMIT_PATTERNS = [
        'ratelimit', 'rate', 'limit', 'throttle', 'quota'
    ]

    CORS_PATTERNS = ['cors', 'crossorigin', 'origin']

    LOGGING_PATTERNS = ['log', 'logger', 'morgan', 'winston']

    ERROR_PATTERNS = ['error', 'exception', 'catch', 'handle']

    @classmethod
    def classify(cls, handler_ref: HandlerRef) -> tuple[MiddlewareType, float, str]:
        """
        Classify middleware type based on handler reference

        Returns: (MiddlewareType, confidence, reason)
        """
        name_lower = handler_ref.name.lower()

        # Check each pattern category
        if cls._matches_patterns(name_lower, cls.AUTH_PATTERNS):
            return (MiddlewareType.AUTH, 0.9, f"Name matches auth pattern: {handler_ref.name}")

        if cls._matches_patterns(name_lower, cls.AUTHZ_PATTERNS):
            return (MiddlewareType.AUTHZ, 0.9, f"Name matches authz pattern: {handler_ref.name}")

        if cls._matches_patterns(name_lower, cls.ENRICHMENT_PATTERNS):
            return (MiddlewareType.ENRICHMENT, 0.7, f"Name matches enrichment pattern: {handler_ref.name}")

        if cls._matches_patterns(name_lower, cls.VALIDATION_PATTERNS):
            return (MiddlewareType.VALIDATION, 0.8, f"Name matches validation pattern: {handler_ref.name}")

        if cls._matches_patterns(name_lower, cls.RATE_LIMIT_PATTERNS):
            return (MiddlewareType.RATE_LIMIT, 0.9, f"Name matches rate limit pattern: {handler_ref.name}")

        if cls._matches_patterns(name_lower, cls.CORS_PATTERNS):
            return (MiddlewareType.CORS, 0.95, f"Name matches CORS pattern: {handler_ref.name}")

        if cls._matches_patterns(name_lower, cls.LOGGING_PATTERNS):
            return (MiddlewareType.LOGGING, 0.8, f"Name matches logging pattern: {handler_ref.name}")

        if cls._matches_patterns(name_lower, cls.ERROR_PATTERNS):
            return (MiddlewareType.ERROR_HANDLER, 0.7, f"Name matches error handler pattern: {handler_ref.name}")

        return (MiddlewareType.UNKNOWN, 0.0, "No pattern match")

    @staticmethod
    def _matches_patterns(name: str, patterns: List[str]) -> bool:
        """Check if name contains any of the patterns"""
        return any(pattern in name for pattern in patterns)


# Export all models
__all__ = [
    'HandlerKind',
    'MiddlewareType',
    'HandlerRef',
    'MiddlewareInfo',
    'RouteSpec',
    'RouterMount',
    'MiddlewareClassifier'
]
