"""
Enhanced Intent Analyzer using LLM

This module uses OpenRouter LLMs to enhance intent inference with:
1. Semantic code understanding
2. Pattern discovery from context
3. Business logic inference
4. Advanced ownership detection
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from scanner.llm.openrouter_client import OpenRouterClient


@dataclass
class LLMIntentAnalysis:
    """Result from LLM intent analysis"""

    resources: List[Dict[str, Any]]
    ownership_patterns: List[str]
    security_boundaries: List[str]
    state_transitions: List[Dict[str, Any]]
    trust_boundaries: List[str]
    confidence: float
    reasoning: str


class EnhancedIntentAnalyzer:
    """
    Uses LLM to enhance intent inference beyond static analysis

    Features:
    - Semantic understanding of code purpose
    - Discovery of implicit security patterns
    - Business logic inference
    - Context-aware ownership detection
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        enable_cache: bool = True
    ):
        """
        Initialize enhanced analyzer

        Args:
            api_key: OpenRouter API key
            cache_dir: Directory for caching LLM responses
            enable_cache: Enable response caching
        """
        self.client = OpenRouterClient(
            api_key=api_key,
            default_model="anthropic/claude-3.5-sonnet"
        )
        self.enable_cache = enable_cache
        self.cache_dir = cache_dir or Path(".cache/llm_intent")

        if self.enable_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def analyze_code_intent(
        self,
        code_snippet: str,
        file_path: str,
        context: Optional[str] = None
    ) -> LLMIntentAnalysis:
        """
        Analyze code to discover security intent

        Args:
            code_snippet: Code to analyze
            file_path: Path to the file (for context)
            context: Additional context about the codebase

        Returns:
            LLMIntentAnalysis with discovered patterns
        """
        # Check cache first
        if self.enable_cache:
            cached = self._get_cached_analysis(code_snippet, context)
            if cached:
                return cached

        system_prompt = """You are a security architect analyzing code to understand security intent.

Your task is to discover:
1. **Resources**: What entities/objects are being managed (User, Document, Order, etc.)
2. **Ownership Patterns**: How ownership/authorization is checked (or should be checked)
3. **Security Boundaries**: Where user input enters and where sensitive data exits
4. **State Transitions**: Valid state changes (e.g., Order: pending → paid → shipped)
5. **Trust Boundaries**: Where trust assumptions change (user → admin, internal → external)

Focus on IMPLICIT security patterns that developers intended but may not have fully implemented.

Return your analysis in JSON format:
{
  "resources": [{"name": "User", "owner_field": "user_id", "sensitive_fields": ["email", "password"]}],
  "ownership_patterns": ["user_id == current_user.id", "object.owner == session.user"],
  "security_boundaries": ["API endpoint receives user input", "Database query returns sensitive data"],
  "state_transitions": [{"resource": "Order", "from": "pending", "to": "paid", "conditions": ["payment verified"]}],
  "trust_boundaries": ["User authentication required", "Admin role check"],
  "confidence": 0.85,
  "reasoning": "Explanation of what you discovered and why"
}"""

        user_prompt = f"""Analyze this code to discover security intent:

**File**: {file_path}

**Code**:
```
{code_snippet}
```
"""

        if context:
            user_prompt += f"\n**Context**: {context}"

        user_prompt += "\n\nProvide your analysis in JSON format."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat_completion(
            messages=messages,
            temperature=0.3,  # Lower temp for more consistent analysis
            max_tokens=2000
        )

        # Parse JSON response
        try:
            # Extract JSON from response (LLM may wrap it in markdown)
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            analysis_data = json.loads(content)

            analysis = LLMIntentAnalysis(
                resources=analysis_data.get("resources", []),
                ownership_patterns=analysis_data.get("ownership_patterns", []),
                security_boundaries=analysis_data.get("security_boundaries", []),
                state_transitions=analysis_data.get("state_transitions", []),
                trust_boundaries=analysis_data.get("trust_boundaries", []),
                confidence=analysis_data.get("confidence", 0.5),
                reasoning=analysis_data.get("reasoning", "")
            )

            # Cache the result
            if self.enable_cache:
                self._cache_analysis(code_snippet, context, analysis)

            return analysis

        except json.JSONDecodeError as e:
            # Fallback: return empty analysis with reasoning
            return LLMIntentAnalysis(
                resources=[],
                ownership_patterns=[],
                security_boundaries=[],
                state_transitions=[],
                trust_boundaries=[],
                confidence=0.0,
                reasoning=f"Failed to parse LLM response: {str(e)}\n\nRaw response: {response.content}"
            )

    def discover_missing_checks(
        self,
        endpoint_code: str,
        discovered_patterns: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to identify missing authorization checks

        Args:
            endpoint_code: Code of the endpoint/function
            discovered_patterns: Patterns found in other parts of codebase

        Returns:
            List of missing checks with recommendations
        """
        system_prompt = """You are a security auditor checking for missing authorization checks.

Given an endpoint and patterns found elsewhere in the codebase, identify:
1. What authorization checks are MISSING
2. What checks SHOULD be present based on patterns
3. Specific recommendations to fix

Return JSON array of missing checks:
[
  {
    "check_type": "ownership_verification",
    "description": "Missing check for document ownership",
    "severity": "high",
    "recommendation": "Add: if document.user_id != current_user.id: abort(403)",
    "confidence": 0.9
  }
]"""

        user_prompt = f"""Endpoint Code:
```
{endpoint_code}
```

Common Patterns Found in Codebase:
{json.dumps(discovered_patterns, indent=2)}

What authorization checks are missing? Return JSON array."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat_completion(
            messages=messages,
            temperature=0.2,
            max_tokens=1500
        )

        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
        except:
            return []

    def explain_vulnerability_context(
        self,
        vulnerability: Dict[str, Any],
        surrounding_code: str
    ) -> str:
        """
        Get LLM explanation of vulnerability in context

        Args:
            vulnerability: Vulnerability details
            surrounding_code: Code around the vulnerability

        Returns:
            Detailed explanation with business impact
        """
        system_prompt = """You are a senior security engineer explaining vulnerabilities.

Provide:
1. WHY this is vulnerable (root cause)
2. HOW attackers would exploit it (step-by-step)
3. WHAT the business impact is (financial, reputation, compliance)
4. HOW to fix it (specific code changes)

Be clear and actionable."""

        user_prompt = f"""Vulnerability Details:
- Type: {vulnerability.get('vuln_type')}
- Severity: {vulnerability.get('severity')}
- Location: {vulnerability.get('file_path')}:{vulnerability.get('line_start')}
- Description: {vulnerability.get('description')}

Surrounding Code:
```
{surrounding_code}
```

Explain this vulnerability comprehensively."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat_completion(
            messages=messages,
            temperature=0.4,
            max_tokens=2000
        )

        return response.content

    def _get_cache_key(self, code_snippet: str, context: Optional[str]) -> str:
        """Generate cache key from code and context"""
        content = code_snippet + (context or "")
        return hashlib.sha256(content.encode()).hexdigest()

    def _get_cached_analysis(
        self,
        code_snippet: str,
        context: Optional[str]
    ) -> Optional[LLMIntentAnalysis]:
        """Retrieve cached analysis if available"""
        cache_key = self._get_cache_key(code_snippet, context)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    return LLMIntentAnalysis(**data)
            except:
                pass

        return None

    def _cache_analysis(
        self,
        code_snippet: str,
        context: Optional[str],
        analysis: LLMIntentAnalysis
    ):
        """Cache analysis result"""
        cache_key = self._get_cache_key(code_snippet, context)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            with open(cache_file, 'w') as f:
                json.dump(asdict(analysis), f, indent=2)
        except Exception as e:
            # Don't fail if caching fails
            pass

    def close(self):
        """Close the LLM client"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
