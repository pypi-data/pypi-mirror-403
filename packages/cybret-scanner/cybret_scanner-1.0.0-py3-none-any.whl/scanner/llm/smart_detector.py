"""
Smart Vulnerability Detector with LLM Enhancement

Combines static analysis with LLM intelligence for:
1. Reduced false positives
2. Context-aware detection
3. Semantic vulnerability understanding
4. Custom pattern discovery
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from scanner.llm.openrouter_client import OpenRouterClient


@dataclass
class SmartDetectionResult:
    """Result from smart detection"""

    is_vulnerable: bool
    confidence: float
    vulnerability_type: str
    severity: str
    explanation: str
    attack_scenario: str
    remediation: str
    false_positive_analysis: str


class SmartDetector:
    """
    Enhances traditional detectors with LLM intelligence

    Two-stage detection:
    1. Fast static analysis (traditional)
    2. LLM validation (reduces false positives)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_fast_model_for_triage: bool = True
    ):
        """
        Initialize smart detector

        Args:
            api_key: OpenRouter API key
            use_fast_model_for_triage: Use Haiku for fast triage, Sonnet for deep analysis
        """
        self.use_fast_model = use_fast_model_for_triage

        # Fast model for triage
        self.triage_client = OpenRouterClient(
            api_key=api_key,
            default_model="anthropic/claude-3-haiku"
        )

        # Powerful model for deep analysis
        self.analysis_client = OpenRouterClient(
            api_key=api_key,
            default_model="anthropic/claude-3.5-sonnet"
        )

    def validate_vulnerability(
        self,
        code_snippet: str,
        vulnerability_type: str,
        static_analysis_evidence: Dict[str, Any]
    ) -> SmartDetectionResult:
        """
        Validate a potential vulnerability found by static analysis

        Args:
            code_snippet: The suspicious code
            vulnerability_type: Type detected by static analysis
            static_analysis_evidence: Evidence from static detector

        Returns:
            SmartDetectionResult with LLM validation
        """
        # Stage 1: Fast triage (is this worth deep analysis?)
        if self.use_fast_model:
            is_worth_analysis = self._fast_triage(
                code_snippet,
                vulnerability_type,
                static_analysis_evidence
            )

            if not is_worth_analysis:
                return SmartDetectionResult(
                    is_vulnerable=False,
                    confidence=0.9,
                    vulnerability_type=vulnerability_type,
                    severity="info",
                    explanation="Fast triage determined this is likely a false positive",
                    attack_scenario="N/A",
                    remediation="N/A",
                    false_positive_analysis="Static pattern matched but semantic analysis shows no vulnerability"
                )

        # Stage 2: Deep analysis with powerful model
        return self._deep_analysis(
            code_snippet,
            vulnerability_type,
            static_analysis_evidence
        )

    def _fast_triage(
        self,
        code_snippet: str,
        vulnerability_type: str,
        evidence: Dict[str, Any]
    ) -> bool:
        """
        Fast triage to filter out obvious false positives

        Returns:
            True if worth deep analysis, False if likely false positive
        """
        system_prompt = """You are a security triage bot. Quickly determine if code is likely vulnerable.

Answer with just: VULNERABLE or SAFE

VULNERABLE = Definitely needs deeper analysis
SAFE = Likely false positive, skip deep analysis"""

        user_prompt = f"""Static analyzer flagged this as {vulnerability_type}:

```
{code_snippet}
```

Evidence: {evidence.get('description', 'N/A')}

Is this VULNERABLE or SAFE?"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.triage_client.chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=10
        )

        return "VULNERABLE" in response.content.upper()

    def _deep_analysis(
        self,
        code_snippet: str,
        vulnerability_type: str,
        evidence: Dict[str, Any]
    ) -> SmartDetectionResult:
        """
        Deep analysis with powerful model

        Returns:
            Comprehensive analysis result
        """
        system_prompt = """You are a senior security engineer performing deep vulnerability analysis.

Analyze the code and provide a comprehensive security assessment.

