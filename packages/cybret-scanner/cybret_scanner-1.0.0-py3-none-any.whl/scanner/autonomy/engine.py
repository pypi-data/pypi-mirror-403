"""
Autonomy Engine - Graduated Remediation System

Implements 4 levels of autonomy for vulnerability remediation:
Level 1: Suggest - Show fix to developer
Level 2: Draft - Generate PR for review
Level 3: Execute with Approval - Auto-fix after human approval
Level 4: Autonomous - Auto-fix with monitoring
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

from scanner.autonomy.trust_scorer import TrustScorer, TrustScore


logger = logging.getLogger(__name__)


class AutonomyLevel(Enum):
    """Graduated autonomy levels"""
    SUGGEST = 1  # Show suggested fix
    DRAFT = 2  # Generate PR for review
    EXECUTE_WITH_APPROVAL = 3  # Auto-fix after approval
    AUTONOMOUS = 4  # Auto-fix with monitoring


class RemediationStatus(Enum):
    """Status of remediation action"""
    PENDING = "pending"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class RemediationAction:
    """
    Represents a remediation action at a specific autonomy level

    Tracks the entire lifecycle of a fix from suggestion to completion
    """
    action_id: str
    vulnerability_id: str
    vulnerability_type: str
    severity: str

    # Autonomy
    autonomy_level: AutonomyLevel
    trust_score: TrustScore

    # Fix details
    file_path: str
    line_start: int
    line_end: Optional[int] = None
    suggested_fix: str = ""
    fix_description: str = ""
    fix_reasoning: str = ""

    # Status tracking
    status: RemediationStatus = RemediationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Git integration
    branch_name: Optional[str] = None
    pr_url: Optional[str] = None
    commit_sha: Optional[str] = None

    # Approval workflow (for Level 3)
    requires_approval: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Monitoring (for Level 4)
    monitoring_enabled: bool = False
    rollback_threshold: float = 0.2  # Rollback if error rate > 20%

    # Results
    success: bool = False
    error_message: Optional[str] = None
    rollback_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "action_id": self.action_id,
            "vulnerability_id": self.vulnerability_id,
            "vulnerability_type": self.vulnerability_type,
            "severity": self.severity,
            "autonomy_level": self.autonomy_level.value,
            "trust_score": {
                "overall": self.trust_score.overall_score,
                "recommended_level": self.trust_score.recommended_level,
                "reasoning": self.trust_score.reasoning,
            },
            "fix_details": {
                "file_path": self.file_path,
                "line_start": self.line_start,
                "line_end": self.line_end,
                "suggested_fix": self.suggested_fix,
                "description": self.fix_description,
                "reasoning": self.fix_reasoning,
            },
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "git": {
                "branch": self.branch_name,
                "pr_url": self.pr_url,
                "commit_sha": self.commit_sha,
            },
            "approval": {
                "requires_approval": self.requires_approval,
                "approved_by": self.approved_by,
                "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            },
            "monitoring": {
                "enabled": self.monitoring_enabled,
                "rollback_threshold": self.rollback_threshold,
            },
            "result": {
                "success": self.success,
                "error_message": self.error_message,
                "rollback_reason": self.rollback_reason,
            }
        }


class AutonomyEngine:
    """
    Graduated Autonomy Engine for Vulnerability Remediation

    Implements 4 levels of autonomy based on trust scores:

    Level 1: SUGGEST
    - Show suggested fix in UI
    - Developer reviews and applies manually
    - Lowest risk, highest human involvement

    Level 2: DRAFT
    - Generate Git branch with fix
    - Create PR for review
    - Developer approves via PR workflow
    - Standard pull request process

    Level 3: EXECUTE WITH APPROVAL
    - Generate fix
    - Request explicit approval
    - Auto-apply after approval
    - Human approval required, but auto-execution

    Level 4: AUTONOMOUS
    - Generate and apply fix automatically
    - Monitor for issues
    - Auto-rollback if problems detected
    - Highest automation, requires highest trust
    """

    def __init__(
        self,
        llm_client,
        git_integration=None,
        monitoring_integration=None
    ):
        """
        Initialize Autonomy Engine

        Args:
            llm_client: LLM client for fix generation
            git_integration: Git integration for PR creation
            monitoring_integration: Monitoring for Level 4 auto-rollback
        """
        self.llm_client = llm_client
        self.git_integration = git_integration
        self.monitoring_integration = monitoring_integration
        self.trust_scorer = TrustScorer()

        # Action tracking
        self.actions: Dict[str, RemediationAction] = {}

        logger.info("AutonomyEngine initialized")

    def create_remediation_action(
        self,
        vulnerability: Dict[str, Any],
        contributing_findings: List[Any] = None,
        historical_data: Dict[str, Any] = None,
    ) -> RemediationAction:
        """
        Create a remediation action with appropriate autonomy level

        Args:
            vulnerability: Vulnerability to remediate
            contributing_findings: Findings from multiple agents
            historical_data: Historical remediation data

        Returns:
            RemediationAction configured for appropriate autonomy level
        """
        # Calculate trust score
        trust_score = self.trust_scorer.calculate_trust_score(
            vulnerability,
            contributing_findings,
            historical_data
        )

        # Determine autonomy level
        autonomy_level = AutonomyLevel(trust_score.recommended_level)

        # Create action
        action_id = f"rem_{vulnerability.get('id', 'unknown')}_{int(datetime.now().timestamp())}"

        action = RemediationAction(
            action_id=action_id,
            vulnerability_id=vulnerability.get("id", "unknown"),
            vulnerability_type=vulnerability.get("finding_type", "unknown"),
            severity=vulnerability.get("severity", "medium"),
            autonomy_level=autonomy_level,
            trust_score=trust_score,
            file_path=vulnerability.get("file_path", ""),
            line_start=vulnerability.get("line_start", 0),
            line_end=vulnerability.get("line_end"),
            fix_description=vulnerability.get("description", ""),
        )

        # Configure based on autonomy level
        if autonomy_level == AutonomyLevel.EXECUTE_WITH_APPROVAL:
            action.requires_approval = True

        if autonomy_level == AutonomyLevel.AUTONOMOUS:
            action.monitoring_enabled = True

        self.actions[action_id] = action

        logger.info(
            f"Created remediation action {action_id} at level {autonomy_level.value} "
            f"(trust score: {trust_score.overall_score:.2f})"
        )

        return action

    async def execute_remediation(
        self,
        action: RemediationAction,
        approval_token: Optional[str] = None
    ) -> bool:
        """
        Execute remediation based on autonomy level

        Args:
            action: Remediation action to execute
            approval_token: Approval token for Level 3

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Executing remediation {action.action_id} at level {action.autonomy_level.value}")

        try:
            if action.autonomy_level == AutonomyLevel.SUGGEST:
                return await self._execute_level1_suggest(action)

            elif action.autonomy_level == AutonomyLevel.DRAFT:
                return await self._execute_level2_draft(action)

            elif action.autonomy_level == AutonomyLevel.EXECUTE_WITH_APPROVAL:
                return await self._execute_level3_with_approval(action, approval_token)

            elif action.autonomy_level == AutonomyLevel.AUTONOMOUS:
                return await self._execute_level4_autonomous(action)

        except Exception as e:
            logger.error(f"Error executing remediation {action.action_id}: {e}")
            action.status = RemediationStatus.FAILED
            action.error_message = str(e)
            action.updated_at = datetime.now()
            return False

    async def _execute_level1_suggest(self, action: RemediationAction) -> bool:
        """
        Level 1: Generate and show suggested fix

        No automatic changes, just AI-generated suggestion
        """
        logger.info(f"Level 1: Generating suggested fix for {action.action_id}")

        # Generate fix using LLM
        suggested_fix = await self._generate_fix_with_llm(action)

        if suggested_fix:
            action.suggested_fix = suggested_fix
            action.status = RemediationStatus.COMPLETED
            action.success = True
            action.updated_at = datetime.now()

            logger.info(f"Level 1: Generated suggestion for {action.action_id}")
            return True
        else:
            action.status = RemediationStatus.FAILED
            action.error_message = "Failed to generate fix suggestion"
            action.updated_at = datetime.now()
            return False

    async def _execute_level2_draft(self, action: RemediationAction) -> bool:
        """
        Level 2: Generate fix and create PR

        Creates Git branch and pull request for review
        """
        logger.info(f"Level 2: Creating PR for {action.action_id}")

        if not self.git_integration:
            logger.error("Git integration not available for Level 2")
            action.status = RemediationStatus.FAILED
            action.error_message = "Git integration not configured"
            return False

        # Generate fix
        suggested_fix = await self._generate_fix_with_llm(action)
        if not suggested_fix:
            action.status = RemediationStatus.FAILED
            action.error_message = "Failed to generate fix"
            return False

        action.suggested_fix = suggested_fix

        # Create branch
        branch_name = f"cybret-fix-{action.vulnerability_type}-{action.action_id}"
        action.branch_name = branch_name

        # Apply fix to branch (via git integration)
        commit_sha = await self.git_integration.create_branch_with_fix(
            branch_name=branch_name,
            file_path=action.file_path,
            fix_content=suggested_fix,
            commit_message=f"Fix {action.vulnerability_type}: {action.fix_description}"
        )

        action.commit_sha = commit_sha

        # Create PR
        pr_url = await self.git_integration.create_pull_request(
            branch_name=branch_name,
            title=f"[CYBRET AI] Fix {action.severity.upper()}: {action.vulnerability_type}",
            body=self._generate_pr_description(action)
        )

        action.pr_url = pr_url
        action.status = RemediationStatus.AWAITING_APPROVAL
        action.updated_at = datetime.now()

        logger.info(f"Level 2: Created PR at {pr_url}")
        return True

    async def _execute_level3_with_approval(
        self,
        action: RemediationAction,
        approval_token: Optional[str]
    ) -> bool:
        """
        Level 3: Execute fix after explicit approval

        Requires approval token before applying fix
        """
        logger.info(f"Level 3: Processing fix for {action.action_id}")

        # Check if approval is required and provided
        if action.requires_approval and not approval_token:
            action.status = RemediationStatus.AWAITING_APPROVAL
            action.updated_at = datetime.now()
            logger.info(f"Level 3: Awaiting approval for {action.action_id}")
            return True  # Successfully moved to awaiting state

        # Validate approval token
        if approval_token and not self._validate_approval_token(approval_token, action):
            action.status = RemediationStatus.REJECTED
            action.error_message = "Invalid approval token"
            action.updated_at = datetime.now()
            return False

        # Generate and apply fix
        suggested_fix = await self._generate_fix_with_llm(action)
        if not suggested_fix:
            action.status = RemediationStatus.FAILED
            action.error_message = "Failed to generate fix"
            return False

        action.suggested_fix = suggested_fix
        action.status = RemediationStatus.IN_PROGRESS
        action.updated_at = datetime.now()

        # Apply fix directly to codebase
        success = await self._apply_fix_to_codebase(action)

        if success:
            action.status = RemediationStatus.COMPLETED
            action.success = True
            action.approved_at = datetime.now()
            logger.info(f"Level 3: Successfully applied fix for {action.action_id}")
        else:
            action.status = RemediationStatus.FAILED
            action.error_message = "Failed to apply fix to codebase"

        action.updated_at = datetime.now()
        return success

    async def _execute_level4_autonomous(self, action: RemediationAction) -> bool:
        """
        Level 4: Autonomous fix with monitoring and auto-rollback

        Highest automation - applies fix and monitors for issues
        """
        logger.info(f"Level 4: Autonomous fix for {action.action_id}")

        # Generate fix
        suggested_fix = await self._generate_fix_with_llm(action)
        if not suggested_fix:
            action.status = RemediationStatus.FAILED
            action.error_message = "Failed to generate fix"
            return False

        action.suggested_fix = suggested_fix
        action.status = RemediationStatus.IN_PROGRESS
        action.updated_at = datetime.now()

        # Apply fix
        success = await self._apply_fix_to_codebase(action)

        if not success:
            action.status = RemediationStatus.FAILED
            action.error_message = "Failed to apply fix"
            action.updated_at = datetime.now()
            return False

        action.status = RemediationStatus.COMPLETED
        action.success = True
        action.updated_at = datetime.now()

        # Enable monitoring for auto-rollback
        if self.monitoring_integration and action.monitoring_enabled:
            await self._enable_monitoring(action)
            logger.info(f"Level 4: Monitoring enabled for {action.action_id}")

        logger.info(f"Level 4: Autonomous fix completed for {action.action_id}")
        return True

    async def _generate_fix_with_llm(self, action: RemediationAction) -> Optional[str]:
        """Generate fix using LLM"""
        try:
            fix = await self.llm_client.generate_fix(
                vulnerability_type=action.vulnerability_type,
                file_path=action.file_path,
                line_start=action.line_start,
                line_end=action.line_end,
                description=action.fix_description,
            )
            return fix
        except Exception as e:
            logger.error(f"LLM fix generation failed: {e}")
            return None

    async def _apply_fix_to_codebase(self, action: RemediationAction) -> bool:
        """Apply generated fix to actual codebase"""
        try:
            # Read current file
            with open(action.file_path, 'r') as f:
                lines = f.readlines()

            # Replace lines
            if action.line_end:
                lines[action.line_start - 1:action.line_end] = [action.suggested_fix + '\n']
            else:
                lines[action.line_start - 1] = action.suggested_fix + '\n'

            # Write back
            with open(action.file_path, 'w') as f:
                f.writelines(lines)

            logger.info(f"Applied fix to {action.file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")
            return False

    async def _enable_monitoring(self, action: RemediationAction):
        """Enable monitoring for auto-rollback (Level 4)"""
        if not self.monitoring_integration:
            logger.warning("Monitoring integration not available")
            return

        await self.monitoring_integration.watch_for_errors(
            action_id=action.action_id,
            file_path=action.file_path,
            threshold=action.rollback_threshold,
            callback=lambda: self._auto_rollback(action)
        )

    async def _auto_rollback(self, action: RemediationAction):
        """Auto-rollback if monitoring detects issues"""
        logger.warning(f"Auto-rollback triggered for {action.action_id}")

        action.status = RemediationStatus.ROLLED_BACK
        action.rollback_reason = "Monitoring detected error rate above threshold"
        action.updated_at = datetime.now()

        # Revert the fix
        # Implementation depends on version control integration

    def _validate_approval_token(self, token: str, action: RemediationAction) -> bool:
        """Validate approval token for Level 3"""
        # Implementation depends on auth system
        # For now, simple check
        return bool(token)

    def _generate_pr_description(self, action: RemediationAction) -> str:
        """Generate PR description for Level 2"""
        return f"""
## Vulnerability Fix

**Type:** {action.vulnerability_type}
**Severity:** {action.severity.upper()}
**Trust Score:** {action.trust_score.overall_score:.2f}

### Description
{action.fix_description}

### Fix Reasoning
{action.fix_reasoning}

### Trust Analysis
{chr(10).join(f"- {reason}" for reason in action.trust_score.reasoning)}

---
*Generated by CYBRET AI - Autonomous Security Intelligence*
*Action ID: {action.action_id}*
        """.strip()

    def get_action(self, action_id: str) -> Optional[RemediationAction]:
        """Get remediation action by ID"""
        return self.actions.get(action_id)

    def get_pending_approvals(self) -> List[RemediationAction]:
        """Get all actions awaiting approval"""
        return [
            action for action in self.actions.values()
            if action.status == RemediationStatus.AWAITING_APPROVAL
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get remediation statistics"""
        total = len(self.actions)
        if total == 0:
            return {"total": 0}

        by_level = {level: 0 for level in AutonomyLevel}
        by_status = {status: 0 for status in RemediationStatus}
        successful = 0

        for action in self.actions.values():
            by_level[action.autonomy_level] += 1
            by_status[action.status] += 1
            if action.success:
                successful += 1

        return {
            "total_actions": total,
            "successful_fixes": successful,
            "success_rate": successful / total if total > 0 else 0,
            "by_autonomy_level": {
                level.name: count for level, count in by_level.items()
            },
            "by_status": {
                status.name: count for status, count in by_status.items()
            }
        }
