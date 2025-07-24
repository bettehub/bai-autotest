from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..parsers.base import TestScenario, TestStep


@dataclass
class GeneratedTest:
    """Represents a generated test."""
    name: str
    code: str
    language: str
    framework: str
    imports: List[str]
    setup_code: Optional[str] = None
    teardown_code: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def save(self, file_path: Path) -> None:
        """Save the generated test to a file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.get_full_code())
    
    def get_full_code(self) -> str:
        """Get the complete test code including imports."""
        parts = []
        
        # Add imports
        if self.imports:
            parts.extend(self.imports)
            parts.append("")  # Empty line after imports
        
        # Add setup code if present
        if self.setup_code:
            parts.append(self.setup_code)
            parts.append("")
        
        # Add main test code
        parts.append(self.code)
        
        # Add teardown code if present
        if self.teardown_code:
            parts.append("")
            parts.append(self.teardown_code)
        
        return "\n".join(parts)


class TestGenerator(ABC):
    """Abstract base class for test generators."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    def generate(self, scenario: TestScenario) -> GeneratedTest:
        """Generate test code from a test scenario.
        
        Args:
            scenario: The test scenario to generate code for
            
        Returns:
            Generated test code
        """
        pass
    
    @abstractmethod
    def generate_step(self, step: TestStep) -> str:
        """Generate code for a single test step.
        
        Args:
            step: The test step to generate code for
            
        Returns:
            Generated code for the step
        """
        pass
    
    def generate_multiple(self, scenarios: List[TestScenario]) -> List[GeneratedTest]:
        """Generate tests for multiple scenarios.
        
        Args:
            scenarios: List of test scenarios
            
        Returns:
            List of generated tests
        """
        return [self.generate(scenario) for scenario in scenarios]
    
    def get_framework_name(self) -> str:
        """Get the name of the test framework."""
        return self.__class__.__name__.replace('Generator', '').lower()
    
    def get_language(self) -> str:
        """Get the programming language for generated tests."""
        return "python"  # Default to Python, override in subclasses