Return JSON:
{
  "is_vulnerable": true/false,
  "confidence": 0.0-1.0,
  "vulnerability_type": "IDOR|AUTH_BYPASS|etc",
  "severity": "critical|high|medium|low|info",
  "explanation": "Why this is/isn't vulnerable",
  "attack_scenario": "Step-by-step attack (if vulnerable)",
  "remediation": "How to fix (if vulnerable)",
  "false_positive_analysis": "Why static analysis flagged this"
}"""

        user_prompt = f"""Static Analysis Result:
- Flagged as: {vulnerability_type}
- Evidence: {evidence}

Code to Analyze:
```
{code_snippet}
```

Is this a real vulnerability? Provide detailed JSON analysis."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.analysis_client.chat_completion(
            messages=messages,
            temperature=0.2,
            max_tokens=2000
        )

        # Parse JSON response
        try:
            import json

            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)

            return SmartDetectionResult(
                is_vulnerable=data.get("is_vulnerable", True),
                confidence=data.get("confidence", 0.5),
                vulnerability_type=data.get("vulnerability_type", vulnerability_type),
                severity=data.get("severity", "medium"),
                explanation=data.get("explanation", ""),
                attack_scenario=data.get("attack_scenario", ""),
                remediation=data.get("remediation", ""),
                false_positive_analysis=data.get("false_positive_analysis", "")
            )

        except Exception as e:
            # Fallback: assume vulnerable but low confidence
            return SmartDetectionResult(
                is_vulnerable=True,
                confidence=0.5,
                vulnerability_type=vulnerability_type,
                severity="medium",
                explanation=f"LLM analysis failed: {str(e)}",
                attack_scenario="Unable to generate",
                remediation="Manual review required",
                false_positive_analysis="Could not validate with LLM"
            )

    def discover_new_patterns(
        self,
        codebase_sample: str,
        known_vulnerabilities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to discover new vulnerability patterns in codebase

        Args:
            codebase_sample: Sample of code from the codebase
            known_vulnerabilities: Previously detected vulnerabilities

        Returns:
            List of new potential vulnerability patterns
        """
        system_prompt = """You are a vulnerability researcher discovering new patterns.

Analyze the codebase and known vulnerabilities to:
1. Identify NEW vulnerability patterns not yet covered
2. Find common anti-patterns
3. Suggest additional detection rules

Return JSON array of new patterns:
[
  {
    "pattern_name": "Missing Rate Limiting",
    "description": "API endpoints without rate limiting",
    "cypher_query": "MATCH (e:Endpoint) WHERE NOT (e)-[:HAS_MIDDLEWARE]->(:RateLimiter)",
    "severity": "medium",
    "confidence": 0.75
  }
]"""

        user_prompt = f"""Codebase Sample:
```
{codebase_sample}
```

Known Vulnerabilities:
{known_vulnerabilities[:5]}  # First 5 for context

Discover new vulnerability patterns. Return JSON array."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.analysis_client.chat_completion(
            messages=messages,
            temperature=0.5,  # Higher temp for creative pattern discovery
            max_tokens=2500
        )

        try:
            import json

            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
        except:
            return []

    def generate_custom_detector(
        self,
        vulnerability_description: str,
        example_code: str
    ) -> str:
        """
        Generate a custom Cypher query for detecting specific vulnerability

        Args:
            vulnerability_description: Description of what to detect
            example_code: Example of vulnerable code

        Returns:
            Cypher query for detection
        """
        system_prompt = """You are a graph query expert creating Cypher queries for vulnerability detection.

Given a vulnerability description and example, generate a Cypher query that detects it in a Neo4j code graph.

Available node types: Endpoint, Function, Call, DatabaseQuery, Variable, Parameter
Available relationships: HAS_CHILD, CALLS, USES, HAS_DECORATOR

Return only the Cypher query, no explanation."""

        user_prompt = f"""Vulnerability: {vulnerability_description}

Example Vulnerable Code:
```
{example_code}
```

Generate Cypher query to detect this pattern:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.analysis_client.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )

        # Extract Cypher query
        content = response.content
        if "```cypher" in content:
            return content.split("```cypher")[1].split("```")[0].strip()
        elif "```" in content:
            return content.split("```")[1].split("```")[0].strip()
        else:
            return content.strip()

    def close(self):
        """Close LLM clients"""
        self.triage_client.close()
        self.analysis_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
