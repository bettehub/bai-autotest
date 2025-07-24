from typing import Dict, Any, List
import json

from .base import TestGenerator, GeneratedTest
from ..parsers.base import TestScenario, TestStep, StepType


class JestRTLGenerator(TestGenerator):
    """Generate Jest + React Testing Library tests for Next.js components."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.component_name = config.get('component_name', 'App') if config else 'App'
        self.use_typescript = config.get('use_typescript', True) if config else True
    
    def get_language(self) -> str:
        """Get the programming language for generated tests."""
        return "typescript" if self.use_typescript else "javascript"
    
    def generate(self, scenario: TestScenario) -> GeneratedTest:
        """Generate Jest + RTL test from scenario."""
        # Generate imports
        imports = self._generate_imports()
        
        # Generate test code
        test_code = self._generate_test_function(scenario)
        
        # Generate setup code if needed
        setup_code = self._generate_setup(scenario)
        
        file_extension = ".test.tsx" if self.use_typescript else ".test.jsx"
        
        return GeneratedTest(
            name=f"{scenario.name}{file_extension}",
            code=test_code,
            language=self.get_language(),
            framework="jest-rtl",
            imports=imports,
            setup_code=setup_code,
            metadata={
                'scenario_name': scenario.name,
                'component_name': self.component_name,
                'use_typescript': self.use_typescript
            }
        )
    
    def generate_step(self, step: TestStep) -> str:
        """Generate Jest/RTL code for a step."""
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
            return f"  // {step.description}"
    
    def _generate_imports(self) -> List[str]:
        """Generate import statements."""
        imports = [
            "import React from 'react';",
            "import { render, screen, fireEvent, waitFor } from '@testing-library/react';",
            "import userEvent from '@testing-library/user-event';",
            "import { rest } from 'msw';",
            "import { setupServer } from 'msw/node';",
            "import '@testing-library/jest-dom';",
            f"import {{ {self.component_name} }} from './{self.component_name}';",
        ]
        
        if self.use_typescript:
            imports.append("import type { User } from '@testing-library/user-event/dist/types/setup/setup';")
        
        return imports
    
    def _generate_setup(self, scenario: TestScenario) -> str:
        """Generate setup code."""
        # Check if there are API calls in the scenario
        api_calls = scenario.get_api_calls()
        
        if api_calls:
            return """// Mock server setup
const server = setupServer(
  rest.post('/api/v1/users/login', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'mock-jwt-token',
        user: { id: '1', email: 'user@example.com' }
      })
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());"""
        
        return ""
    
    def _generate_test_function(self, scenario: TestScenario) -> str:
        """Generate the main test function."""
        lines = [
            f"describe('{scenario.name}', () => {{",
            f"  let user: User;",
            "",
            "  beforeEach(() => {",
            "    user = userEvent.setup();",
            "  });",
            "",
            f"  test('{scenario.description}', async () => {{",
            f"    render(<{self.component_name} />);",
            ""
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
        
        if 'click' in action or '클릭' in action:
            if '로그인' in step.action:
                return "    await user.click(screen.getByRole('button', { name: /로그인/i }));"
            elif 'button' in action:
                text = self._extract_button_text(step.action)
                return f"    await user.click(screen.getByRole('button', {{ name: /{text}/i }}));"
            else:
                return "    // Click action - specify the element"
        
        elif 'type' in action or 'enter' in action or '입력' in action:
            if '이메일' in step.action:
                text = step.data.get('text', 'user@example.com')
                return f"    await user.type(screen.getByLabelText(/이메일/i), '{text}');"
            elif '비밀번호' in step.action or 'password' in action:
                text = step.data.get('text', 'password123')
                return f"    await user.type(screen.getByLabelText(/비밀번호/i), '{text}');"
            else:
                return "    // Type action - specify the input"
        
        elif '접속' in action:
            return "    // User accesses the page (handled by render)"
        
        else:
            return f"    // TODO: Implement {step.action}"
    
    def _generate_api_call(self, step: TestStep) -> str:
        """Generate code for API calls."""
        method = step.data.get('method', 'GET')
        endpoint = step.data.get('endpoint', '/')
        
        return f"    // API Call: {method} {endpoint} (handled by MSW mock)"
    
    def _generate_assertion(self, step: TestStep) -> str:
        """Generate assertion code."""
        if 'JWT' in step.action and '토큰' in step.action:
            return """    await waitFor(() => {
      expect(document.cookie).toContain('access_token');
    });"""
        elif '에러' in step.action:
            return """    await waitFor(() => {
      expect(screen.getByText(/에러/i)).toBeInTheDocument();
    });"""
        elif '메인' in step.action and '페이지' in step.action:
            return """    await waitFor(() => {
      expect(window.location.pathname).toBe('/dashboard');
    });"""
        elif step.expected:
            return f"""    await waitFor(() => {{
      expect(screen.getByText(/{step.expected}/i)).toBeInTheDocument();
    }});"""
        else:
            return f"    // Assertion: {step.description}"
    
    def _generate_navigation(self, step: TestStep) -> str:
        """Generate navigation code."""
        if '메인' in step.action and '페이지' in step.action:
            return """    // Navigation to main page
    await waitFor(() => {
      expect(window.location.pathname).toBe('/dashboard');
    });"""
        else:
            return f"    // Navigation: {step.description}"
    
    def _generate_wait(self, step: TestStep) -> str:
        """Generate wait code."""
        timeout = step.data.get('timeout', 1000)
        return f"""    await waitFor(() => {{
      // Wait for condition
    }}, {{ timeout: {timeout} }});"""
    
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