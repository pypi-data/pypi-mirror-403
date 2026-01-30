"""
Neo4j graph builder for constructing code knowledge graphs
"""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver, Session
from dataclasses import asdict

from scanner.parsers.base import ASTNode, CodeEntity, EntityType
from scanner.config import settings


class GraphBuilder:
    """Builds and manages Neo4j knowledge graph for code analysis"""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        """
        Initialize Neo4j connection

        Args:
            uri: Neo4j connection URI (default from settings)
            user: Neo4j username (default from settings)
            password: Neo4j password (default from settings)
            database: Neo4j database name (default from settings)
        """
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        self.database = database or settings.neo4j_database

        self.driver: Optional[Driver] = None
        self._connect()

    def _connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            # Verify connectivity
            self.driver.verify_connectivity()
            print(f"[X] Connected to Neo4j at {self.uri}")
        except Exception as e:
            print(f"✗ Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            print("[X] Neo4j connection closed")

    def clear_graph(self):
        """Clear all nodes and relationships (USE WITH CAUTION)"""
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("[X] Graph cleared")

    def create_constraints(self):
        """Create Neo4j constraints and indexes for performance"""
        constraints = [
            # Uniqueness constraints
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Class) REQUIRE (c.name, c.file_path) IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (fn:Function) REQUIRE (fn.name, fn.file_path, fn.line_start) IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Method) REQUIRE (m.name, m.file_path, m.line_start) IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Endpoint) REQUIRE (e.name, e.file_path) IS UNIQUE",

            # Indexes for performance
            "CREATE INDEX IF NOT EXISTS FOR (f:File) ON (f.language)",
            "CREATE INDEX IF NOT EXISTS FOR (fn:Function) ON (fn.name)",
            "CREATE INDEX IF NOT EXISTS FOR (v:Vulnerability) ON (v.type)",
            "CREATE INDEX IF NOT EXISTS FOR (v:Vulnerability) ON (v.severity)",
        ]

        with self.driver.session(database=self.database) as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    print(f"Constraint/Index creation note: {e}")

        print("[X] Constraints and indexes created")

    def build_graph_from_ast(self, ast_nodes: List[ASTNode], scan_id: str) -> Dict[str, int]:
        """
        Build Neo4j graph from parsed AST nodes

        Args:
            ast_nodes: List of root AST nodes (one per file)
            scan_id: Unique identifier for this scan

        Returns:
            Statistics dictionary with node and relationship counts
        """
        stats = {"nodes": 0, "relationships": 0}

        with self.driver.session(database=self.database) as session:
            # Create scan node
            session.run(
                """
                CREATE (s:Scan {
                    scan_id: $scan_id,
                    timestamp: datetime(),
                    status: 'in_progress'
                })
                """,
                scan_id=scan_id,
            )

            # Process each file
            for file_node in ast_nodes:
                file_stats = self._create_file_subgraph(session, file_node, scan_id)
                stats["nodes"] += file_stats["nodes"]
                stats["relationships"] += file_stats["relationships"]

            # Mark scan as complete
            session.run(
                """
                MATCH (s:Scan {scan_id: $scan_id})
                SET s.status = 'completed'
                """,
                scan_id=scan_id,
            )

        print(f"[X] Graph built: {stats['nodes']} nodes, {stats['relationships']} relationships")
        return stats

    def _create_file_subgraph(
        self, session: Session, file_node: ASTNode, scan_id: str
    ) -> Dict[str, int]:
        """Create subgraph for a single file"""
        stats = {"nodes": 0, "relationships": 0}

        file_path = file_node.get_attribute("file_path", "")

        # Create File node
        result = session.run(
            """
            MERGE (f:File {path: $path})
            SET f.name = $name,
                f.entity_type = $entity_type
            WITH f
            MATCH (s:Scan {scan_id: $scan_id})
            MERGE (s)-[:SCANNED]->(f)
            RETURN f
            """,
            path=file_path,
            name=file_node.name,
            entity_type=file_node.entity_type.value,
            scan_id=scan_id,
        )
        stats["nodes"] += 1
        stats["relationships"] += 1

        # Recursively create nodes for children
        for child in file_node.children:
            child_stats = self._create_ast_node(session, child, file_path, parent_id=f"file:{file_path}")
            stats["nodes"] += child_stats["nodes"]
            stats["relationships"] += child_stats["relationships"]

        return stats

    def _create_ast_node(
        self, session: Session, ast_node: ASTNode, file_path: str, parent_id: str
    ) -> Dict[str, int]:
        """Recursively create AST node and its children in graph"""
        stats = {"nodes": 0, "relationships": 0}

        # Determine node label based on entity type
        label = self._get_node_label(ast_node.entity_type)

        # Create unique ID for this node
        node_id = f"{file_path}:{ast_node.name}:{ast_node.line_start}"

        # Build properties
        props = {
            "id": node_id,
            "name": ast_node.name or "<anonymous>",
            "node_type": ast_node.node_type,
            "entity_type": ast_node.entity_type.value,
            "file_path": file_path,
            "line_start": ast_node.line_start,
            "line_end": ast_node.line_end,
            "col_start": ast_node.col_start,
            "col_end": ast_node.col_end,
            "is_public": ast_node.is_public,
            "is_async": ast_node.is_async,
            "has_decorators": ast_node.has_decorators,
            "decorators": ast_node.decorators,
            "tags": list(ast_node.tags),
        }

        # Add custom attributes
        props.update(ast_node.attributes)

        # Create node
        query = f"""
        MERGE (n:{label} {{id: $props.id}})
        SET n += $props
        WITH n
        MATCH (f:File {{path: $file_path}})
        MERGE (f)-[:CONTAINS]->(n)
        RETURN n
        """

        session.run(query, props=props, file_path=file_path)
        stats["nodes"] += 1
        stats["relationships"] += 1

        # Create CALLS relationships for function calls
        if ast_node.entity_type == EntityType.EXTERNAL_CALL:
            # This will be used later to create CALLS relationships
            pass

        # Recursively create children
        for child in ast_node.children:
            child_stats = self._create_ast_node(session, child, file_path, parent_id=node_id)
            stats["nodes"] += child_stats["nodes"]
            stats["relationships"] += child_stats["relationships"]

            # Create parent-child relationship
            session.run(
                f"""
                MATCH (parent {{id: $parent_id}})
                MATCH (child {{id: $child_id}})
                MERGE (parent)-[:HAS_CHILD]->(child)
                """,
                parent_id=node_id,
                child_id=f"{file_path}:{child.name}:{child.line_start}",
            )
            stats["relationships"] += 1

        return stats

    def _get_node_label(self, entity_type: EntityType) -> str:
        """Map EntityType to Neo4j node label"""
        label_map = {
            EntityType.FILE: "File",
            EntityType.MODULE: "Module",
            EntityType.CLASS: "Class",
            EntityType.FUNCTION: "Function",
            EntityType.METHOD: "Method",
            EntityType.VARIABLE: "Variable",
            EntityType.PARAMETER: "Parameter",
            EntityType.API_ENDPOINT: "Endpoint",
            EntityType.DATABASE_QUERY: "DatabaseQuery",
            EntityType.EXTERNAL_CALL: "Call",
            EntityType.IF_STATEMENT: "IfStatement",
            EntityType.LOOP: "Loop",
            EntityType.RETURN: "Return",
        }
        return label_map.get(entity_type, "CodeNode")

    def create_entities(self, entities: List[CodeEntity], scan_id: str) -> int:
        """
        Create entity nodes with security context

        Args:
            entities: List of extracted code entities
            scan_id: Scan identifier

        Returns:
            Number of entities created
        """
        count = 0

        with self.driver.session(database=self.database) as session:
            for entity in entities:
                label = self._get_node_label(entity.entity_type)

                # Create entity node with security properties
                session.run(
                    f"""
                    MERGE (e:{label} {{
                        name: $name,
                        file_path: $file_path,
                        line_start: $line_start
                    }})
                    SET e.entity_type = $entity_type,
                        e.line_end = $line_end,
                        e.handles_user_input = $handles_user_input,
                        e.accesses_database = $accesses_database,
                        e.performs_authentication = $performs_authentication,
                        e.performs_authorization = $performs_authorization,
                        e.has_security_check = $has_security_check,
                        e.object_id_signal = $object_id_signal,
                        e.has_auth_middleware = $has_auth_middleware
                    WITH e
                    MATCH (s:Scan {{scan_id: $scan_id}})
                    MERGE (s)-[:HAS_ENTITY]->(e)
                    """,
                    name=entity.name,
                    file_path=entity.file_path,
                    line_start=entity.line_start,
                    line_end=entity.line_end,
                    entity_type=entity.entity_type.value,
                    handles_user_input=entity.handles_user_input,
                    accesses_database=entity.accesses_database,
                    performs_authentication=entity.performs_authentication,
                    performs_authorization=entity.performs_authorization,
                    has_security_check=entity.has_security_check,
                    object_id_signal=entity.object_id_signal,
                    has_auth_middleware=entity.has_auth_middleware,
                    scan_id=scan_id,
                )

                count += 1

        print(f"[X] Created {count} entity nodes")
        return count

    def create_call_relationships(self, scan_id: str) -> int:
        """
        Create CALLS relationships between functions based on call patterns

        Args:
            scan_id: Scan identifier

        Returns:
            Number of relationships created
        """
        with self.driver.session(database=self.database) as session:
            # Find all Call nodes and link them to their targets
            result = session.run(
                """
                MATCH (s:Scan {scan_id: $scan_id})-[:SCANNED]->(:File)-[:CONTAINS*]->(caller)
                WHERE caller:Function OR caller:Method OR caller:Endpoint
                MATCH (caller)-[:HAS_CHILD*]->(call:Call)
                MATCH (target)
                WHERE (target:Function OR target:Method) AND target.name = call.name
                MERGE (caller)-[:CALLS]->(target)
                RETURN count(*) as count
                """,
                scan_id=scan_id,
            )

            record = result.single()
            count = record["count"] if record else 0
            print(f"[X] Created {count} CALLS relationships")
            return count

    def create_route_graph(self, routes: List, mounts: List, scan_id: str) -> Dict[str, int]:
        """
        Create Route Graph in Neo4j from extracted routes and mounts

        Args:
            routes: List of RouteSpec objects
            mounts: List of RouterMount objects
            scan_id: Scan identifier

        Returns:
            Statistics dictionary
        """
        stats = {"routes": 0, "middleware": 0, "mounts": 0, "relationships": 0}

        with self.driver.session(database=self.database) as session:
            # Create Route nodes
            for route in routes:
                route_dict = route.to_dict()

                session.run(
                    """
                    MATCH (scan:Scan {scan_id: $scan_id})
                    CREATE (route:Route {
                        route_id: $route_id,
                        method: $method,
                        path: $path,
                        full_path: $full_path,
                        file_path: $file_path,
                        line_start: $line_start,
                        line_end: $line_end,
                        requires_auth: $requires_auth,
                        auth_middleware_names: $auth_middleware_names,
                        framework: $framework,
                        router_name: $router_name,
                        mount_prefix: $mount_prefix
                    })
                    MERGE (scan)-[:HAS_ROUTE]->(route)
                    """,
                    scan_id=scan_id,
                    route_id=route_dict['route_id'],
                    method=route_dict['method'],
                    path=route_dict['path'],
                    full_path=route_dict['full_path'],
                    file_path=route_dict['file_path'],
                    line_start=route_dict['line_start'],
                    line_end=route_dict['line_end'],
                    requires_auth=route_dict['requires_auth'],
                    auth_middleware_names=route_dict['auth_middleware_names'],
                    framework=route_dict['framework'],
                    router_name=route_dict.get('router_name', ''),
                    mount_prefix=route_dict.get('mount_prefix', '')
                )

                stats['routes'] += 1

                # Create middleware chain
                for mw_info in route.middleware:
                    mw_dict = mw_info.to_dict()
                    handler_dict = mw_dict['handler_ref']

                    # Create or merge Middleware node
                    session.run(
                        """
                        MATCH (route:Route {route_id: $route_id})
                        MERGE (mw:Middleware {
                            handler_id: $handler_id,
                            name: $name
                        })
                        ON CREATE SET
                            mw.kind = $kind,
                            mw.is_call = $is_call,
                            mw.module_name = $module_name,
                            mw.function_name = $function_name
                        CREATE (route)-[:USES_MIDDLEWARE {
                            order: $order,
                            middleware_type: $middleware_type,
                            is_auth: $is_auth,
                            confidence: $confidence
                        }]->(mw)
                        """,
                        route_id=route_dict['route_id'],
                        handler_id=handler_dict['handler_id'],
                        name=handler_dict['name'],
                        kind=handler_dict['kind'],
                        is_call=handler_dict['is_call'],
                        module_name=handler_dict.get('module_name', ''),
                        function_name=handler_dict.get('function_name', ''),
                        order=mw_dict['order'],
                        middleware_type=mw_dict['middleware_type'],
                        is_auth=mw_dict['is_auth'],
                        confidence=mw_dict['classification_confidence']
                    )

                    stats['middleware'] += 1
                    stats['relationships'] += 1

                # Create handler relationship
                if route.handler:
                    handler_dict = route.handler.to_dict()

                    session.run(
                        """
                        MATCH (route:Route {route_id: $route_id})
                        MERGE (handler:Handler {
                            handler_id: $handler_id,
                            name: $name
                        })
                        ON CREATE SET
                            handler.kind = $kind,
                            handler.is_call = $is_call,
                            handler.file_path = $file_path,
                            handler.line_start = $line_start,
                            handler.module_name = $module_name,
                            handler.function_name = $function_name
                        CREATE (route)-[:HANDLED_BY]->(handler)
                        """,
                        route_id=route_dict['route_id'],
                        handler_id=handler_dict['handler_id'],
                        name=handler_dict['name'],
                        kind=handler_dict['kind'],
                        is_call=handler_dict['is_call'],
                        file_path=handler_dict['file_path'],
                        line_start=handler_dict['line_start'],
                        module_name=handler_dict.get('module_name', ''),
                        function_name=handler_dict.get('function_name', '')
                    )

                    stats['relationships'] += 1

            # Create RouterMount nodes
            for mount in mounts:
                mount_dict = mount.to_dict()

                session.run(
                    """
                    MATCH (scan:Scan {scan_id: $scan_id})
                    CREATE (mount:RouterMount {
                        mount_id: $mount_id,
                        prefix: $prefix,
                        router_name: $router_name,
                        file_path: $file_path,
                        line_start: $line_start
                    })
                    MERGE (scan)-[:HAS_MOUNT]->(mount)
                    """,
                    scan_id=scan_id,
                    mount_id=mount_dict['mount_id'],
                    prefix=mount_dict['prefix'],
                    router_name=mount_dict['router_name'],
                    file_path=mount_dict['file_path'],
                    line_start=mount_dict['line_start']
                )

                stats['mounts'] += 1

        print(f"[X] Route Graph: {stats['routes']} routes, {stats['middleware']} middleware, {stats['mounts']} mounts")
        return stats

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
