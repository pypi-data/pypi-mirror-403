"""
Trust Scorer - Determines autonomy level based on confidence metrics

Analyzes vulnerability characteristics to determine appropriate
autonomy level for remediation.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class ConfidenceFactor(Enum):
    """Factors contributing to trust score"""
    AGENT_CONSENSUS = "agent_consensus"  # Multiple agents agree
    PATTERN_MATCH = "pattern_match"  # Known vulnerability pattern
    LLM_VALIDATION = "llm_validation"  # LLM confirmed the issue
    CODE_COMPLEXITY = "code_complexity"  # Simple vs complex fix
    BLAST_RADIUS = "blast_radius"  # Impact scope of fix
    HISTORICAL_SUCCESS = "historical_success"  # Past fix success rate
    TEST_COVERAGE = "test_coverage"  # Tests covering this code


@dataclass
class TrustScore:
    """
    Trust score for autonomous remediation decision

    Score ranges:
    - 0.0 - 0.4: Level 1 (Suggest only)
    - 0.4 - 0.6: Level 2 (Draft PR)
    - 0.6 - 0.8: Level 3 (Execute with approval)
    - 0.8 - 1.0: Level 4 (Autonomous)
    """
    overall_score: float  # 0.0 to 1.0
    confidence_factors: Dict[ConfidenceFactor, float]
    recommended_level: int  # 1-4
    reasoning: List[str]


class TrustScorer:
    """
    Calculates trust scores for autonomous remediation decisions

    Uses multiple signals to determine how much autonomy to grant:
    - Agent consensus (multiple agents detecting same issue)
    - Pattern confidence (how well it matches known patterns)
    - LLM validation (AI confirmation of vulnerability)
    - Code complexity (simpler = higher trust)
    - Blast radius (smaller impact = higher trust)
    - Historical data (past success rate)
    - Test coverage (better tests = higher trust)
    """

    # Weights for each confidence factor
    FACTOR_WEIGHTS = {
        ConfidenceFactor.AGENT_CONSENSUS: 0.25,
        ConfidenceFactor.PATTERN_MATCH: 0.15,
        ConfidenceFactor.LLM_VALIDATION: 0.20,
        ConfidenceFactor.CODE_COMPLEXITY: 0.15,
        ConfidenceFactor.BLAST_RADIUS: 0.10,
        ConfidenceFactor.HISTORICAL_SUCCESS: 0.10,
        ConfidenceFactor.TEST_COVERAGE: 0.05,
    }

    def calculate_trust_score(
        self,
        vulnerability: Dict[str, Any],
        contributing_findings: List[Any] = None,
        historical_data: Dict[str, Any] = None,
    ) -> TrustScore:
        """
        Calculate trust score for a vulnerability

        Args:
            vulnerability: Vulnerability data
            contributing_findings: Findings from multiple agents
            historical_data: Historical remediation success data

        Returns:
            TrustScore with overall score and recommendation
        """
        confidence_factors = {}
        reasoning = []

        # Factor 1: Agent Consensus
        agent_consensus_score = self._score_agent_consensus(
            contributing_findings or []
        )
        confidence_factors[ConfidenceFactor.AGENT_CONSENSUS] = agent_consensus_score
        if agent_consensus_score > 0.7:
            reasoning.append(f"Multiple agents agree ({agent_consensus_score:.2f} consensus)")
        elif agent_consensus_score < 0.3:
            reasoning.append("Low agent consensus - needs human review")

        # Factor 2: Pattern Match
        pattern_match_score = self._score_pattern_match(vulnerability)
        confidence_factors[ConfidenceFactor.PATTERN_MATCH] = pattern_match_score
        if pattern_match_score > 0.8:
            reasoning.append("Well-known vulnerability pattern detected")

        # Factor 3: LLM Validation
        llm_validation_score = vulnerability.get("confidence", 0.5)
        confidence_factors[ConfidenceFactor.LLM_VALIDATION] = llm_validation_score

        # Factor 4: Code Complexity
        code_complexity_score = self._score_code_complexity(vulnerability)
        confidence_factors[ConfidenceFactor.CODE_COMPLEXITY] = code_complexity_score
        if code_complexity_score < 0.4:
            reasoning.append("Complex code - requires careful review")

        # Factor 5: Blast Radius
        blast_radius_score = self._score_blast_radius(vulnerability)
        confidence_factors[ConfidenceFactor.BLAST_RADIUS] = blast_radius_score
        if blast_radius_score < 0.5:
            reasoning.append("Large blast radius - high impact fix")

        # Factor 6: Historical Success
        if historical_data:
            historical_score = self._score_historical_success(
                vulnerability, historical_data
            )
        else:
            historical_score = 0.5  # Neutral if no history
        confidence_factors[ConfidenceFactor.HISTORICAL_SUCCESS] = historical_score

        # Factor 7: Test Coverage
        test_coverage_score = self._score_test_coverage(vulnerability)
        confidence_factors[ConfidenceFactor.TEST_COVERAGE] = test_coverage_score
        if test_coverage_score > 0.7:
            reasoning.append("Good test coverage - safer to auto-fix")

        # Calculate weighted overall score
        overall_score = sum(
            score * self.FACTOR_WEIGHTS[factor]
            for factor, score in confidence_factors.items()
        )

        # Determine recommended autonomy level
        if overall_score >= 0.8:
            recommended_level = 4
            reasoning.append("HIGH TRUST: Safe for autonomous remediation")
        elif overall_score >= 0.6:
            recommended_level = 3
            reasoning.append("MEDIUM-HIGH TRUST: Execute with approval")
        elif overall_score >= 0.4:
            recommended_level = 2
            reasoning.append("MEDIUM TRUST: Draft PR for review")
        else:
            recommended_level = 1
            reasoning.append("LOW TRUST: Suggest fix only")

        return TrustScore(
            overall_score=overall_score,
            confidence_factors=confidence_factors,
            recommended_level=recommended_level,
            reasoning=reasoning,
        )

    def _score_agent_consensus(self, contributing_findings: List[Any]) -> float:
        """
        Score based on how many agents agree on the issue

        More agents = higher confidence
        """
        if not contributing_findings:
            return 0.5  # Neutral if no data

        num_agents = len(set(f.agent_name for f in contributing_findings))

        if num_agents >= 4:
            return 1.0  # 4+ agents agree = very high confidence
        elif num_agents == 3:
            return 0.8
        elif num_agents == 2:
            return 0.6
        else:
            return 0.4  # Single agent = lower confidence

    def _score_pattern_match(self, vulnerability: Dict[str, Any]) -> float:
        """
        Score based on how well it matches known patterns

        Well-known patterns = higher confidence
        """
        finding_type = vulnerability.get("finding_type", "")

        # High confidence patterns (well-known vulnerabilities)
        high_confidence_patterns = {
            "sql_injection", "unvalidated_input", "price_manipulation",
            "missing_authentication", "privilege_escalation"
        }

        # Medium confidence patterns
        medium_confidence_patterns = {
            "missing_ownership_check", "race_condition", "toctou",
            "negative_value_handling", "cross_service_trust"
        }

        if finding_type in high_confidence_patterns:
            return 0.9
        elif finding_type in medium_confidence_patterns:
            return 0.7
        else:
            return 0.5

    def _score_code_complexity(self, vulnerability: Dict[str, Any]) -> float:
        """
        Score based on code complexity

        Simpler code = higher confidence in fix
        Lower score = more complex, needs human review
        """
        # Estimate complexity from various signals
        evidence = vulnerability.get("evidence", {})

        # Check path length (longer paths = more complex)
        path_length = evidence.get("path_length", 1)
        if path_length > 5:
            complexity_penalty = 0.3
        elif path_length > 3:
            complexity_penalty = 0.15
        else:
            complexity_penalty = 0.0

        # Check if involves multiple files (cross-file = more complex)
        cross_file = evidence.get("cross_file", False)
        if cross_file:
            complexity_penalty += 0.2

        # Start with high score, reduce based on complexity
        return max(0.0, 1.0 - complexity_penalty)

    def _score_blast_radius(self, vulnerability: Dict[str, Any]) -> float:
        """
        Score based on potential impact of fix

        Smaller blast radius = higher confidence
        """
        evidence = vulnerability.get("evidence", {})

        # Check if it affects multiple endpoints/functions
        num_affected = evidence.get("affected_count", 1)

        if num_affected == 1:
            return 0.9  # Single location = small blast radius
        elif num_affected <= 3:
            return 0.7
        elif num_affected <= 10:
            return 0.5
        else:
            return 0.3  # Many locations = large blast radius

    def _score_historical_success(
        self,
        vulnerability: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> float:
        """
        Score based on past remediation success rate

        Historical data format:
        {
            "finding_type": {
                "total_fixes": int,
                "successful_fixes": int,
                "rollback_rate": float
            }
        }
        """
        finding_type = vulnerability.get("finding_type", "")

        if finding_type not in historical_data:
            return 0.5  # No history = neutral score

        stats = historical_data[finding_type]

        if stats["total_fixes"] < 5:
            return 0.5  # Not enough data

        success_rate = stats["successful_fixes"] / stats["total_fixes"]
        rollback_penalty = stats.get("rollback_rate", 0.0) * 0.5

        return max(0.0, success_rate - rollback_penalty)

    def _score_test_coverage(self, vulnerability: Dict[str, Any]) -> float:
        """
        Score based on test coverage

        Better test coverage = safer to auto-fix
        """
        evidence = vulnerability.get("evidence", {})
        test_coverage = evidence.get("test_coverage_percent", 0)

        if test_coverage >= 80:
            return 0.9
        elif test_coverage >= 60:
            return 0.7
        elif test_coverage >= 40:
            return 0.5
        elif test_coverage >= 20:
            return 0.3
        else:
            return 0.1

    def calculate_batch_trust_score(
        self,
        vulnerabilities: List[Dict[str, Any]]
    ) -> Dict[str, TrustScore]:
        """
        Calculate trust scores for multiple vulnerabilities

        Args:
            vulnerabilities: List of vulnerabilities

        Returns:
            Dictionary mapping vulnerability ID to TrustScore
        """
        return {
            vuln.get("id", str(idx)): self.calculate_trust_score(vuln)
            for idx, vuln in enumerate(vulnerabilities)
        }
