"""
LLM Agent System for Context-Aware Vulnerability Analysis

Multi-agent architecture where specialized LLMs handle different aspects
of vulnerability understanding and remediation.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class AgentRole(Enum):
    """Specialized agent roles"""
    VULNERABILITY_ANALYST = "vulnerability_analyst"
    BUSINESS_LOGIC_EXPERT = "business_logic_expert"
    CODE_REVIEWER = "code_reviewer"
    FIX_GENERATOR = "fix_generator"
    TEST_ENGINEER = "test_engineer"
    SECURITY_VALIDATOR = "security_validator"


@dataclass
class CodeContext:
    """Rich context for LLM analysis"""
    # Target code
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str

    # Surrounding context
    function_definition: str
    class_definition: Optional[str]
    imports: List[str]

    # Route context
    route_method: str
    route_path: str
    middleware_chain: List[str]

    # Handler resolution
    handler_name: str
    handler_file: str
    handler_code: str

    # Database models
    models_accessed: List[str]
    model_schemas: Dict[str, Any]

    # Business logic
    related_routes: List[str]
    authentication_flow: str
    authorization_rules: str

    # Call graph
    caller_functions: List[str]
    callee_functions: List[str]
    data_flow: List[str]


@dataclass
class VulnerabilityContext:
    """Complete vulnerability context for LLM"""
    vulnerability_type: str
    confidence: float
    evidence: List[str]

    code_context: CodeContext

    # Static analysis results
    ownership_checks: List[Dict]
    auth_checks: List[Dict]
    db_queries: List[Dict]

    # Business logic
    resource_type: str
    user_roles: List[str]
    access_patterns: List[str]


class VulnerabilityAnalystAgent:
    """
    Agent that deeply analyzes vulnerabilities with business context

    Capabilities:
    - Understands business logic implications
    - Identifies attack vectors
    - Assesses real-world exploitability
    - Explains vulnerability in business terms
    """

    def __init__(self, llm_client):
        self.llm = llm_client
        self.role = AgentRole.VULNERABILITY_ANALYST

    def analyze_vulnerability(self, vuln_context: VulnerabilityContext) -> Dict[str, Any]:
        """
        Deep vulnerability analysis with business logic understanding
        """

        prompt = self._build_analysis_prompt(vuln_context)

        response = self.llm.complete(
            prompt=prompt,
            system="""You are an expert security analyst specializing in business logic
            vulnerabilities. Analyze code with deep understanding of:
            - Business logic flaws
            - Authorization bypass patterns
            - Data exposure risks
            - Real-world attack scenarios
            - Business impact assessment""",
            temperature=0.3,  # Low temperature for consistency
            max_tokens=2000
        )

        return self._parse_analysis(response.content)

    def _build_analysis_prompt(self, context: VulnerabilityContext) -> str:
        """Build comprehensive analysis prompt"""

        return f"""
# Vulnerability Analysis Request

## Detected Vulnerability
Type: {context.vulnerability_type}
Confidence: {context.confidence * 100:.1f}%
Evidence: {', '.join(context.evidence)}

## Code Context
Route: {context.code_context.route_method} {context.code_context.route_path}
Handler: {context.code_context.handler_name}
File: {context.code_context.handler_file}:{context.code_context.line_start}

### Handler Code
```javascript
{context.code_context.handler_code}
```

### Middleware Chain
{chr(10).join(f"- {mw}" for mw in context.code_context.middleware_chain)}

## Database Access
Models: {', '.join(context.code_context.models_accessed)}

### Model Schemas
{self._format_schemas(context.code_context.model_schemas)}

## Security Checks Found
Ownership checks: {len(context.ownership_checks)}
Auth checks: {len(context.auth_checks)}

## Business Logic Context
Resource type: {context.resource_type}
User roles: {', '.join(context.user_roles)}
Access patterns: {', '.join(context.access_patterns)}

## Related Routes
{chr(10).join(f"- {route}" for route in context.code_context.related_routes)}

---

# Analysis Required

Please provide a comprehensive analysis covering:

1. **Vulnerability Explanation**
   - What is the vulnerability?
   - Why does it exist?
   - What security principle is violated?

2. **Business Logic Impact**
   - What business rules are bypassed?
   - What data can be exposed?
   - What actions can be performed unauthorized?
   - What is the business impact severity?

3. **Attack Scenario**
   - Step-by-step exploitation process
   - Example malicious requests
   - What an attacker could achieve
   - Real-world impact

4. **Root Cause Analysis**
   - Why wasn't this prevented?
   - What security check is missing?
   - What assumption was made?
   - What pattern was overlooked?

5. **Exploitability Assessment**
   - How easy to exploit? (1-10)
   - What access level required?
   - What knowledge required?
   - What tools required?

