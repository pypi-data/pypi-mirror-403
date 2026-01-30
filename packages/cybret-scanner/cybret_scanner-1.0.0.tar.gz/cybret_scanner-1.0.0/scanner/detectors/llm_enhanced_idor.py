"""
LLM-Enhanced IDOR Detector

Combines static Cypher analysis with LLM intelligence for:
1. Reduced false positives
2. Better attack scenario generation
3. Context-aware severity assessment
"""

import os
from typing import List, Optional
from pathlib import Path

from scanner.detectors.idor import IDORDetector
from scanner.detectors.base import Vulnerability
from scanner.llm.smart_detector import SmartDetector
from scanner.llm.enhanced_intent_analyzer import EnhancedIntentAnalyzer


class LLMEnhancedIDORDetector(IDORDetector):
    """
    IDOR detector enhanced with LLM capabilities

    Workflow:
    1. Run traditional static detection (Cypher queries)
    2. Validate each finding with LLM
    3. Enhance vulnerability details with LLM analysis
    4. Filter false positives
    """

    def __init__(
        self,
        driver,
        database: str = "neo4j",
        enable_llm: bool = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize LLM-enhanced detector

        Args:
            driver: Neo4j driver
            database: Database name
            enable_llm: Enable LLM features (defaults to ENABLE_AI_ANALYSIS env var)
            api_key: OpenRouter API key
        """
        super().__init__(driver, database)

        # Check if LLM is enabled
        if enable_llm is None:
            enable_llm = os.getenv("ENABLE_AI_ANALYSIS", "false").lower() == "true"

        self.enable_llm = enable_llm and os.getenv("OPENROUTER_API_KEY") is not None

        if self.enable_llm:
            self.smart_detector = SmartDetector(api_key=api_key)
            self.intent_analyzer = EnhancedIntentAnalyzer(api_key=api_key)
        else:
            self.smart_detector = None
            self.intent_analyzer = None

    def detect(self, scan_id: str) -> List[Vulnerability]:
        """
        Detect IDOR vulnerabilities with LLM enhancement

        Args:
            scan_id: Scan ID to analyze

        Returns:
            List of validated vulnerabilities
        """
        # Step 1: Run traditional detection
        vulnerabilities = super().detect(scan_id)

        if not self.enable_llm or not vulnerabilities:
            return vulnerabilities

        print(f"\n🤖 LLM Enhancement: Validating {len(vulnerabilities)} findings...")

        # Step 2: Validate with LLM
        validated_vulns = []

        for idx, vuln in enumerate(vulnerabilities):
            print(f"  [{idx+1}/{len(vulnerabilities)}] Validating {vuln.vuln_id[:12]}...")

            # Get code snippet
            code_snippet = self._get_code_snippet(vuln)

            # Validate with LLM
            validation_result = self.smart_detector.validate_vulnerability(
                code_snippet=code_snippet,
                vulnerability_type="IDOR",
                static_analysis_evidence={
                    "description": vuln.description,
                    "line": vuln.line_start,
                    "function": vuln.function_name
                }
            )

            # Only keep if LLM confirms it's vulnerable
            if validation_result.is_vulnerable and validation_result.confidence > 0.6:
                # Enhance vulnerability with LLM insights
                vuln = self._enhance_vulnerability(vuln, validation_result)
                validated_vulns.append(vuln)

                print(f"    [X] Confirmed (confidence: {validation_result.confidence:.0%})")
            else:
                print(f"    [ ] False positive (confidence: {validation_result.confidence:.0%})")

        false_positive_count = len(vulnerabilities) - len(validated_vulns)
        if false_positive_count > 0:
            print(f"\n  🎯 Filtered out {false_positive_count} false positives")

        # Step 3: Enhance with intent analysis
        if validated_vulns and self.intent_analyzer:
            validated_vulns = self._enhance_with_intent_analysis(validated_vulns, scan_id)

        return validated_vulns

    def _get_code_snippet(self, vuln: Vulnerability, context_lines: int = 10) -> str:
        """
        Extract code snippet around vulnerability

        Args:
            vuln: Vulnerability object
            context_lines: Number of lines before/after to include

        Returns:
            Code snippet as string
        """
        try:
            file_path = Path(vuln.file_path)
            if not file_path.exists():
                return f"# Unable to read {file_path}\n# Line {vuln.line_start}"

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            start = max(0, vuln.line_start - context_lines - 1)
            end = min(len(lines), vuln.line_start + context_lines)

            snippet = "".join(lines[start:end])
            return snippet

        except Exception as e:
            return f"# Error reading file: {str(e)}\n# Line {vuln.line_start}"

    def _enhance_vulnerability(
        self,
        vuln: Vulnerability,
        llm_result
    ) -> Vulnerability:
        """
        Enhance vulnerability with LLM analysis

        Args:
            vuln: Original vulnerability
            llm_result: Result from LLM analysis

        Returns:
            Enhanced vulnerability
        """
        # Update severity if LLM has different assessment
        if llm_result.severity != vuln.severity.value:
            from scanner.models.vulnerability import Severity
            vuln.severity = Severity(llm_result.severity)

        # Enhance description with LLM explanation
        if llm_result.explanation:
            vuln.description += f"\n\n**LLM Analysis**: {llm_result.explanation}"

        # Add LLM insights to evidence
        vuln.evidence["llm_validation"] = {
            "confidence": llm_result.confidence,
            "attack_scenario": llm_result.attack_scenario,
            "remediation": llm_result.remediation,
            "false_positive_analysis": llm_result.false_positive_analysis
        }

        return vuln

    def _enhance_with_intent_analysis(
        self,
        vulnerabilities: List[Vulnerability],
        scan_id: str
    ) -> List[Vulnerability]:
        """
        Use intent analyzer to add context to vulnerabilities

        Args:
            vulnerabilities: List of vulnerabilities
            scan_id: Scan ID

        Returns:
            Vulnerabilities with enhanced context
        """
        print("\n  🧠 Analyzing intent patterns...")

        for vuln in vulnerabilities:
            code_snippet = self._get_code_snippet(vuln, context_lines=15)

            # Analyze intent
            intent_analysis = self.intent_analyzer.analyze_code_intent(
                code_snippet=code_snippet,
                file_path=vuln.file_path,
                context=f"IDOR vulnerability at line {vuln.line_start}"
            )

            # Add intent insights to evidence
            vuln.evidence["intent_analysis"] = {
                "discovered_resources": intent_analysis.resources,
                "expected_patterns": intent_analysis.ownership_patterns,
                "security_boundaries": intent_analysis.security_boundaries,
                "confidence": intent_analysis.confidence,
                "reasoning": intent_analysis.reasoning
            }

        return vulnerabilities

    def __del__(self):
        """Cleanup LLM clients"""
        if self.smart_detector:
            self.smart_detector.close()
        if self.intent_analyzer:
            self.intent_analyzer.close()
