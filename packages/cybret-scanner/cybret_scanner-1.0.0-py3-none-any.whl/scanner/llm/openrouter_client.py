"""
OpenRouter API client for LLM-powered vulnerability analysis
"""

import os
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from LLM"""

    content: str
    model: str
    tokens_used: int
    cost: float


class OpenRouterClient:
    """
    Client for OpenRouter API

    Supports multiple models:
    - anthropic/claude-3.5-sonnet
    - openai/gpt-4-turbo
    - meta-llama/llama-3.1-70b-instruct
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        default_model: str = "anthropic/claude-3.5-sonnet",
    ):
        """
        Initialize OpenRouter client

        Args:
            api_key: OpenRouter API key (reads from OPENROUTER_API_KEY env var if not provided)
            base_url: OpenRouter API base URL
            default_model: Default model to use
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable "
                "or pass api_key parameter"
            )

        self.base_url = base_url
        self.default_model = default_model
        self.client = httpx.Client(timeout=60.0)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """
        Send chat completion request

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to client's default_model)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse object

        Example:
            messages = [
                {"role": "system", "content": "You are a security expert."},
                {"role": "user", "content": "Analyze this vulnerability..."}
            ]
            response = client.chat_completion(messages)
            print(response.content)
        """
        model = model or self.default_model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cybret.ai",  # Optional: for rankings
            "X-Title": "CYBRET AI Scanner",  # Optional: for rankings
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            # Extract response
            content = data["choices"][0]["message"]["content"]

            # Extract usage stats
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)

            # Calculate cost (approximate, depends on model)
            cost = self._estimate_cost(model, tokens_used)

            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens_used,
                cost=cost,
            )

        except httpx.HTTPStatusError as e:
            raise Exception(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Failed to call OpenRouter API: {str(e)}")

    def analyze_vulnerability(
        self,
        code_snippet: str,
        vulnerability_type: str,
        context: Optional[str] = None,
    ) -> str:
        """
        Use LLM to analyze a vulnerability and provide detailed explanation

        Args:
            code_snippet: The vulnerable code
            vulnerability_type: Type of vulnerability (IDOR, AUTH_BYPASS, etc.)
            context: Additional context about the code

        Returns:
            Detailed analysis from LLM
        """
        system_prompt = """You are a senior security engineer specializing in application security.
Analyze the provided code snippet and vulnerability type, then provide:
1. A clear explanation of why this is vulnerable
2. Specific attack scenarios
3. Detailed remediation steps with code examples
4. Additional security considerations

Be concise but thorough. Use security best practices."""

        user_prompt = f"""Vulnerability Type: {vulnerability_type}

Code Snippet:
```
{code_snippet}
```
"""

        if context:
            user_prompt += f"\n\nContext:\n{context}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = self.chat_completion(
            messages=messages,
            temperature=0.3,  # Lower temperature for more focused analysis
            max_tokens=1500,
        )

        return response.content

    def generate_fix(
        self,
        vulnerable_code: str,
        vulnerability_description: str,
        language: str = "python",
    ) -> str:
        """
        Generate a secure version of vulnerable code

        Args:
            vulnerable_code: The vulnerable code
            vulnerability_description: Description of the vulnerability
            language: Programming language

        Returns:
            Fixed code with explanation
        """
        system_prompt = f"""You are a senior {language} developer and security expert.
Generate a secure, fixed version of the provided vulnerable code.
Include:
1. The fixed code
2. Explanation of changes made
3. Why the fix works

Maintain the same functionality while fixing the security issue."""

        user_prompt = f"""Vulnerability: {vulnerability_description}

Vulnerable Code:
```{language}
{vulnerable_code}
```

Provide the fixed code and explanation."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = self.chat_completion(
            messages=messages,
            temperature=0.2,  # Low temperature for consistent code generation
            max_tokens=2000,
        )

        return response.content

    def explain_to_developer(
        self,
        vulnerability: Dict[str, Any],
        developer_level: str = "intermediate",
    ) -> str:
        """
        Explain vulnerability in developer-friendly terms

        Args:
            vulnerability: Vulnerability dict with details
            developer_level: 'beginner', 'intermediate', or 'senior'

        Returns:
            Developer-friendly explanation
        """
        level_prompts = {
            "beginner": "Explain in simple terms suitable for a junior developer. Use analogies and examples.",
            "intermediate": "Provide a balanced explanation with technical details and practical examples.",
            "senior": "Give a concise, technical explanation focusing on root cause and architectural implications.",
        }

        system_prompt = f"""You are explaining a security vulnerability to a {developer_level} developer.
{level_prompts.get(developer_level, level_prompts['intermediate'])}"""

        user_prompt = f"""Explain this vulnerability:

Type: {vulnerability.get('vuln_type')}
Severity: {vulnerability.get('severity')}
Location: {vulnerability.get('file_path')}:{vulnerability.get('line_start')}

Description: {vulnerability.get('description')}
Impact: {vulnerability.get('impact')}

Make it clear and actionable."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = self.chat_completion(
            messages=messages,
            temperature=0.5,
            max_tokens=1000,
        )

        return response.content

    def _estimate_cost(self, model: str, tokens: int) -> float:
        """
        Estimate cost based on model and tokens

        Note: These are approximate rates. Check OpenRouter for current pricing.
        """
        # Approximate costs per 1M tokens (input + output averaged)
        model_costs = {
            "anthropic/claude-3.5-sonnet": 3.00,
            "anthropic/claude-3-opus": 15.00,
            "anthropic/claude-3-haiku": 0.25,
            "openai/gpt-4-turbo": 10.00,
            "openai/gpt-4": 30.00,
            "openai/gpt-3.5-turbo": 0.50,
            "meta-llama/llama-3.1-70b-instruct": 0.60,
        }

        cost_per_million = model_costs.get(model, 1.00)  # Default $1/M tokens
        return (tokens / 1_000_000) * cost_per_million

    def close(self):
        """Close HTTP client"""
        self.client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
