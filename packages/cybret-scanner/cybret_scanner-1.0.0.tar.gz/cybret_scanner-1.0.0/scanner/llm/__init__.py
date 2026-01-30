"""
LLM-Enhanced Vulnerability Analysis and Autonomous Remediation

This module provides LLM-powered agents for:
- Context-aware vulnerability analysis
- Business logic understanding
- Automated fix generation
- Security validation
- Autonomous remediation
"""

from .llm_client import (
    get_llm_client,
    LLMClientFactory,
    LLMProvider,
    LLMConfig,
    LLMResponse
)

from .remediation import (
    RemediationEngine,
    analyze_scan_results
)

__all__ = [
    'get_llm_client',
    'LLMClientFactory',
    'LLMProvider',
    'LLMConfig',
    'LLMResponse',
    'RemediationEngine',
    'analyze_scan_results'
]
