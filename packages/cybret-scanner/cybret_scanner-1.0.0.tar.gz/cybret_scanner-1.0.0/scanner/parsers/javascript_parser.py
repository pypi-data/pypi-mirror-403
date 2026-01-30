"""
JavaScript/TypeScript parser using esprima for AST extraction
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from scanner.parsers.base import BaseParser, ASTNode, CodeEntity, EntityType


class JavaScriptParser(BaseParser):
    """Parser for JavaScript and TypeScript code"""

    def __init__(self):
        super().__init__(language="javascript")
        self._check_dependencies()

    def _check_dependencies(self):
        """Verify Node.js and esprima are available"""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Node.js is not installed or not in PATH")
        except Exception as e:
            print(f"Warning: Node.js not available: {e}")
            print("JavaScript parsing will be limited")

    def get_file_extension(self) -> List[str]:
        """Supported JavaScript/TypeScript file extensions"""
        return [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]

    def _find_source_files(self, directory: Path) -> List[Path]:
        """Find all JavaScript/TypeScript files"""
        js_files = []
        for ext in self.get_file_extension():
            js_files.extend(directory.rglob(f"*{ext}"))
        return js_files

    def parse_file(self, file_path: Path) -> ASTNode:
        """Parse JavaScript/TypeScript file using esprima"""
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        # Parse using esprima via Node.js
        esprima_ast = self._parse_with_esprima(source_code, file_path)

        # Build language-agnostic AST
        root_node = ASTNode(
            node_type="Program",
            entity_type=EntityType.FILE,
            name=file_path.name,
            source_code=source_code,
        )
        root_node.set_attribute("file_path", str(file_path))

        # Store raw ESTree AST for route extraction
        root_node.set_attribute("raw_ast", esprima_ast)

        # Convert esprima AST to our format
        if esprima_ast and "body" in esprima_ast:
            for stmt in esprima_ast["body"]:
                self._visit_node(stmt, root_node)

        return root_node

    def extract_routes(self, ast_node: ASTNode):
        """
        Extract HTTP routes from AST (Express/TypeScript)

        Returns: (routes, mounts) tuple
        """
        from scanner.extractors.route_graph_extractor import RouteGraphExtractor

        raw_ast = ast_node.get_attribute("raw_ast")
        file_path = ast_node.get_attribute("file_path")

        if not raw_ast or not file_path:
            return [], []

        extractor = RouteGraphExtractor()
        routes, mounts = extractor.extract_routes_from_ast(raw_ast, file_path)

        return routes, mounts

    def extract_symbols(self, ast_node: ASTNode):
        """
        Extract imports, exports, and function definitions from AST

        Returns: (imports, exports, functions) tuple
        """
        from scanner.extractors.symbol_table import ImportInfo, ExportInfo, FunctionDef

        raw_ast = ast_node.get_attribute("raw_ast")
        file_path = ast_node.get_attribute("file_path")

        if not raw_ast or not file_path:
            return [], [], []

        # Normalize to absolute path for consistent lookups
        file_path = str(Path(file_path).resolve())

        imports = []
        exports = []
        functions = []

        # Walk AST to extract symbols
        for node in raw_ast.get("body", []):
            node_type = node.get("type")

            # Extract imports
            if node_type == "ImportDeclaration":
                import_infos = self._extract_import(node, file_path)
                imports.extend(import_infos)

            # Extract exports
            elif node_type in ["ExportNamedDeclaration", "ExportDefaultDeclaration", "ExportAllDeclaration"]:
                export_infos = self._extract_export(node, file_path)
                exports.extend(export_infos)

            # Extract function declarations
            elif node_type == "FunctionDeclaration":
                func_def = self._extract_function(node, file_path, is_exported=False)
                if func_def:
                    functions.append(func_def)

        return imports, exports, functions

    def _extract_import(self, node: Dict, file_path: str) -> List:
        """Extract import statement (can return multiple ImportInfo for named imports)"""
        from scanner.extractors.symbol_table import ImportInfo

        source = node.get("source", {}).get("value", "")
        if not source:
            return []

        line_number = node.get("loc", {}).get("start", {}).get("line", 0)
        imports = []

        # import * as security from './lib/insecurity'
        specifiers = node.get("specifiers", [])
        if not specifiers:
            return []

        # Check for namespace import first (takes precedence)
        for specifier in specifiers:
            spec_type = specifier.get("type")

            if spec_type == "ImportNamespaceSpecifier":
                # import * as security
                local_name = specifier.get("local", {}).get("name", "")
                return [ImportInfo(
                    local_name=local_name,
                    source_module=source,
                    import_type="namespace",
                    imported_names=[],
                    file_path=file_path,
                    line_number=line_number
                )]

            elif spec_type == "ImportDefaultSpecifier":
                # import config from 'config'
                local_name = specifier.get("local", {}).get("name", "")
                imports.append(ImportInfo(
                    local_name=local_name,
                    source_module=source,
                    import_type="default",
                    imported_names=[],
                    file_path=file_path,
                    line_number=line_number
                ))

            elif spec_type == "ImportSpecifier":
                # import { foo, bar } from './lib'
                local_name = specifier.get("local", {}).get("name", "")
                imported_name = specifier.get("imported", {}).get("name", local_name)
                imports.append(ImportInfo(
                    local_name=local_name,
                    source_module=source,
                    import_type="named",
                    imported_names=[imported_name],
                    file_path=file_path,
                    line_number=line_number
                ))

        return imports

    def _extract_export(self, node: Dict, file_path: str) -> List:
        """Extract export statement"""
        from scanner.extractors.symbol_table import ExportInfo

        exports = []
        node_type = node.get("type")

        if node_type == "ExportNamedDeclaration":
            declaration = node.get("declaration")

            if declaration:
                # export function verify()
                if declaration.get("type") == "FunctionDeclaration":
                    name = declaration.get("id", {}).get("name", "")
                    is_async = declaration.get("async", False)
                    loc = declaration.get("loc", {})
                    exports.append(ExportInfo(
                        export_name=name,
                        export_type="function",
                        is_async=is_async,
                        file_path=file_path,
                        line_start=loc.get("start", {}).get("line", 0),
                        line_end=loc.get("end", {}).get("line", 0)
                    ))

                # export const foo = ...
                elif declaration.get("type") == "VariableDeclaration":
                    for decl in declaration.get("declarations", []):
                        name = decl.get("id", {}).get("name", "")
                        if name:
                            loc = decl.get("loc", {})
                            exports.append(ExportInfo(
                                export_name=name,
                                export_type="const",
                                file_path=file_path,
                                line_start=loc.get("start", {}).get("line", 0),
                                line_end=loc.get("end", {}).get("line", 0)
                            ))

            # export { foo, bar } from './lib' (re-export)
            elif node.get("source"):
                source_module = node.get("source", {}).get("value", "")
                for specifier in node.get("specifiers", []):
                    exported_name = specifier.get("exported", {}).get("name", "")
                    if exported_name:
                        exports.append(ExportInfo(
                            export_name=exported_name,
                            export_type="function",
                            file_path=file_path,
                            line_start=node.get("loc", {}).get("start", {}).get("line", 0),
                            line_end=node.get("loc", {}).get("end", {}).get("line", 0),
                            source_module=source_module
                        ))

            # export { foo, bar } (local exports)
            else:
                for specifier in node.get("specifiers", []):
                    local_name = specifier.get("local", {}).get("name", "")
                    exported_name = specifier.get("exported", {}).get("name", local_name)
                    if exported_name:
                        exports.append(ExportInfo(
                            export_name=exported_name,
                            export_type="function",  # Could be function, const, etc.
                            file_path=file_path,
                            line_start=node.get("loc", {}).get("start", {}).get("line", 0),
                            line_end=node.get("loc", {}).get("end", {}).get("line", 0)
                        ))

        elif node_type == "ExportDefaultDeclaration":
            # export default function()
            declaration = node.get("declaration", {})
            if declaration.get("type") == "FunctionDeclaration":
                name = declaration.get("id", {}).get("name", "default")
                is_async = declaration.get("async", False)
                loc = declaration.get("loc", {})
                exports.append(ExportInfo(
                    export_name=name,
                    export_type="default",
                    is_async=is_async,
                    file_path=file_path,
                    line_start=loc.get("start", {}).get("line", 0),
                    line_end=loc.get("end", {}).get("line", 0)
                ))

        return exports

    def _extract_function(self, node: Dict, file_path: str, is_exported: bool) -> Optional:
        """Extract function declaration"""
        from scanner.extractors.symbol_table import FunctionDef

        name = node.get("id", {}).get("name", "")
        if not name:
            return None

        is_async = node.get("async", False)
        parameters = []

        for param in node.get("params", []):
            param_type = param.get("type")
            if param_type == "Identifier":
                parameters.append(param.get("name", ""))
            elif param_type == "AssignmentPattern":
                # Default parameter: (req, res = {})
                left = param.get("left", {})
                if left.get("type") == "Identifier":
                    parameters.append(left.get("name", ""))

        loc = node.get("loc", {})

        return FunctionDef(
            name=name,
            is_async=is_async,
            is_exported=is_exported,
            parameters=parameters,
            file_path=file_path,
            line_start=loc.get("start", {}).get("line", 0),
            line_end=loc.get("end", {}).get("line", 0)
        )

    def _parse_with_esprima(self, source_code: str, file_path: Path) -> Optional[Dict[str, Any]]:
        """Use TypeScript parser for JavaScript/TypeScript code"""
        # Create a temporary Node.js script to parse the code
        parser_script = """
        const parser = require('@typescript-eslint/typescript-estree');
        const fs = require('fs');

        const code = fs.readFileSync(process.argv[2], 'utf-8');
        const filePath = process.argv[2];

        try {
            // Parse as TypeScript/JavaScript
            const ast = parser.parse(code, {
                loc: true,
                range: true,
                ecmaFeatures: {
                    jsx: true
                }
            });
            console.log(JSON.stringify(ast));
        } catch (error) {
            console.error(JSON.stringify({error: error.message}));
            process.exit(1);
        }
        """

        try:
            # Write parser script temporarily (cross-platform)
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            script_path = temp_dir / "esprima_parser.js"
            script_path.write_text(parser_script)

            # Execute Node.js parser with NODE_PATH to find esprima
            # Point to the LogicVulnScanner's node_modules directory
            scanner_root = Path(__file__).parent.parent.parent
            node_modules_path = scanner_root / "node_modules"

            env = subprocess.os.environ.copy()
            env["NODE_PATH"] = str(node_modules_path)

            result = subprocess.run(
                ["node", str(script_path), str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                print(f"Error parsing {file_path}: {result.stderr}")
                return None

        except Exception as e:
            print(f"Failed to parse {file_path} with esprima: {e}")
            return None

    def _visit_node(self, js_node: Dict[str, Any], parent_node: ASTNode) -> None:
        """Visit esprima AST node and convert to our format"""
        node_type = js_node.get("type", "Unknown")

        # Extract location
        loc = js_node.get("loc", {})
        line_start = loc.get("start", {}).get("line", 0)
        line_end = loc.get("end", {}).get("line", line_start)
        col_start = loc.get("start", {}).get("column", 0)
        col_end = loc.get("end", {}).get("column", 0)

        ast_node = None

        # Handle export declarations by visiting their declaration
        if node_type in ["ExportNamedDeclaration", "ExportDefaultDeclaration"]:
            declaration = js_node.get("declaration")
            if declaration:
                self._visit_node(declaration, parent_node)
            # Also handle specifiers for named exports
            specifiers = js_node.get("specifiers", [])
            for spec in specifiers:
                if isinstance(spec, dict):
                    self._visit_node(spec, parent_node)
            return  # Don't process children again
        
        # Handle block statements and expression statements (pass through)
        if node_type in ["BlockStatement", "ExpressionStatement"]:
            self._visit_children(js_node, parent_node)
            return
        
        if node_type == "FunctionDeclaration":
            ast_node = self._handle_function_declaration(js_node, line_start, line_end, col_start, col_end)
        elif node_type == "FunctionExpression" or node_type == "ArrowFunctionExpression":
            ast_node = self._handle_function_expression(js_node, line_start, line_end, col_start, col_end)
        elif node_type == "ClassDeclaration":
            ast_node = self._handle_class(js_node, line_start, line_end, col_start, col_end)
        elif node_type == "MethodDefinition":
            ast_node = self._handle_method(js_node, line_start, line_end, col_start, col_end)
        elif node_type == "IfStatement":
            ast_node = self._handle_if(js_node, line_start, line_end, col_start, col_end)
        elif node_type in ["ForStatement", "WhileStatement", "DoWhileStatement", "ForInStatement", "ForOfStatement"]:
            ast_node = self._handle_loop(js_node, line_start, line_end, col_start, col_end)
        elif node_type == "TryStatement":
            ast_node = self._handle_try(js_node, line_start, line_end, col_start, col_end)
        elif node_type == "ReturnStatement":
            ast_node = self._handle_return(js_node, line_start, line_end, col_start, col_end)
        elif node_type == "CallExpression":
            ast_node = self._handle_call(js_node, line_start, line_end, col_start, col_end)
        elif node_type == "VariableDeclaration":
            ast_node = self._handle_variable(js_node, line_start, line_end, col_start, col_end)

        # Add node if created
        if ast_node:
            parent_node.add_child(ast_node)
            current_parent = ast_node
        else:
            current_parent = parent_node

        # Recursively visit children
        self._visit_children(js_node, current_parent)

    def _visit_children(self, js_node: Dict[str, Any], parent_node: ASTNode):
        """Recursively visit child nodes"""
        # Common child properties in esprima AST
        child_keys = ["body", "consequent", "alternate", "declarations", "expression", 
                      "argument", "arguments", "params", "init", "callee", "object", "property"]

        for key in child_keys:
            child = js_node.get(key)
            if isinstance(child, dict):
                self._visit_node(child, parent_node)
            elif isinstance(child, list):
                for item in child:
                    if isinstance(item, dict):
                        self._visit_node(item, parent_node)

    def _handle_function_declaration(
        self, js_node: Dict[str, Any], line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle function declaration"""
        func_id = js_node.get("id", {})
        name = func_id.get("name", "<anonymous>") if func_id else "<anonymous>"

        node = ASTNode(
            node_type="FunctionDeclaration",
            entity_type=EntityType.FUNCTION,
            name=name,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
            is_async=js_node.get("async", False),
        )

        # Extract parameters
        params = []
        for param in js_node.get("params", []):
            if isinstance(param, dict):
                param_name = param.get("name", "<param>")
                params.append(param_name)
        node.set_attribute("parameters", params)

        return node

    def _handle_function_expression(
        self, js_node: Dict[str, Any], line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle function expression or arrow function"""
        func_id = js_node.get("id", {})
        name = func_id.get("name", "<anonymous>") if func_id else "<anonymous>"

        node = ASTNode(
            node_type=js_node["type"],
            entity_type=EntityType.FUNCTION,
            name=name,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
            is_async=js_node.get("async", False),
        )

        # Extract parameters
        params = []
        for param in js_node.get("params", []):
            if isinstance(param, dict):
                param_name = param.get("name", "<param>")
                params.append(param_name)
        node.set_attribute("parameters", params)

        return node

    def _handle_class(
        self, js_node: Dict[str, Any], line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle class declaration"""
        class_id = js_node.get("id", {})
        name = class_id.get("name", "<anonymous>") if class_id else "<anonymous>"

        node = ASTNode(
            node_type="ClassDeclaration",
            entity_type=EntityType.CLASS,
            name=name,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )

        # Extract superclass
        superclass = js_node.get("superClass")
        if superclass and isinstance(superclass, dict):
            super_name = superclass.get("name", "")
            node.set_attribute("superclass", super_name)

        return node

    def _handle_method(
        self, js_node: Dict[str, Any], line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle method definition"""
        key = js_node.get("key", {})
        name = key.get("name", "<method>") if key else "<method>"

        node = ASTNode(
            node_type="MethodDefinition",
            entity_type=EntityType.METHOD,
            name=name,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )

        method_kind = js_node.get("kind", "method")
        node.set_attribute("kind", method_kind)

        return node

    def _handle_if(
        self, js_node: Dict[str, Any], line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle if statement"""
        node = ASTNode(
            node_type="IfStatement",
            entity_type=EntityType.IF_STATEMENT,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )
        return node

    def _handle_loop(
        self, js_node: Dict[str, Any], line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle loop statement"""
        node = ASTNode(
            node_type=js_node["type"],
            entity_type=EntityType.LOOP,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )
        return node

    def _handle_try(
        self, js_node: Dict[str, Any], line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle try-catch statement"""
        node = ASTNode(
            node_type="TryStatement",
            entity_type=EntityType.TRY_CATCH,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )
        return node

    def _handle_return(
        self, js_node: Dict[str, Any], line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle return statement"""
        node = ASTNode(
            node_type="ReturnStatement",
            entity_type=EntityType.RETURN,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )
        return node

    def _handle_call(
        self, js_node: Dict[str, Any], line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle function call"""
        callee = js_node.get("callee", {})
        func_name = self._extract_name(callee)

        node = ASTNode(
            node_type="CallExpression",
            entity_type=EntityType.EXTERNAL_CALL,
            name=func_name,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )

        # Tag database operations
        if any(keyword in func_name.lower() for keyword in ["query", "execute", "find", "filter"]):
            node.add_tag("database_operation")
            node.entity_type = EntityType.DATABASE_QUERY

        return node

    def _handle_variable(
        self, js_node: Dict[str, Any], line_start: int, line_end: int, col_start: int, col_end: int
    ) -> ASTNode:
        """Handle variable declaration"""
        node = ASTNode(
            node_type="VariableDeclaration",
            entity_type=EntityType.VARIABLE,
            line_start=line_start,
            line_end=line_end,
            col_start=col_start,
            col_end=col_end,
        )

        var_kind = js_node.get("kind", "var")
        node.set_attribute("kind", var_kind)

        return node

    def _extract_name(self, node: Dict[str, Any]) -> str:
        """Extract name from a node"""
        if not isinstance(node, dict):
            return "<unknown>"

        node_type = node.get("type", "")

        if node_type == "Identifier":
            return node.get("name", "<unknown>")
        elif node_type == "MemberExpression":
            obj = self._extract_name(node.get("object", {}))
            prop = self._extract_name(node.get("property", {}))
            return f"{obj}.{prop}"
        else:
            return "<complex>"

    def extract_entities(self, root_node: ASTNode) -> List[CodeEntity]:
        """Extract high-level entities from AST"""
        entities = []

        # Detect auth middleware at file level
        file_source = root_node.source_code or ""
        file_has_auth_mw = self._detect_auth_middleware(file_source)

        # Find all functions and methods
        functions = root_node.find_children_by_type(EntityType.FUNCTION)
        functions.extend(root_node.find_children_by_type(EntityType.METHOD))

        for func in functions:
            # Make anonymous functions unique by including line number
            func_name = func.name if func.name and func.name != "<anonymous>" else f"<anonymous>@{func.line_start}"
            
            # Extract source code from file for this function
            func_source = self._extract_function_source(file_source, func.line_start, func.line_end)
            
            entity = CodeEntity(
                entity_type=func.entity_type,
                name=func_name,
                file_path=root_node.get_attribute("file_path", ""),
                line_start=func.line_start,
                line_end=func.line_end,
                source_code=func_source,
            )

            # Find database queries
            db_queries = [child for child in func.find_children_by_type(EntityType.DATABASE_QUERY)]
            if db_queries:
                entity.accesses_database = True

            # Extract function calls
            calls = [child for child in func.find_children_by_type(EntityType.EXTERNAL_CALL)]
            entity.calls = [call.name for call in calls if call.name]
            
            # Detect API endpoints (Express.js route handlers)
            # Check if function has Request/Response parameters (common in Express)
            # AND has database access or is a named exported function
            params = func.get_attribute("parameters", [])
            has_req_res_params = any(p in ["req", "request", "res", "response", "next"] for p in params)
            
            # Only mark as endpoint if:
            # 1. Has req/res/next params AND accesses database, OR
            # 2. Is a named exported function (not anonymous)
            if has_req_res_params and (entity.accesses_database or func.name != "<anonymous>"):
                entity.handles_user_input = True
                entity.entity_type = EntityType.API_ENDPOINT

            # Compute object_id_signal using regex on source code
            entity.object_id_signal = self._compute_object_id_signal_regex(func_source or "")
            
            # Set middleware detection (file-level for now)
            entity.has_auth_middleware = file_has_auth_mw

            entities.append(entity)

        return entities
    
    def _extract_function_source(self, file_source: str, line_start: int, line_end: int) -> str:
        """Extract source code for a function from file source"""
        if not file_source:
            return ""
        
        lines = file_source.split('\n')
        if line_start <= 0 or line_end > len(lines):
            return ""
        
        # Extract lines (1-indexed to 0-indexed)
        func_lines = lines[line_start-1:line_end]
        return '\n'.join(func_lines)
    
    def _compute_object_id_signal_regex(self, source_code: str) -> int:
        """
        Compute object_id_signal (0-2) using comprehensive regex patterns
        
        Strong signals (+2):
        - Direct access: req.params.id, req.body.UserId (dot notation)
        - Bracket notation: req.params['id'], req.body["UserId"]
        
        Medium signals (+1):
        - Destructuring: const { id } = req.params
        - Route params: /:id, /:userId
        - ORM by PK: findByPk(, findOne({where: {id
        
        Returns: 0-2 score (capped)
        """
        import re
        
        signal = 0
        
        # Strong signal: Direct access (dot notation)
        # Matches: req.params.id, req.body.UserId, request.query.accountId
        direct_dot_pattern = r'\b(req|request)\s*\.\s*(params|query|body)\s*\.\s*([A-Za-z_][A-Za-z0-9_]*)'
        matches = re.findall(direct_dot_pattern, source_code)
        
        for match in matches:
            key_name = match[2].lower()
            # Check if key name is id-ish
            if re.search(r'(^id$|.*id$|.*_id$|uuid|guid|token)', key_name):
                signal = 2
                break
        
        # Strong signal: Bracket notation
        if signal < 2:
            bracket_pattern = r'\b(req|request)\s*\.\s*(params|query|body)\s*\[\s*[\'"]([^\'"]+)[\'"]\s*\]'
            matches = re.findall(bracket_pattern, source_code)
            
            for match in matches:
                key_name = match[2].lower()
                if re.search(r'(^id$|.*id$|.*_id$|uuid|guid|token)', key_name):
                    signal = 2
                    break
        
        # Medium signal: Destructuring
        if signal < 2:
            destructure_pattern = r'const\s*\{\s*([^}]+)\s*\}\s*=\s*(req|request)\s*\.\s*(params|query|body)'
            matches = re.findall(destructure_pattern, source_code)
            
            for match in matches:
                keys = match[0]
                if re.search(r'\bid\b|.*id\b|.*_id\b', keys, re.IGNORECASE):
                    signal = max(signal, 1)
                    break
        
        # Medium signal: Route params
        if signal < 2:
            route_pattern = r'[\'"]\/[^\'"]*:([A-Za-z_][A-Za-z0-9_]*)'
            matches = re.findall(route_pattern, source_code)
            
            for match in matches:
                if re.search(r'(^id$|.*id$|.*_id$)', match, re.IGNORECASE):
                    signal = max(signal, 1)
                    break
        
        # Medium signal: ORM by PK
        if signal < 2:
            if re.search(r'findByPk\s*\(', source_code):
                signal = max(signal, 1)
            elif re.search(r'findOne\s*\(\s*\{\s*where\s*:\s*\{\s*([A-Za-z_][A-Za-z0-9_]*)', source_code):
                # Check if the where clause has id-ish key
                where_matches = re.findall(r'findOne\s*\(\s*\{\s*where\s*:\s*\{\s*([A-Za-z_][A-Za-z0-9_]*)', source_code)
                for key in where_matches:
                    if re.search(r'(^id$|.*id$|.*_id$)', key, re.IGNORECASE):
                        signal = max(signal, 1)
                        break
        
        return signal

    def _detect_auth_middleware(self, source_code: str) -> bool:
        """
        Detect if file uses auth middleware in route registration
        
        Looks for common Express.js auth middleware patterns:
        - isAuthenticated, authenticate, verifyToken, jwt
        - requireAuth, isAuthorized, authorize, ensureLoggedIn
        - Juice Shop specific: security.*, authenticatedUsers.*
        
        Returns: True if auth middleware detected
        """
        import re
        
        # Common auth middleware names
        auth_patterns = [
            r'isAuthenticated',
            r'authenticate',
            r'verifyToken',
            r'requireAuth',
            r'isAuthorized',
            r'authorize',
            r'ensureLoggedIn',
            r'isAdmin',
            r'security\.',
            r'authenticatedUsers\.',
            r'\.use\([^)]*auth',
            r'router\.use\([^)]*security',
        ]
        
        for pattern in auth_patterns:
            if re.search(pattern, source_code, re.IGNORECASE):
                return True
        
        return False

