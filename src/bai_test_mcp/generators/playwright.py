from typing import Dict, Any, List
import json

from .base import TestGenerator, GeneratedTest
from ..parsers.base import TestScenario, TestStep, StepType


class PlaywrightGenerator(TestGenerator):
    """Generate Playwright tests from test scenarios."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.browser = config.get('browser', 'chromium') if config else 'chromium'
        self.base_url = config.get('base_url', 'http://localhost:3000') if config else 'http://localhost:3000'
        self.headless = config.get('headless', True) if config else True
    
    def generate(self, scenario: TestScenario) -> GeneratedTest:
        """Generate Playwright test from scenario."""
        # Generate imports
        imports = self._generate_imports()
        
        # Generate test function
        test_code = self._generate_test_function(scenario)
        
        # Generate setup/teardown if needed
        setup_code = self._generate_setup(scenario)
        
        return GeneratedTest(
            name=f"test_{scenario.name}",
            code=test_code,
            language="python",
            framework="playwright",
            imports=imports,
            setup_code=setup_code,
            metadata={
                'scenario_name': scenario.name,
                'browser': self.browser,
                'base_url': self.base_url
            }
        )
    
    def generate_step(self, step: TestStep) -> str:
        """Generate Playwright code for a step."""
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
            return f"    # {step.description}"
    
    def _generate_imports(self) -> List[str]:
        """Generate import statements."""
        return [
            "import pytest",
            "from playwright.sync_api import Page, expect",
            "import json",
            "from typing import Dict, Any"
        ]
    
    def _generate_test_function(self, scenario: TestScenario) -> str:
        """Generate the main test function."""
        lines = [
            f"def test_{scenario.name}(page: Page):",
            f'    """Test: {scenario.description}"""',
            f"    # Navigate to base URL",
            f"    page.goto('{self.base_url}')",
            ""
        ]
        
        # Generate code for each step
        for i, step in enumerate(scenario.steps):
            lines.append(f"    # Step {i+1}: {step.description}")
            step_code = self.generate_step(step)
            if step_code:
                lines.append(step_code)
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_setup(self, scenario: TestScenario) -> str:
        """Generate setup code if needed."""
        return f"""@pytest.fixture(scope="function")
def browser_context_args(browser_context_args):
    return {{
        **browser_context_args,
        "base_url": "{self.base_url}",
        "ignore_https_errors": True,
    }}"""
    
    def _generate_user_action(self, step: TestStep) -> str:
        """Generate code for user actions."""
        action = step.action.lower()
        
        if 'click' in action:
            # Extract selector from action
            selector = self._extract_selector(step.action)
            return f"    page.click('{selector}')"
        
        elif 'type' in action or 'enter' in action:
            selector = self._extract_selector(step.action)
            text = step.data.get('text', '')
            return f"    page.fill('{selector}', '{text}')"
        
        elif 'select' in action:
            selector = self._extract_selector(step.action)
            value = step.data.get('value', '')
            return f"    page.select_option('{selector}', '{value}')"
        
        else:
            return f"    # TODO: Implement {step.action}"
    
    def _generate_api_call(self, step: TestStep) -> str:
        """Generate code for API calls."""
        method = step.data.get('method', 'GET')
        endpoint = step.data.get('endpoint', '/')
        
        lines = [
            f"    # API Call: {method} {endpoint}",
            f"    response = page.request.{method.lower()}('{endpoint}'"  
        ]
        
        if step.data.get('payload'):
            lines[1] += f", data={step.data['payload']}"
        
        lines[1] += ")"
        lines.append("    assert response.ok")
        
        return "\n".join(lines)
    
    def _generate_assertion(self, step: TestStep) -> str:
        """Generate assertion code."""
        if step.expected:
            return f"    expect(page).to_have_title('{step.expected}')"
        else:
            return f"    # Assertion: {step.description}"
    
    def _generate_navigation(self, step: TestStep) -> str:
        """Generate navigation code."""
        url = step.data.get('url', '/')
        return f"    page.goto('{url}')"
    
    def _generate_wait(self, step: TestStep) -> str:
        """Generate wait code."""
        timeout = step.data.get('timeout', 1000)
        return f"    page.wait_for_timeout({timeout})"
    
    def _extract_selector(self, action: str) -> str:
        """Extract selector from action description."""
        # Simple extraction logic - can be enhanced
        if '"' in action:
            import re
            match = re.search(r'"([^"]+)"', action)
            if match:
                return match.group(1)
        
        # Default selectors for common elements
        action_lower = action.lower()
        if 'login' in action_lower:
            return 'button:has-text("Login")'
        elif 'submit' in action_lower:
            return 'button[type="submit"]'
        elif 'email' in action_lower:
            return 'input[type="email"]'
        elif 'password' in action_lower:
            return 'input[type="password"]'
        
        return 'body'  # Fallback