6. **Business Context**
   - What business process is affected?
   - What compliance issues? (GDPR, PCI-DSS, etc.)
   - What is the financial risk?
   - What is the reputational risk?

Provide detailed, actionable analysis focused on business logic understanding.
"""

    def _format_schemas(self, schemas: Dict[str, Any]) -> str:
        """Format model schemas for prompt"""
        result = []
        for model_name, schema in schemas.items():
            result.append(f"\n{model_name}:")
            for field, field_type in schema.items():
                result.append(f"  - {field}: {field_type}")
        return '\n'.join(result)

    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured analysis"""
        # Parse sections from response
        # This would use structured output parsing
        return {
            "explanation": self._extract_section(response, "Vulnerability Explanation"),
            "business_impact": self._extract_section(response, "Business Logic Impact"),
            "attack_scenario": self._extract_section(response, "Attack Scenario"),
            "root_cause": self._extract_section(response, "Root Cause Analysis"),
            "exploitability": self._extract_exploitability(response),
            "business_context": self._extract_section(response, "Business Context")
        }

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract section from response"""
        import re

        # Try to find section by header
        pattern = rf'#{1,3}\s*\*?\*?{re.escape(section_name)}\*?\*?.*?\n(.*?)(?=\n#{1,3}\s|\Z)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # Fallback: return whole text
        return text

    def _extract_exploitability(self, text: str) -> Dict[str, Any]:
        """Extract exploitability metrics"""
        import re

        # Try to extract difficulty score
        difficulty_match = re.search(r'difficulty:?\s*(\d+)(?:/10)?', text, re.IGNORECASE)
        difficulty = int(difficulty_match.group(1)) if difficulty_match else 5

        # Extract access level
        access_match = re.search(r'access\s+(?:level\s+)?required:?\s*([^\n]+)', text, re.IGNORECASE)
        access_required = access_match.group(1).strip() if access_match else "Unknown"

        # Extract tools
        tools_match = re.search(r'tools\s+required:?\s*([^\n]+)', text, re.IGNORECASE)
        tools = tools_match.group(1).strip() if tools_match else "Unknown"

        return {
            "difficulty": difficulty,
            "access_required": access_required,
            "tools": tools
        }


class BusinessLogicExpertAgent:
    """
    Agent that understands application business logic

    Capabilities:
    - Maps code to business processes
    - Identifies business rule violations
    - Understands authorization models
    - Detects logic flow issues
    """

    def __init__(self, llm_client):
        self.llm = llm_client
        self.role = AgentRole.BUSINESS_LOGIC_EXPERT

    def analyze_business_logic(self, code_context: CodeContext) -> Dict[str, Any]:
        """
        Analyze code for business logic understanding
        """

        prompt = f"""
# Business Logic Analysis

## Code to Analyze
Route: {code_context.route_method} {code_context.route_path}

```javascript
{code_context.handler_code}
```

## Context
Models: {', '.join(code_context.models_accessed)}
Middleware: {', '.join(code_context.middleware_chain)}
Related routes: {', '.join(code_context.related_routes)}

---

Analyze this code and provide:

1. **Business Process Identification**
   - What business process does this implement?
   - What business entities are involved?
   - What business rules should apply?

2. **Authorization Model**
   - What authorization model is used?
   - What roles/permissions are relevant?
   - What ownership rules apply?
   - What should be checked but isn't?

3. **Data Flow**
   - What data flows through this endpoint?
   - What transformations occur?
   - What validations should exist?
   - What side effects occur?

4. **Business Rule Violations**
   - What business rules could be violated?
   - What constraints are missing?
   - What edge cases aren't handled?

5. **Expected vs Actual Behavior**
   - What should this code do (business perspective)?
   - What does it actually do?
   - What's the gap?
"""

        response = self.llm.complete(
            prompt=prompt,
            system="""You are a business analyst expert at understanding application
            business logic. You map code to business processes, identify authorization
            models, and detect business rule violations.""",
            temperature=0.3,
            max_tokens=2000
        )

        return self._parse_business_logic(response.content)

    def _parse_business_logic(self, response: str) -> Dict[str, Any]:
        """Parse business logic analysis"""
        return {
            "business_process": self._extract_section(response, "Business Process"),
            "authorization_model": self._extract_section(response, "Authorization Model"),
            "data_flow": self._extract_section(response, "Data Flow"),
            "rule_violations": self._extract_list(response, "Business Rule Violations"),
            "expected_vs_actual": self._extract_section(response, "Expected vs Actual")
        }

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract section from response"""
        import re
        pattern = rf'#{1,3}\s*\*?\*?{re.escape(section_name)}\*?\*?.*?\n(.*?)(?=\n#{1,3}\s|\Z)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_list(self, text: str, section_name: str) -> List[str]:
        """Extract list items from section"""
        section = self._extract_section(text, section_name)
        import re
        items = re.findall(r'[-*]\s*(.+)', section)
        return [item.strip() for item in items]


