"""
Symbol Table for cross-file handler resolution

Tracks imports, exports, and function definitions to resolve:
- twoFactorAuth.verify → ./routes/2fa.ts:verify:22
- payment.getPaymentMethods → ./routes/payment.ts:getPaymentMethods:19
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class ImportInfo:
    """Import statement information"""
    local_name: str
    source_module: str
    import_type: str  # "namespace", "default", "named"
    imported_names: List[str] = field(default_factory=list)
    file_path: str = ""
    line_number: int = 0


@dataclass
class ExportInfo:
    """Export statement information"""
    export_name: str
    export_type: str  # "function", "const", "default"
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    is_async: bool = False
    source_module: Optional[str] = None  # For re-exports


@dataclass
class FunctionDef:
    """Function definition"""
    name: str
    is_async: bool
    is_exported: bool
    parameters: List[str] = field(default_factory=list)
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0


class SymbolTable:
    """
    Cross-file symbol resolution for handler binding
    
    Tracks:
    - Imports: What each file imports and from where
    - Exports: What each file exports
    - Functions: Function definitions with locations
    """
    
    def __init__(self):
        # file_path → List[ImportInfo]
        self.imports: Dict[str, List[ImportInfo]] = {}
        
        # file_path → List[ExportInfo]
        self.exports: Dict[str, List[ExportInfo]] = {}
        
        # file_path → List[FunctionDef]
        self.functions: Dict[str, List[FunctionDef]] = {}
        
        # Cache for resolved paths
        self._resolution_cache: Dict[str, Optional[str]] = {}
    
    def add_imports(self, file_path: str, imports: List[ImportInfo]):
        """Add imports for a file"""
        file_path = str(Path(file_path).resolve())
        self.imports[file_path] = imports
    
    def add_exports(self, file_path: str, exports: List[ExportInfo]):
        """Add exports for a file"""
        file_path = str(Path(file_path).resolve())
        self.exports[file_path] = exports
    
    def add_functions(self, file_path: str, functions: List[FunctionDef]):
        """Add function definitions for a file"""
        file_path = str(Path(file_path).resolve())
        self.functions[file_path] = functions
    
    def resolve_member_expression(
        self, 
        module_name: str, 
        function_name: str, 
        context_file: str
    ) -> Optional[str]:
        """
        Resolve module.function to actual file path and location
        
        Example: twoFactorAuth.verify in server.ts → ./routes/2fa.ts:verify:22
        
        Returns: "file_path:function_name:line_start" or None
        """
        cache_key = f"{context_file}:{module_name}.{function_name}"
        if cache_key in self._resolution_cache:
            return self._resolution_cache[cache_key]
        
        context_file = str(Path(context_file).resolve())
        
        # Step 1: Find import of module_name in context_file
        file_imports = self.imports.get(context_file, [])
        
        source_module = None
        for imp in file_imports:
            if imp.local_name == module_name:
                source_module = imp.source_module
                break
        
        if not source_module:
            self._resolution_cache[cache_key] = None
            return None
        
        # Step 2: Resolve source module to file path
        target_file = self._resolve_module_path(source_module, context_file)
        if not target_file:
            self._resolution_cache[cache_key] = None
            return None
        
        # Step 3: Find export of function_name in target_file
        file_exports = self.exports.get(target_file, [])

        for exp in file_exports:
            if exp.export_name == function_name:
                # Try to find the actual function definition line
                line_number = exp.line_start

                # Check if we have function definitions for this file
                file_functions = self.functions.get(target_file, [])
                for func in file_functions:
                    if func.name == function_name:
                        line_number = func.line_start
                        break

                result = f"{target_file}:{function_name}:{line_number}"
                self._resolution_cache[cache_key] = result
                return result
        
        self._resolution_cache[cache_key] = None
        return None
    
    def resolve_identifier(self, identifier: str, context_file: str) -> Optional[str]:
        """
        Resolve identifier to file path and location
        
        Example: login in server.ts → ./routes/login.ts:login:18
        """
        cache_key = f"{context_file}:{identifier}"
        if cache_key in self._resolution_cache:
            return self._resolution_cache[cache_key]
        
        context_file = str(Path(context_file).resolve())
        
        # Check if it's imported
        file_imports = self.imports.get(context_file, [])
        
        for imp in file_imports:
            if imp.local_name == identifier:
                # Resolve to target file
                target_file = self._resolve_module_path(imp.source_module, context_file)
                if target_file:
                    # Find export
                    file_exports = self.exports.get(target_file, [])
                    for exp in file_exports:
                        if exp.export_name == identifier or exp.export_type == "default":
                            # Try to find the actual function definition line
                            line_number = exp.line_start

                            # Check if we have function definitions for this file
                            file_functions = self.functions.get(target_file, [])
                            for func in file_functions:
                                if func.name == exp.export_name:
                                    line_number = func.line_start
                                    break

                            result = f"{target_file}:{exp.export_name}:{line_number}"
                            self._resolution_cache[cache_key] = result
                            return result
        
        # Check if it's defined locally
        file_functions = self.functions.get(context_file, [])
        for func in file_functions:
            if func.name == identifier:
                result = f"{context_file}:{func.name}:{func.line_start}"
                self._resolution_cache[cache_key] = result
                return result
        
        self._resolution_cache[cache_key] = None
        return None
    
    def _resolve_module_path(self, source_module: str, context_file: str) -> Optional[str]:
        """
        Resolve module path to absolute file path
        
        Example: './routes/2fa' from server.ts → /path/to/routes/2fa.ts
        """
        if not source_module.startswith('.'):
            # External module (node_modules) - skip for now
            return None
        
        context_dir = Path(context_file).parent
        
        # Try common extensions
        for ext in ['.ts', '.js', '.tsx', '.jsx', '']:
            candidate = context_dir / (source_module + ext)
            if candidate.exists():
                return str(candidate.resolve())
            
            # Try index files
            index_candidate = context_dir / source_module / f'index{ext}'
            if index_candidate.exists():
                return str(index_candidate.resolve())
        
        return None
    
    def get_statistics(self) -> Dict[str, int]:
        """Get symbol table statistics"""
        total_imports = sum(len(imps) for imps in self.imports.values())
        total_exports = sum(len(exps) for exps in self.exports.values())
        total_functions = sum(len(funcs) for funcs in self.functions.values())
        
        return {
            "files": len(self.imports),
            "imports": total_imports,
            "exports": total_exports,
            "functions": total_functions,
            "cache_hits": len(self._resolution_cache)
        }
