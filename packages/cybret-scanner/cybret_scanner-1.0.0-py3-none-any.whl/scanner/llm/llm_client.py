"""
LLM Client Abstraction Layer

Supports multiple LLM providers with a unified interface:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Local models (Ollama)
- Mock (for testing)
"""

import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    MOCK = "mock"


@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 2000
    timeout: int = 60


@dataclass
class LLMResponse:
    """Standardized LLM response"""
    content: str
    model: str
    provider: str
    tokens_used: int
    finish_reason: str
    raw_response: Optional[Dict] = None


class BaseLLMClient(ABC):
    """Base class for LLM clients"""

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Generate completion"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = None
        self._initialize()

    def _initialize(self):
        """Initialize OpenAI client"""
        try:
            import openai
            api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not provided")

            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Generate completion using OpenAI"""

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            timeout=self.config.timeout
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            provider="openai",
            tokens_used=response.usage.total_tokens,
            finish_reason=response.choices[0].finish_reason,
            raw_response=response.model_dump()
        )

    def is_available(self) -> bool:
        """Check if OpenAI is available"""
        try:
            return self.client is not None
        except:
            return False


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = None
        self._initialize()

    def _initialize(self):
        """Initialize Anthropic client"""
        try:
            import anthropic
            api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key not provided")

            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Generate completion using Claude"""

        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=max_tokens or self.config.max_tokens,
            temperature=temperature or self.config.temperature,
            system=system or "",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            provider="anthropic",
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason,
            raw_response=None  # Anthropic response not JSON serializable
        )

    def is_available(self) -> bool:
        """Check if Anthropic is available"""
        try:
            return self.client is not None
        except:
            return False


class OpenRouterClient(BaseLLMClient):
    """OpenRouter API client - provides access to multiple models"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = None
        self._initialize()

    def _initialize(self):
        """Initialize OpenRouter client"""
        try:
            import openai
            api_key = self.config.api_key or os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError("OpenRouter API key not provided")

            # OpenRouter uses OpenAI-compatible API
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Generate completion using OpenRouter with smart fallback"""

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # Define fallback chain for next-gen models
        fallback_models = {
            "anthropic/claude-opus-4.5": "anthropic/claude-3.5-sonnet:beta",
            "openai/gpt-5.2": "openai/gpt-4o",
            "google/gemini-3-pro": "google/gemini-pro-2.0"
        }

        model_to_use = self.config.model
        tried_models = []

        while True:
            try:
                response = self.client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    temperature=temperature or self.config.temperature,
                    max_tokens=max_tokens or self.config.max_tokens,
                    timeout=self.config.timeout
                )

                # Success! Check if we used fallback
                if model_to_use != self.config.model:
                    print(f"[OpenRouter] Model {self.config.model} not available, used {model_to_use}")

                return LLMResponse(
                    content=response.choices[0].message.content,
                    model=response.model,
                    provider="openrouter",
                    tokens_used=response.usage.total_tokens if response.usage else 0,
                    finish_reason=response.choices[0].finish_reason,
                    raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
                )

            except Exception as e:
                error_msg = str(e).lower()
                tried_models.append(model_to_use)

                # Check if model not found
                if "not a valid model" in error_msg or "model not found" in error_msg or "400" in error_msg:
                    # Try fallback if available
                    if model_to_use in fallback_models and fallback_models[model_to_use] not in tried_models:
                        model_to_use = fallback_models[model_to_use]
                        print(f"[OpenRouter] Next-gen model not yet available, falling back to {model_to_use}")
                        continue
                    else:
                        # No fallback available, re-raise
                        raise Exception(f"Model {self.config.model} not available and no fallback found. Tried: {tried_models}")
                else:
                    # Other error, re-raise
                    raise

    def is_available(self) -> bool:
        """Check if OpenRouter is available"""
        try:
            return self.client is not None
        except:
            return False


class OllamaClient(BaseLLMClient):
    """Ollama local LLM client"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Generate completion using Ollama"""

        import requests

        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.config.model,
                "prompt": full_prompt,
                "temperature": temperature or self.config.temperature,
                "stream": False
            },
            timeout=self.config.timeout
        )

        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            content=data["response"],
            model=self.config.model,
            provider="ollama",
            tokens_used=0,  # Ollama doesn't return token count
            finish_reason="stop",
            raw_response=data
        )

    def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.responses = {}
        self.call_count = 0

    def set_response(self, key: str, response: str):
        """Set mock response for a key"""
        self.responses[key] = response

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Return mock response"""

        self.call_count += 1

        # Try to find matching response
        for key, response in self.responses.items():
            if key.lower() in prompt.lower():
                return LLMResponse(
                    content=response,
                    model="mock",
                    provider="mock",
                    tokens_used=100,
                    finish_reason="stop"
                )

        # Default response
        return LLMResponse(
            content=self._generate_default_response(prompt, system),
            model="mock",
            provider="mock",
            tokens_used=100,
            finish_reason="stop"
        )

    def _generate_default_response(self, prompt: str, system: Optional[str]) -> str:
        """Generate a reasonable default response"""

        if "vulnerability" in prompt.lower():
            return """