class FixGeneratorAgent:
    """
    Agent that generates security fixes with business logic awareness

    Capabilities:
    - Generates contextually appropriate fixes
    - Preserves business logic
    - Maintains code style
    - Considers edge cases
    """

    def __init__(self, llm_client):
        self.llm = llm_client
        self.role = AgentRole.FIX_GENERATOR

    def generate_fix(
        self,
        vuln_context: VulnerabilityContext,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate fix with full context awareness
        """

        prompt = f"""
# Fix Generation Request

## Vulnerability
Type: {vuln_context.vulnerability_type}
Location: {vuln_context.code_context.handler_file}:{vuln_context.code_context.line_start}

## Current Code
```javascript
{vuln_context.code_context.handler_code}
```

## Vulnerability Analysis
{analysis['explanation']}

## Business Logic
{analysis['business_context']}

## Root Cause
{analysis['root_cause']}

---

Generate a secure fix that:

1. **Addresses the Vulnerability**
   - Implements proper security checks
   - Follows security best practices
   - Prevents the identified attack

2. **Preserves Business Logic**
   - Maintains intended functionality
   - Keeps business rules intact
   - Doesn't break existing features

3. **Handles Edge Cases**
   - Considers all access patterns
   - Handles error conditions
   - Validates all inputs

4. **Maintains Code Quality**
   - Matches existing code style
   - Uses established patterns
   - Includes helpful comments

Provide:
1. The complete fixed code
2. Explanation of changes
3. Line-by-line diff
4. Test cases to verify fix
5. Potential side effects
"""

        response = self.llm.complete(
            prompt=prompt,
            system="""You are an expert security engineer who writes secure,
            production-ready code. You fix vulnerabilities while preserving business
            logic and maintaining code quality.""",
            temperature=0.2,  # Very low for code generation
            max_tokens=3000
        )

        return self._parse_fix(response.content)

    def _parse_fix(self, response: str) -> Dict[str, Any]:
        """Parse generated fix"""
        import re

        # Extract code blocks
        code_blocks = re.findall(r'```(?:javascript|typescript|js|ts)?\n(.*?)```', response, re.DOTALL)
        fixed_code = code_blocks[0] if code_blocks else ""

        return {
            "fixed_code": fixed_code,
            "explanation": self._extract_section(response, "Explanation"),
            "diff": self._extract_section(response, "Changes") or self._extract_section(response, "Diff"),
            "test_cases": self._extract_list(response, "Test Cases"),
            "side_effects": self._extract_list(response, "Side Effects")
        }

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract section from response"""
        import re
        pattern = rf'#{1,3}\s*\*?\*?{re.escape(section_name)}\*?\*?.*?\n(.*?)(?=\n#{1,3}\s|\Z)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_list(self, text: str, section_name: str) -> List[str]:
        """Extract list items from section"""
        section = self._extract_section(text, section_name)
        import re
        items = re.findall(r'[-*\d+\.]\s*(.+)', section)
        return [item.strip() for item in items]


class SecurityValidatorAgent:
    """
    Agent that validates fixes for security and correctness

    Capabilities:
    - Verifies fix addresses vulnerability
    - Checks for new issues introduced
    - Validates business logic preservation
    - Assesses completeness
    """

    def __init__(self, llm_client):
        self.llm = llm_client
        self.role = AgentRole.SECURITY_VALIDATOR

    def validate_fix(
        self,
        original_code: str,
        fixed_code: str,
        vuln_context: VulnerabilityContext,
        fix_explanation: str
    ) -> Dict[str, Any]:
        """
        Validate that fix is secure and correct
        """

        prompt = f"""
# Security Fix Validation

## Original Vulnerable Code
```javascript
{original_code}
```

## Proposed Fixed Code
```javascript
{fixed_code}
```

## Vulnerability Being Fixed
{vuln_context.vulnerability_type}

## Fix Explanation
{fix_explanation}

---

Validate this fix by analyzing:

1. **Vulnerability Coverage**
   - Does it fully prevent the vulnerability?
   - Are all attack vectors blocked?
   - Are there bypass possibilities?
   - Rate coverage: 0-100%

2. **New Issues Introduced**
   - Does the fix create new vulnerabilities?
   - Are there logic errors?
   - Are there edge cases not handled?
   - List any concerns

3. **Business Logic Preservation**
   - Is intended functionality maintained?
   - Are business rules still enforced?
   - Will this break existing features?
   - Rate preservation: 0-100%

4. **Code Quality**
   - Is the code well-structured?
   - Are errors handled properly?
   - Is it maintainable?
   - Rate quality: 0-100%

5. **Completeness**
   - Are all necessary changes included?
   - Are there related places needing fixes?
   - Is error handling complete?
   - Rate completeness: 0-100%

6. **Recommendation**
   - APPROVE: Fix is secure and correct
   - APPROVE_WITH_CONCERNS: Fix works but has minor issues
   - REJECT: Fix has significant problems
   - Provide reasoning

Provide detailed validation with specific concerns and recommendations.
"""

        response = self.llm.complete(
            prompt=prompt,
            system="""You are a senior security auditor who validates security fixes.
            You are thorough, critical, and focused on ensuring fixes are both secure
            and correct.""",
            temperature=0.3,
            max_tokens=2000
        )

        return self._parse_validation(response.content)

    def _parse_validation(self, response: str) -> Dict[str, Any]:
        """Parse validation results"""
        import re

        # Extract scores
        def extract_score(name):
            pattern = rf'{name}.*?:?\s*(\d+)%?'
            match = re.search(pattern, response, re.IGNORECASE)
            return float(match.group(1)) / 100 if match else 0.5

        # Extract recommendation
        rec_match = re.search(r'recommendation:?\s*(APPROVE|REJECT|APPROVE_WITH_CONCERNS)', response, re.IGNORECASE)
        recommendation = rec_match.group(1).upper() if rec_match else "UNKNOWN"

        return {
            "coverage_score": extract_score("coverage"),
            "new_issues": self._extract_list(response, "New Issues"),
            "preservation_score": extract_score("preservation"),
            "quality_score": extract_score("quality"),
            "completeness_score": extract_score("completeness"),
            "recommendation": recommendation,
            "reasoning": self._extract_section(response, "Reasoning") or self._extract_section(response, "Recommendation"),
            "concerns": self._extract_list(response, "Concerns")
        }

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract section from response"""
        import re
        pattern = rf'#{1,3}\s*\*?\*?{re.escape(section_name)}\*?\*?.*?\n(.*?)(?=\n#{1,3}\s|\Z)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_list(self, text: str, section_name: str) -> List[str]:
        """Extract list items from section"""
        section = self._extract_section(text, section_name)
        import re
        items = re.findall(r'[-*]\s*(.+)', section)
        return [item.strip() for item in items]


class AgentOrchestrator:
    """
    Orchestrates multi-agent workflow for autonomous remediation
    """

    def __init__(self, llm_client):
        self.analyst = VulnerabilityAnalystAgent(llm_client)
        self.business_expert = BusinessLogicExpertAgent(llm_client)
        self.fix_generator = FixGeneratorAgent(llm_client)
        self.validator = SecurityValidatorAgent(llm_client)

    def autonomous_remediation(
        self,
        vuln_context: VulnerabilityContext
    ) -> Dict[str, Any]:
        """
        Complete autonomous remediation workflow
        """

        # Step 1: Deep vulnerability analysis
        print("[1/5] Analyzing vulnerability with business context...")
        analysis = self.analyst.analyze_vulnerability(vuln_context)

        # Step 2: Business logic understanding
        print("[2/5] Understanding business logic...")
        business_logic = self.business_expert.analyze_business_logic(
            vuln_context.code_context
        )

        # Merge insights
        analysis['business_logic'] = business_logic

        # Step 3: Generate fix
        print("[3/5] Generating security fix...")
        fix = self.fix_generator.generate_fix(vuln_context, analysis)

        # Step 4: Validate fix
        print("[4/5] Validating fix...")
        validation = self.validator.validate_fix(
            vuln_context.code_context.handler_code,
            fix['fixed_code'],
            vuln_context,
            fix['explanation']
        )

        # Step 5: Iterative refinement if needed
        if validation['recommendation'] == "REJECT":
            print("[5/5] Refining fix based on validation feedback...")
            # Regenerate with validation feedback
            fix = self._refine_fix(fix, validation, vuln_context, analysis)
            validation = self.validator.validate_fix(
                vuln_context.code_context.handler_code,
                fix['fixed_code'],
                vuln_context,
                fix['explanation']
            )

        return {
            "analysis": analysis,
            "business_logic": business_logic,
            "fix": fix,
            "validation": validation,
            "approved": validation['recommendation'] in ["APPROVE", "APPROVE_WITH_CONCERNS"]
        }

    def _refine_fix(
        self,
        original_fix: Dict,
        validation: Dict,
        vuln_context: VulnerabilityContext,
        analysis: Dict
    ) -> Dict[str, Any]:
        """Refine fix based on validation feedback"""

        # Add validation feedback to context
        feedback_prompt = f"""
Previous fix had issues. Please address:

Concerns: {', '.join(validation['concerns'])}
Reasoning: {validation['reasoning']}

Generate an improved fix.
"""

        # Regenerate with feedback
        return self.fix_generator.generate_fix(vuln_context, analysis)
