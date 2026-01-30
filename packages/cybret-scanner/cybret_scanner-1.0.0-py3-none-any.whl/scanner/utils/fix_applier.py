"""
Fix Applier - Automatically applies LLM-generated fixes to source files

This module provides safe, automated application of security fixes:
- Creates backups before modifying files
- Validates file locations
- Handles errors gracefully
- Supports dry-run mode
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class FixApplier:
    """
    Safely applies LLM-generated fixes to source files
    
    Features:
    - Automatic backups before modification
    - Dry-run mode for testing
    - Error handling and rollback
    - Detailed logging
    """
    
    def __init__(self, codebase_path: str, backup_dir: str = ".scanner-backups", dry_run: bool = False):
        """
        Initialize fix applier
        
        Args:
            codebase_path: Path to the codebase root
            backup_dir: Directory for backup files
            dry_run: If True, don't actually modify files
        """
        self.codebase_path = Path(codebase_path).resolve()
        self.backup_dir = Path(backup_dir).resolve()
        self.dry_run = dry_run
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create backup directory if not in dry-run mode
        if not dry_run and not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def apply_fixes(self, approved_fixes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply all approved fixes
        
        Args:
            approved_fixes: List of approved fix analyses
            
        Returns:
            List of results for each fix application
        """
        results = []
        
        for fix_analysis in approved_fixes:
            result = self._apply_single_fix(fix_analysis)
            results.append(result)
        
        return results
    
    def _apply_single_fix(self, fix_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a single fix to a file
        
        Args:
            fix_analysis: Fix analysis containing location and fixed code
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            # Extract file path from location (format: "path/to/file.js:line")
            location = fix_analysis.get('location', '')
            if ':' not in location:
                return {
                    'success': False,
                    'file': location,
                    'error': 'Invalid location format'
                }
            
            file_path_str, line_str = location.rsplit(':', 1)
            file_path = Path(file_path_str)
            
            # Make path absolute if relative
            if not file_path.is_absolute():
                file_path = self.codebase_path / file_path
            
            # Validate file exists
            if not file_path.exists():
                return {
                    'success': False,
                    'file': str(file_path),
                    'error': 'File not found'
                }
            
            # Validate file is within codebase
            try:
                file_path.resolve().relative_to(self.codebase_path)
            except ValueError:
                return {
                    'success': False,
                    'file': str(file_path),
                    'error': 'File outside codebase'
                }
            
            # Get fixed code
            fix_data = fix_analysis.get('fix', {})
            fixed_code = fix_data.get('fixed_code', '')
            
            if not fixed_code:
                return {
                    'success': False,
                    'file': str(file_path),
                    'error': 'No fixed code provided'
                }
            
            # Dry run - just report what would happen
            if self.dry_run:
                return {
                    'success': True,
                    'file': str(file_path),
                    'action': 'would_apply',
                    'backup': 'would_create',
                    'dry_run': True
                }
            
            # Create backup
            backup_path = self._create_backup(file_path)
            
            # Extract the function/handler to replace
            # This is a simplified version - in production, you'd want more sophisticated parsing
            original_content = file_path.read_text(encoding='utf-8')
            
            # Try to find and replace the vulnerable code
            # Strategy: Look for the function containing the vulnerability
            function_name = fix_analysis.get('function_name', '')
            
            if function_name:
                # Try to replace the specific function
                new_content = self._replace_function(original_content, fixed_code, function_name)
            else:
                # Fallback: Replace entire file (risky, but works for single-function files)
                new_content = fixed_code
            
            # Write the fixed code
            file_path.write_text(new_content, encoding='utf-8')
            
            return {
                'success': True,
                'file': str(file_path),
                'backup': str(backup_path),
                'action': 'applied',
                'lines_changed': len(new_content.splitlines()) - len(original_content.splitlines())
            }
            
        except Exception as e:
            return {
                'success': False,
                'file': fix_analysis.get('location', 'unknown'),
                'error': str(e)
            }
    
    def _create_backup(self, file_path: Path) -> Path:
        """
        Create a backup of the file before modification
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Path to backup file
        """
        # Create backup path: .scanner-backups/timestamp/relative/path/to/file.js.bak
        relative_path = file_path.relative_to(self.codebase_path)
        backup_path = self.backup_dir / self.timestamp / relative_path.parent / f"{relative_path.name}.bak"
        
        # Create parent directories
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file to backup
        shutil.copy2(file_path, backup_path)
        
        return backup_path
    
    def _replace_function(self, original_content: str, fixed_code: str, function_name: str) -> str:
        """
        Replace a specific function in the original content
        
        This is a simplified implementation. In production, you'd want to use
        proper AST parsing and manipulation.
        
        Args:
            original_content: Original file content
            fixed_code: Fixed code (may be just the function or full file)
            function_name: Name of function to replace
            
        Returns:
            Modified content
        """
        # For now, if the fixed_code looks like a complete file (has imports, multiple functions),
        # use it as-is. Otherwise, try to replace just the function.
        
        # Simple heuristic: if fixed_code has "import" or "require" at the start, it's a full file
        if fixed_code.strip().startswith(('import ', 'const ', 'var ', 'let ', 'require(')):
            # Check if it looks like a full file
            if fixed_code.count('\n') > 10 or 'import' in fixed_code[:100]:
                return fixed_code
        
        # Otherwise, try to find and replace the function
        # This is a very basic implementation - production would need proper parsing
        lines = original_content.split('\n')
        fixed_lines = fixed_code.split('\n')
        
        # Find the function definition
        function_start = None
        for i, line in enumerate(lines):
            if function_name in line and ('function' in line or '=>' in line or 'async' in line):
                function_start = i
                break
        
        if function_start is None:
            # Can't find function, return fixed code as-is (risky but better than nothing)
            return fixed_code
        
        # Find the end of the function (simplified - looks for closing brace)
        brace_count = 0
        function_end = function_start
        started = False
        
        for i in range(function_start, len(lines)):
            line = lines[i]
            if '{' in line:
                brace_count += line.count('{')
                started = True
            if '}' in line:
                brace_count -= line.count('}')
            
            if started and brace_count == 0:
                function_end = i
                break
        
        # Replace the function
        new_lines = lines[:function_start] + fixed_lines + lines[function_end + 1:]
        
        return '\n'.join(new_lines)
    
    def rollback(self, backup_path: Path, original_path: Path) -> bool:
        """
        Rollback a file to its backup
        
        Args:
            backup_path: Path to backup file
            original_path: Path to original file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if backup_path.exists():
                shutil.copy2(backup_path, original_path)
                return True
            return False
        except Exception:
            return False
    
    def get_backup_info(self) -> Dict[str, Any]:
        """
        Get information about backups
        
        Returns:
            Dictionary with backup information
        """
        if not self.backup_dir.exists():
            return {
                'exists': False,
                'path': str(self.backup_dir),
                'backups': []
            }
        
        backups = []
        for backup_file in self.backup_dir.rglob('*.bak'):
            backups.append({
                'file': str(backup_file),
                'size': backup_file.stat().st_size,
                'modified': datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
            })
        
        return {
            'exists': True,
            'path': str(self.backup_dir),
            'count': len(backups),
            'backups': backups
        }


def restore_from_backup(backup_dir: str, timestamp: str = None) -> Dict[str, Any]:
    """
    Restore all files from a specific backup
    
    Args:
        backup_dir: Backup directory path
        timestamp: Specific timestamp to restore (if None, uses latest)
        
    Returns:
        Dictionary with restoration results
    """
    backup_path = Path(backup_dir)
    
    if not backup_path.exists():
        return {
            'success': False,
            'error': 'Backup directory not found'
        }
    
    # Find timestamp directory
    if timestamp:
        timestamp_dir = backup_path / timestamp
    else:
        # Find latest timestamp
        timestamp_dirs = sorted([d for d in backup_path.iterdir() if d.is_dir()])
        if not timestamp_dirs:
            return {
                'success': False,
                'error': 'No backups found'
            }
        timestamp_dir = timestamp_dirs[-1]
    
    if not timestamp_dir.exists():
        return {
            'success': False,
            'error': f'Timestamp {timestamp} not found'
        }
    
    # Restore all files
    restored = []
    failed = []
    
    for backup_file in timestamp_dir.rglob('*.bak'):
        try:
            # Get original path
            relative_path = backup_file.relative_to(timestamp_dir)
            original_name = relative_path.stem  # Remove .bak extension
            original_path = backup_file.parent / original_name
            
            # Restore file
            shutil.copy2(backup_file, original_path)
            restored.append(str(original_path))
        except Exception as e:
            failed.append({
                'file': str(backup_file),
                'error': str(e)
            })
    
    return {
        'success': len(failed) == 0,
        'restored': len(restored),
        'failed': len(failed),
        'files': restored,
        'errors': failed
    }