# Vulnerability Analysis

## Vulnerability Explanation
This is a Broken Object Level Authorization (BOLA/IDOR) vulnerability where users
can access resources they don't own by manipulating ID parameters.

## Business Logic Impact
- Users can access other users' data
- Privacy violation
- Potential GDPR breach
- Business impact: HIGH

## Attack Scenario
1. User A logs in
2. User A accesses /api/Resource/1 (their resource)
3. User A changes to /api/Resource/2 (User B's resource)
4. System returns User B's resource without authorization check

## Root Cause Analysis
The handler retrieves resources using user-supplied ID without verifying ownership.

## Exploitability Assessment
- Difficulty: 1/10 (trivial)
- Access required: Authenticated user
- Tools: Browser or curl

## Business Context
This affects the core business process and violates data privacy principles.
"""

        elif "business logic" in prompt.lower():
            return """
# Business Logic Analysis

## Business Process Identification
Process: Resource Management
Entities: User, Resource
Rules: Users should only access their own resources

## Authorization Model
Type: Ownership-based access control
Owner field: userId
Required check: resource.userId === req.user.id

## Data Flow
Request → Auth → Get Resource → [MISSING: Ownership check] → Return

## Business Rule Violations
- Ownership rule not enforced
- Privacy rule not enforced

## Expected vs Actual Behavior
Expected: Verify ownership before returning resource
Actual: Returns resource without ownership check
"""

        elif "fix" in prompt.lower() or "generate" in prompt.lower():
            return """
# Generated Fix

## Fixed Code
```javascript
app.get('/api/Resource/:id', async (req, res) => {
  const resourceId = req.params.id
  const resource = await Resource.findOne({ id: resourceId })

  if (!resource) {
    return res.status(404).json({ error: 'Resource not found' })
  }

  // Ownership verification
  if (resource.userId !== req.user.id) {
    console.warn(`Unauthorized access attempt: User ${req.user.id} tried to access resource ${resourceId}`)
    return res.status(403).json({ error: 'Permission denied' })
  }

  res.json(resource)
})
```

## Explanation
Added ownership verification after resource retrieval to prevent unauthorized access.

## Changes
- Added resource existence check (404)
- Added ownership verification (403)
- Added security logging

## Test Cases
1. Authorized access (own resource) - Pass
2. Unauthorized access (other's resource) - Block with 403
3. Non-existent resource - Return 404
"""

        elif "validate" in prompt.lower():
            return """
# Fix Validation

## Vulnerability Coverage
Score: 100%
Assessment: Fix fully prevents the vulnerability

## New Issues Introduced
None detected

## Business Logic Preservation
Score: 100%
Assessment: Functionality maintained

## Code Quality
Score: 95%
Assessment: Well-structured, includes logging

## Completeness
Score: 100%
Assessment: All necessary changes included

## Recommendation
APPROVE - Fix is secure and correct
"""

        return "Mock LLM response"

    def is_available(self) -> bool:
        """Mock is always available"""
        return True


class LLMClientFactory:
    """Factory for creating LLM clients"""

    @staticmethod
    def create(
        provider: LLMProvider,
        model: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> BaseLLMClient:
        """Create LLM client for specified provider"""

        config = LLMConfig(
            provider=provider,
            model=model,
            api_key=api_key,
            **kwargs
        )

        if provider == LLMProvider.OPENAI:
            return OpenAIClient(config)
        elif provider == LLMProvider.ANTHROPIC:
            return AnthropicClient(config)
        elif provider == LLMProvider.OPENROUTER:
            return OpenRouterClient(config)
        elif provider == LLMProvider.OLLAMA:
            return OllamaClient(config)
        elif provider == LLMProvider.MOCK:
            return MockLLMClient(config)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def create_from_env() -> BaseLLMClient:
        """Create LLM client from environment variables"""

        # Check for OpenAI
        if os.getenv("OPENAI_API_KEY"):
            return LLMClientFactory.create(
                LLMProvider.OPENAI,
                model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
            )

        # Check for Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            return LLMClientFactory.create(
                LLMProvider.ANTHROPIC,
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
            )

        # Check for OpenRouter
        if os.getenv("OPENROUTER_API_KEY"):
            return LLMClientFactory.create(
                LLMProvider.OPENROUTER,
                model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet:beta")
            )

        # Check for Ollama
        try:
            client = LLMClientFactory.create(
                LLMProvider.OLLAMA,
                model=os.getenv("OLLAMA_MODEL", "deepseek-coder:33b")
            )
            if client.is_available():
                return client
        except:
            pass

        # Fallback to mock for testing
        print("Warning: No LLM provider configured. Using mock client.")
        print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY to use real LLMs.")
        return LLMClientFactory.create(LLMProvider.MOCK, model="mock")


# Convenience function
def get_llm_client() -> BaseLLMClient:
    """Get LLM client (auto-detects from environment)"""
    return LLMClientFactory.create_from_env()
