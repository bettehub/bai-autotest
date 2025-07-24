from typing import Dict, Any, List
import json

from .base import TestGenerator, GeneratedTest
from ..parsers.base import TestScenario, TestStep, StepType


class CypressGenerator(TestGenerator):
    """Generate Cypress tests for Next.js applications."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = config.get('base_url', 'http://localhost:3000') if config else 'http://localhost:3000'
        self.viewport = config.get('viewport', {'width': 1280, 'height': 720}) if config else {'width': 1280, 'height': 720}
    
    def get_language(self) -> str:
        """Get the programming language for generated tests."""
        return "javascript"
    
    def generate(self, scenario: TestScenario) -> GeneratedTest:
        """Generate Cypress test from scenario."""
        # Generate test code
        test_code = self._generate_test_function(scenario)
        
        return GeneratedTest(
            name=f"{scenario.name}.cy.js",
            code=test_code,
            language="javascript",
            framework="cypress",
            imports=[],  # Cypress doesn't need explicit imports
            metadata={
                'scenario_name': scenario.name,
                'base_url': self.base_url,
                'viewport': self.viewport
            }
        )
    
    def generate_step(self, step: TestStep) -> str:
        """Generate Cypress code for a step."""
        if step.step_type == StepType.USER_ACTION:
            return self._generate_user_action(step)
        elif step.step_type == StepType.API_CALL:
            return self._generate_api_call(step)
        elif step.step_type == StepType.ASSERTION:
            return self._generate_assertion(step)
        elif step.step_type == StepType.NAVIGATION:
            return self._generate_navigation(step)
        elif step.step_type == StepType.WAIT:
            return self._generate_wait(step)
        else:
            return f"    // {step.description}"
    
    def _generate_test_function(self, scenario: TestScenario) -> str:
        """Generate the main test function."""
        lines = [
            f"describe('{scenario.name}', () => {{",
            f"  beforeEach(() => {{",
            f"    cy.viewport({self.viewport['width']}, {self.viewport['height']});",
            f"    cy.visit('{self.base_url}');",
            f"  }});",
            "",
            f"  it('{scenario.description}', () => {{",
        ]
        
        # Generate code for each step
        for i, step in enumerate(scenario.steps):
            lines.append(f"    // Step {i+1}: {step.description}")
            step_code = self.generate_step(step)
            if step_code:
                lines.append(step_code)
            lines.append("")
        
        lines.extend([
            "  });",
            "});"
        ])
        
        return "\n".join(lines)
    
    def _generate_user_action(self, step: TestStep) -> str:
        """Generate code for user actions."""
        action = step.action.lower()
        
        if 'click' in action:
            selector = self._extract_selector(step.action)
            if '로그인' in step.action:
                return "    cy.contains('로그인').click();"
            elif 'button' in action:
                text = self._extract_button_text(step.action)
                return f"    cy.contains('button', '{text}').click();"
            else:
                return f"    cy.get('{selector}').click();"
        
        elif 'type' in action or 'enter' in action or '입력' in action:
            if '이메일' in step.action:
                text = step.data.get('text', 'user@example.com')
                return f"    cy.get('input[type="email"]').type('{text}');"
            elif '비밀번호' in step.action or 'password' in action:
                text = step.data.get('text', 'password123')
                return f"    cy.get('input[type="password"]').type('{text}');"
            else:
                selector = self._extract_selector(step.action)
                text = step.data.get('text', '')
                return f"    cy.get('{selector}').type('{text}');"
        
        elif 'select' in action:
            selector = self._extract_selector(step.action)
            value = step.data.get('value', '')
            return f"    cy.get('{selector}').select('{value}');"
        
        elif '접속' in action:
            return f"    // 사용자가 페이지에 접속"
        
        else:
            return f"    // TODO: Implement {step.action}"
    
    def _generate_api_call(self, step: TestStep) -> str:
        """Generate code for API calls."""
        method = step.data.get('method', 'GET')
        endpoint = step.data.get('endpoint', '/')
        
        lines = [
            f"    // API Call: {method} {endpoint}",
            f"    cy.intercept('{method}', '{endpoint}', {{ fixture: 'auth-success.json' }}).as('apiCall');",
            f"    cy.wait('@apiCall');"
        ]
        
        return "\n".join(lines)
    
    def _generate_assertion(self, step: TestStep) -> str:
        """Generate assertion code."""
        if 'JWT' in step.action and '토큰' in step.action:
            return "    cy.getCookie('access_token').should('exist');"
        elif '에러' in step.action:
            return "    cy.contains('에러').should('be.visible');"
        elif step.expected:
            return f"    cy.contains('{step.expected}').should('be.visible');"
        else:
            return f"    // Assertion: {step.description}"
    
    def _generate_navigation(self, step: TestStep) -> str:
        """Generate navigation code."""
        if '메인' in step.action and '페이지' in step.action:
            return "    cy.url().should('include', '/dashboard');"
        elif '리다이렉트' in step.action:
            url = step.data.get('url', '/dashboard')
            return f"    cy.url().should('include', '{url}');"
        else:
            url = step.data.get('url', '/')
            return f"    cy.visit('{url}');"
    
    def _generate_wait(self, step: TestStep) -> str:
        """Generate wait code."""
        timeout = step.data.get('timeout', 1000)
        return f"    cy.wait({timeout});"
    
    def _extract_selector(self, action: str) -> str:
        """Extract selector from action description."""
        # Simple extraction logic
        if '"' in action:
            import re
            match = re.search(r'"([^"]+)"', action)
            if match:
                return match.group(1)
        
        # Default selectors for common elements
        action_lower = action.lower()
        if 'login' in action_lower or '로그인' in action:
            return 'button[type="submit"]'
        elif 'email' in action_lower or '이메일' in action:
            return 'input[type="email"]'
        elif 'password' in action_lower or '비밀번호' in action:
            return 'input[type="password"]'
        
        return 'body'
    
    def _extract_button_text(self, action: str) -> str:
        """Extract button text from action."""
        if '"' in action:
            import re
            match = re.search(r'"([^"]+)"', action)
            if match:
                return match.group(1)
        
        if '로그인' in action:
            return '로그인'
        elif '제출' in action or 'submit' in action.lower():
            return '제출'
        
        return 'Click'