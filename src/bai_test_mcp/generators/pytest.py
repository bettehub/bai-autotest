from typing import Dict, Any, List
import json

from .base import TestGenerator, GeneratedTest
from ..parsers.base import TestScenario, TestStep, StepType


class PytestGenerator(TestGenerator):
    """Generate Pytest tests from test scenarios."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = config.get('base_url', 'http://localhost:8000') if config else 'http://localhost:8000'
        self.use_async = config.get('use_async', False) if config else False
    
    def generate(self, scenario: TestScenario) -> GeneratedTest:
        """Generate Pytest test from scenario."""
        # Generate imports
        imports = self._generate_imports()
        
        # Generate test function
        test_code = self._generate_test_function(scenario)
        
        # Generate fixtures if needed
        setup_code = self._generate_fixtures(scenario)
        
        return GeneratedTest(
            name=f"test_{scenario.name}",
            code=test_code,
            language="python",
            framework="pytest",
            imports=imports,
            setup_code=setup_code,
            metadata={
                'scenario_name': scenario.name,
                'base_url': self.base_url,
                'use_async': self.use_async
            }
        )
    
    def generate_step(self, step: TestStep) -> str:
        """Generate Pytest code for a step."""
        if step.step_type == StepType.API_CALL:
            return self._generate_api_call(step)
        elif step.step_type == StepType.ASSERTION:
            return self._generate_assertion(step)
        elif step.step_type == StepType.USER_ACTION:
            return f"    # User action: {step.action}"
        else:
            return f"    # {step.description}"
    
    def _generate_imports(self) -> List[str]:
        """Generate import statements."""
        imports = [
            "import pytest",
            "import requests",
            "import json",
            "from typing import Dict, Any"
        ]
        
        if self.use_async:
            imports.extend([
                "import asyncio",
                "import aiohttp"
            ])
        
        return imports
    
    def _generate_test_function(self, scenario: TestScenario) -> str:
        """Generate the main test function."""
        async_prefix = "async " if self.use_async else ""
        await_prefix = "await " if self.use_async else ""
        
        lines = [
            f"{async_prefix}def test_{scenario.name}(client):",
            f'    """Test: {scenario.description}"""',
            ""
        ]
        
        # Track response variables
        response_count = 0
        
        # Generate code for each step
        for i, step in enumerate(scenario.steps):
            lines.append(f"    # Step {i+1}: {step.description}")
            
            if step.step_type == StepType.API_CALL:
                response_count += 1
                step.data['response_var'] = f"response_{response_count}"
            
            step_code = self.generate_step(step)
            if step_code:
                lines.append(step_code)
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_fixtures(self, scenario: TestScenario) -> str:
        """Generate pytest fixtures."""
        if self.use_async:
            return self._generate_async_fixtures()
        else:
            return self._generate_sync_fixtures()
    
    def _generate_sync_fixtures(self) -> str:
        """Generate synchronous fixtures."""
        return f"""@pytest.fixture
def client():
    """HTTP client for API testing."""
    session = requests.Session()
    session.headers.update({{
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }})
    return session


@pytest.fixture
def base_url():
    """Base URL for API endpoints."""
    return "{self.base_url}""""
    
    def _generate_async_fixtures(self) -> str:
        """Generate asynchronous fixtures."""
        return f"""@pytest.fixture
async def client():
    """Async HTTP client for API testing."""
    async with aiohttp.ClientSession() as session:
        session.headers.update({{
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }})
        yield session


@pytest.fixture
def base_url():
    """Base URL for API endpoints."""
    return "{self.base_url}""""
    
    def _generate_api_call(self, step: TestStep) -> str:
        """Generate code for API calls."""
        method = step.data.get('method', 'GET').lower()
        endpoint = step.data.get('endpoint', '/')
        response_var = step.data.get('response_var', 'response')
        
        if self.use_async:
            return self._generate_async_api_call(method, endpoint, response_var, step.data)
        else:
            return self._generate_sync_api_call(method, endpoint, response_var, step.data)
    
    def _generate_sync_api_call(self, method: str, endpoint: str, response_var: str, data: Dict) -> str:
        """Generate synchronous API call."""
        lines = [f"    {response_var} = client.{method}(f'{{base_url}}{endpoint}'"]
        
        if data.get('payload'):
            lines[0] += f", json={data['payload']}"
        
        lines[0] += ")"
        lines.append(f"    assert {response_var}.status_code == 200")
        
        return "\n".join(lines)
    
    def _generate_async_api_call(self, method: str, endpoint: str, response_var: str, data: Dict) -> str:
        """Generate asynchronous API call."""
        lines = [f"    async with client.{method}(f'{{base_url}}{endpoint}'"]
        
        if data.get('payload'):
            lines[0] += f", json={data['payload']}"
        
        lines[0] += f") as {response_var}:"
        lines.append(f"        assert {response_var}.status == 200")
        lines.append(f"        data = await {response_var}.json()")
        
        return "\n".join(lines)
    
    def _generate_assertion(self, step: TestStep) -> str:
        """Generate assertion code."""
        if step.expected:
            return f"    assert result == {repr(step.expected)}"
        else:
            return f"    # Assertion: {step.description}"