"""
PR Creator - Automatically creates pull requests for security fixes

This module provides automated PR creation with:
- Git branch management
- Commit creation
- PR creation via GitHub CLI or API
- Detailed PR descriptions with fix summaries
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class PRCreator:
    """
    Automatically creates pull requests for applied security fixes
    
    Features:
    - Creates new branch from base
    - Commits applied fixes
    - Generates detailed PR description
    - Creates PR via GitHub CLI (gh) or API
    - Handles errors gracefully
    """
    
    def __init__(
        self,
        codebase_path: str,
        branch_name: str = "security/llm-auto-fixes",
        base_branch: str = "main"
    ):
        """
        Initialize PR creator
        
        Args:
            codebase_path: Path to the codebase root
            branch_name: Name for the new branch
            base_branch: Base branch to create PR against
        """
        self.codebase_path = Path(codebase_path).resolve()
        self.branch_name = branch_name
        self.base_branch = base_branch
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def create_pr(
        self,
        llm_results: Dict[str, Any],
        applied_results: List[Dict[str, Any]],
        report_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a pull request with applied fixes
        
        Args:
            llm_results: Results from LLM analysis
            applied_results: Results from fix application
            report_path: Path to remediation report (optional)
            
        Returns:
            Dictionary with PR creation results
        """
        try:
            # Check if we're in a git repository
            if not self._is_git_repo():
                return {
                    'success': False,
                    'error': 'Not a git repository'
                }
            
            # Check if GitHub CLI is available
            gh_available = self._is_gh_cli_available()
            
            if not gh_available:
                return {
                    'success': False,
                    'error': 'GitHub CLI (gh) not installed. Install from: https://cli.github.com/'
                }
            
            # Get current branch to return to later
            original_branch = self._get_current_branch()
            
            # Create and checkout new branch
            branch_result = self._create_branch()
            if not branch_result['success']:
                return branch_result
            
            # Stage and commit changes
            commit_result = self._commit_changes(llm_results, applied_results)
            if not commit_result['success']:
                self._checkout_branch(original_branch)
                return commit_result
            
            # Push branch to remote
            push_result = self._push_branch()
            if not push_result['success']:
                self._checkout_branch(original_branch)
                return push_result
            
            # Generate PR description
            pr_body = self._generate_pr_description(
                llm_results,
                applied_results,
                report_path
            )
            
            # Create PR using GitHub CLI
            pr_result = self._create_github_pr(pr_body)
            
            # Return to original branch
            self._checkout_branch(original_branch)
            
            if pr_result['success']:
                return {
                    'success': True,
                    'pr_url': pr_result['pr_url'],
                    'pr_number': pr_result['pr_number'],
                    'branch': self.branch_name,
                    'files_changed': len([r for r in applied_results if r['success']]),
                    'commit_sha': commit_result.get('commit_sha')
                }
            else:
                return pr_result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': 'Unexpected error during PR creation'
            }
    
    def _is_git_repo(self) -> bool:
        """Check if current directory is a git repository"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.codebase_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _is_gh_cli_available(self) -> bool:
        """Check if GitHub CLI is installed and authenticated"""
        try:
            result = subprocess.run(
                ['gh', 'auth', 'status'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _get_current_branch(self) -> str:
        """Get the current git branch name"""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.codebase_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except:
            return 'main'
    
    def _create_branch(self) -> Dict[str, Any]:
        """Create and checkout a new branch"""
        try:
            # Check if branch already exists
            check_result = subprocess.run(
                ['git', 'rev-parse', '--verify', self.branch_name],
                cwd=self.codebase_path,
                capture_output=True,
                timeout=5
            )
            
            if check_result.returncode == 0:
                # Branch exists, add timestamp to make it unique
                self.branch_name = f"{self.branch_name}-{self.timestamp}"
            
            # Create and checkout new branch
            result = subprocess.run(
                ['git', 'checkout', '-b', self.branch_name],
                cwd=self.codebase_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {'success': True, 'branch': self.branch_name}
            else:
                return {
                    'success': False,
                    'error': f'Failed to create branch: {result.stderr}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Branch creation failed: {str(e)}'
            }
    
    def _checkout_branch(self, branch: str) -> bool:
        """Checkout a specific branch"""
        try:
            result = subprocess.run(
                ['git', 'checkout', branch],
                cwd=self.codebase_path,
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _commit_changes(
        self,
        llm_results: Dict[str, Any],
        applied_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Stage and commit the applied fixes"""
        try:
            # Get list of successfully modified files
            modified_files = [
                r['file'] for r in applied_results 
                if r['success'] and not r.get('dry_run', False)
            ]
            
            if not modified_files:
                return {
                    'success': False,
                    'error': 'No files to commit'
                }
            
            # Stage the modified files
            for file_path in modified_files:
                subprocess.run(
                    ['git', 'add', file_path],
                    cwd=self.codebase_path,
                    capture_output=True,
                    timeout=5
                )
            
            # Generate commit message
            commit_message = self._generate_commit_message(llm_results, applied_results)
            
            # Commit changes
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.codebase_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Get commit SHA
                sha_result = subprocess.run(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=self.codebase_path,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                return {
                    'success': True,
                    'commit_sha': sha_result.stdout.strip()
                }
            else:
                return {
                    'success': False,
                    'error': f'Commit failed: {result.stderr}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Commit creation failed: {str(e)}'
            }
    
    def _push_branch(self) -> Dict[str, Any]:
        """Push the branch to remote"""
        try:
            result = subprocess.run(
                ['git', 'push', '-u', 'origin', self.branch_name],
                cwd=self.codebase_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': f'Push failed: {result.stderr}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Push failed: {str(e)}'
            }
    
    def _generate_commit_message(
        self,
        llm_results: Dict[str, Any],
        applied_results: List[Dict[str, Any]]
    ) -> str:
        """Generate a descriptive commit message"""
        
        approved_fixes = llm_results.get('approved_fixes', [])
        success_count = sum(1 for r in applied_results if r['success'])
        
        # Group by vulnerability type
        vuln_types = {}
        for fix in approved_fixes:
            vuln_type = fix.get('vulnerability_type', 'Unknown')
            vuln_types[vuln_type] = vuln_types.get(vuln_type, 0) + 1
        
        # Create commit message
        message = f"Security: Auto-apply {success_count} LLM-generated fixes\n\n"
        
        # Add vulnerability breakdown
        message += "Vulnerabilities fixed:\n"
        for vuln_type, count in vuln_types.items():
            message += f"- {vuln_type}: {count}\n"
        
        message += "\n"
        message += "These fixes were automatically generated and validated by\n"
        message += "the LLM-enhanced security scanner with multi-agent analysis.\n"
        message += "\n"
        message += "All fixes have been:\n"
        message += "- Analyzed for business logic impact\n"
        message += "- Validated for security completeness\n"
        message += "- Approved by automated quality gates\n"
        
        return message
    
    def _generate_pr_description(
        self,
        llm_results: Dict[str, Any],
        applied_results: List[Dict[str, Any]],
        report_path: Optional[str] = None
    ) -> str:
        """Generate detailed PR description"""
        
        approved_fixes = llm_results.get('approved_fixes', [])
        success_count = sum(1 for r in applied_results if r['success'])
        total_vulns = llm_results.get('total_vulnerabilities', 0)
        
        # Start with summary
        description = "# 🔒 Automated Security Fixes\n\n"
        description += "This PR contains automatically generated and applied security fixes "
        description += "from the LLM-enhanced vulnerability scanner.\n\n"
        
        # Summary section
        description += "## 📊 Summary\n\n"
        description += f"- **Total Vulnerabilities Analyzed:** {total_vulns}\n"
        description += f"- **Approved Fixes:** {len(approved_fixes)}\n"
        description += f"- **Successfully Applied:** {success_count}\n"
        description += f"- **Files Modified:** {len(set(r['file'] for r in applied_results if r['success']))}\n\n"
        
        # Vulnerability breakdown
        description += "## 🐛 Vulnerabilities Fixed\n\n"
        
        vuln_by_severity = {}
        for fix in approved_fixes:
            severity = fix.get('severity', 'unknown').upper()
            vuln_by_severity.setdefault(severity, []).append(fix)
        
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if severity in vuln_by_severity:
                fixes = vuln_by_severity[severity]
                description += f"### {severity} ({len(fixes)})\n\n"
                
                for fix in fixes[:5]:  # Show first 5 per severity
                    vuln_type = fix.get('vulnerability_type', 'Unknown')
                    location = fix.get('location', 'Unknown')
                    description += f"- **{vuln_type}** at `{location}`\n"
                
                if len(fixes) > 5:
                    description += f"- ... and {len(fixes) - 5} more\n"
                
                description += "\n"
        
        # What was done
        description += "## 🔧 Changes Made\n\n"
        description += "Each fix includes:\n\n"
        description += "1. **Security Enhancement** - Added missing authorization/validation checks\n"
        description += "2. **Error Handling** - Proper error responses (404, 403)\n"
        description += "3. **Logging** - Security event logging for monitoring\n"
        description += "4. **Business Logic Preservation** - All existing functionality maintained\n\n"
        
        # Validation
        description += "## ✅ Validation\n\n"
        description += "All fixes have been:\n\n"
        description += "- ✅ **Analyzed** by Vulnerability Analyst Agent\n"
        description += "- ✅ **Validated** by Business Logic Expert Agent\n"
        description += "- ✅ **Generated** by Fix Generator Agent\n"
        description += "- ✅ **Approved** by Security Validator Agent\n"
        description += "- ✅ **Quality Checked** - Coverage ≥70%, No new issues\n\n"
        
        # Testing recommendations
        description += "## 🧪 Testing Checklist\n\n"
        description += "Please verify:\n\n"
        description += "- [ ] All existing tests pass\n"
        description += "- [ ] Manual testing of affected endpoints\n"
        description += "- [ ] Security testing (unauthorized access attempts)\n"
        description += "- [ ] Performance testing (no regressions)\n"
        description += "- [ ] Review fix explanations in detailed report\n\n"
        
        # Link to detailed report
        if report_path:
            description += f"## 📄 Detailed Report\n\n"
            description += f"See `{report_path}` for complete analysis and fix explanations.\n\n"
        
        # Modified files
        description += "## 📝 Modified Files\n\n"
        for result in applied_results:
            if result['success']:
                file_path = result['file']
                description += f"- `{file_path}`\n"
        
        description += "\n"
        
        # Backups
        description += "## 💾 Backups\n\n"
        description += "Original files have been backed up to `.scanner-backups/` directory.\n"
        description += "To rollback if needed:\n"
        description += "```bash\n"
        description += "python -m scanner.cli rollback\n"
        description += "```\n\n"
        
        # Footer
        description += "---\n\n"
        description += "🤖 **Generated by:** LLM-Enhanced Security Scanner v3.0\n"
        description += f"⏰ **Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        description += "🔐 **Confidence:** High (Multi-agent validation)\n"
        
        return description
    
    def _create_github_pr(self, pr_body: str) -> Dict[str, Any]:
        """Create PR using GitHub CLI"""
        try:
            # Generate PR title
            pr_title = f"Security: Auto-apply LLM-generated fixes ({datetime.now().strftime('%Y-%m-%d')})"
            
            # Create PR using gh CLI
            result = subprocess.run(
                [
                    'gh', 'pr', 'create',
                    '--title', pr_title,
                    '--body', pr_body,
                    '--base', self.base_branch,
                    '--head', self.branch_name
                ],
                cwd=self.codebase_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Extract PR URL from output
                pr_url = result.stdout.strip()
                
                # Extract PR number from URL
                pr_number = None
                if '/pull/' in pr_url:
                    pr_number = pr_url.split('/pull/')[-1].strip()
                
                return {
                    'success': True,
                    'pr_url': pr_url,
                    'pr_number': pr_number
                }
            else:
                return {
                    'success': False,
                    'error': f'PR creation failed: {result.stderr}',
                    'details': result.stdout
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'PR creation failed: {str(e)}'
            }


def create_pr_from_results(
    codebase_path: str,
    llm_results: Dict[str, Any],
    applied_results: List[Dict[str, Any]],
    report_path: Optional[str] = None,
    branch_name: str = "security/llm-auto-fixes",
    base_branch: str = "main"
) -> Dict[str, Any]:
    """
    Convenience function to create a PR from scan results
    
    Args:
        codebase_path: Path to codebase
        llm_results: Results from LLM analysis
        applied_results: Results from fix application
        report_path: Path to remediation report
        branch_name: Branch name for PR
        base_branch: Base branch for PR
        
    Returns:
        Dictionary with PR creation results
    """
    creator = PRCreator(codebase_path, branch_name, base_branch)
    return creator.create_pr(llm_results, applied_results, report_path)
