"""
LLM-Enhanced Autonomous Remediation

This module provides the main interface for integrating LLM-based
autonomous remediation with the scanner.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from scanner.llm import get_llm_client
from scanner.llm.agents import AgentOrchestrator, VulnerabilityContext
from scanner.llm.context_builder import ContextBuilder
from scanner.detectors.base import Vulnerability
from scanner.models.route_graph import RouteSpec


class RemediationEngine:
    """
    Main engine for LLM-enhanced autonomous remediation

    Orchestrates the complete pipeline:
    Scanner Detection → Context Building → LLM Analysis → Fix Generation
    """

    def __init__(self, codebase_path: str, llm_provider: Optional[str] = None):
        """
        Initialize remediation engine

        Args:
            codebase_path: Path to the codebase root
            llm_provider: Optional LLM provider ("openai", "anthropic", "ollama", "mock")
                         If None, auto-detects from environment
        """
        self.codebase_path = Path(codebase_path)
        self.context_builder = ContextBuilder(str(codebase_path))

        # Initialize LLM client
        if llm_provider:
            from scanner.llm.llm_client import LLMClientFactory, LLMProvider
            provider_enum = LLMProvider[llm_provider.upper()]
            self.llm_client = LLMClientFactory.create(provider_enum)
        else:
            self.llm_client = get_llm_client()

        # Initialize orchestrator
        self.orchestrator = AgentOrchestrator(self.llm_client)

    def analyze_vulnerability(
        self,
        vulnerability: Vulnerability,
        route: Optional[RouteSpec] = None
    ) -> Dict[str, Any]:
        """
        Analyze a single vulnerability and generate remediation

        Args:
            vulnerability: Detected vulnerability from scanner
            route: Optional route specification (improves context)

        Returns:
            Complete remediation analysis with fix suggestion
        """

        # Build context
        vuln_context = self.context_builder.build_from_vulnerability(
            vulnerability, route
        )

        # Run autonomous remediation
        result = self.orchestrator.autonomous_remediation(vuln_context)

        # Add metadata
        result['vulnerability_id'] = vulnerability.vuln_id
        result['vulnerability_type'] = vulnerability.vuln_type
        result['severity'] = vulnerability.severity.value
        result['location'] = f"{vulnerability.file_path}:{vulnerability.line_start}"

        return result

    def analyze_batch(
        self,
        vulnerabilities: List[Vulnerability],
        routes: Optional[Dict[str, RouteSpec]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple vulnerabilities in batch

        Args:
            vulnerabilities: List of detected vulnerabilities
            routes: Optional mapping of file:line -> RouteSpec

        Returns:
            List of remediation analyses
        """

        results = []

        for vuln in vulnerabilities:
            # Try to find matching route
            route = None
            if routes:
                route_key = f"{vuln.file_path}:{vuln.line_start}"
                route = routes.get(route_key)

            # Analyze
            try:
                result = self.analyze_vulnerability(vuln, route)
                results.append(result)
            except Exception as e:
                # Log error but continue with other vulnerabilities
                print(f"Error analyzing {vuln.vuln_id}: {e}")
                results.append({
                    'vulnerability_id': vuln.vuln_id,
                    'error': str(e),
                    'approved': False
                })

        return results

    def get_approved_fixes(
        self,
        analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter analyses to only return approved fixes

        Args:
            analyses: List of remediation analyses

        Returns:
            List of approved fixes ready for application
        """

        return [
            analysis for analysis in analyses
            if analysis.get('approved', False)
        ]

    def generate_remediation_report(
        self,
        analyses: List[Dict[str, Any]],
        output_format: str = "markdown"
    ) -> str:
        """
        Generate human-readable remediation report

        Args:
            analyses: List of remediation analyses
            output_format: "markdown" or "json"

        Returns:
            Formatted report
        """

        if output_format == "json":
            import json
            return json.dumps(analyses, indent=2, default=str)

        # Markdown format
        report = "# Autonomous Remediation Report\n\n"

        approved = self.get_approved_fixes(analyses)
        rejected = [a for a in analyses if not a.get('approved', False)]

        report += f"## Summary\n\n"
        report += f"- Total Vulnerabilities: {len(analyses)}\n"
        report += f"- Approved Fixes: {len(approved)}\n"
        report += f"- Rejected/Needs Review: {len(rejected)}\n\n"

        # Approved fixes
        if approved:
            report += "## Approved Fixes (Ready for Deployment)\n\n"
            for i, analysis in enumerate(approved, 1):
                report += f"### {i}. {analysis.get('vulnerability_type', 'Unknown')}\n\n"
                report += f"**Location:** {analysis.get('location', 'Unknown')}\n\n"
                report += f"**Severity:** {analysis.get('severity', 'Unknown').upper()}\n\n"

                fix = analysis.get('fix', {})
                report += f"**Fix Explanation:**\n{fix.get('explanation', 'N/A')}\n\n"

                validation = analysis.get('validation', {})
                report += f"**Validation:**\n"
                report += f"- Coverage: {validation.get('coverage_score', 0):.0%}\n"
                report += f"- Quality: {validation.get('quality_score', 0):.0%}\n\n"

        # Rejected/Needs review
        if rejected:
            report += "## Needs Review\n\n"
            for i, analysis in enumerate(rejected, 1):
                report += f"### {i}. {analysis.get('vulnerability_type', 'Unknown')}\n\n"
                report += f"**Location:** {analysis.get('location', 'Unknown')}\n\n"

                if 'error' in analysis:
                    report += f"**Error:** {analysis['error']}\n\n"
                else:
                    validation = analysis.get('validation', {})
                    report += f"**Reason:** {validation.get('reasoning', 'N/A')}\n\n"

        return report


def analyze_scan_results(
    scan_id: str,
    vulnerabilities: List[Vulnerability],
    codebase_path: str,
    routes: Optional[Dict[str, RouteSpec]] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to analyze all vulnerabilities from a scan

    Args:
        scan_id: Scan identifier
        vulnerabilities: Detected vulnerabilities
        codebase_path: Path to codebase
        routes: Optional route specifications
        output_file: Optional file to write report

    Returns:
        Dictionary with analyses and summary
    """

    engine = RemediationEngine(codebase_path)

    print(f"\n[LLM] Starting autonomous remediation for {len(vulnerabilities)} vulnerabilities...")
    print(f"[LLM] Using LLM provider: {engine.llm_client.config.provider.value}")
    print(f"[LLM] Model: {engine.llm_client.config.model}")

    analyses = engine.analyze_batch(vulnerabilities, routes)

    approved = engine.get_approved_fixes(analyses)

    print(f"[LLM] Complete! {len(approved)}/{len(vulnerabilities)} fixes approved")

    # Generate report
    report = engine.generate_remediation_report(analyses)

    # Save report if requested
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"[LLM] Report saved to {output_file}")

    return {
        'scan_id': scan_id,
        'total_vulnerabilities': len(vulnerabilities),
        'analyses': analyses,
        'approved_fixes': approved,
        'report': report
    }


__all__ = [
    'RemediationEngine',
    'analyze_scan_results'
]
