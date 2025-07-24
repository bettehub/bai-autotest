from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class StepType(Enum):
    """Types of test steps."""
    USER_ACTION = "user_action"
    API_CALL = "api_call"
    ASSERTION = "assertion"
    NAVIGATION = "navigation"
    WAIT = "wait"
    NOTE = "note"


@dataclass
class TestStep:
    """Represents a single test step."""
    step_type: StepType
    actor: str
    target: Optional[str] = None
    action: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    expected: Optional[Any] = None
    description: str = ""
    
    def __post_init__(self):
        if not self.description:
            self.description = f"{self.actor} {self.action}"
            if self.target:
                self.description += f" to {self.target}"


@dataclass
class TestScenario:
    """Represents a complete test scenario."""
    name: str
    description: str
    steps: List[TestStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, step: TestStep) -> None:
        """Add a step to the scenario."""
        self.steps.append(step)
    
    def get_actors(self) -> List[str]:
        """Get unique actors in the scenario."""
        return list(set(step.actor for step in self.steps if step.actor))
    
    def get_api_calls(self) -> List[TestStep]:
        """Get all API call steps."""
        return [step for step in self.steps if step.step_type == StepType.API_CALL]
    
    def get_user_actions(self) -> List[TestStep]:
        """Get all user action steps."""
        return [step for step in self.steps if step.step_type == StepType.USER_ACTION]


class DiagramParser(ABC):
    """Abstract base class for diagram parsers."""
    
    @abstractmethod
    def parse(self, content: str) -> List[TestScenario]:
        """Parse diagram content and return test scenarios.
        
        Args:
            content: The diagram content as string
            
        Returns:
            List of test scenarios extracted from the diagram
        """
        pass
    
    @abstractmethod
    def validate(self, content: str) -> bool:
        """Validate if the content can be parsed.
        
        Args:
            content: The diagram content to validate
            
        Returns:
            True if content is valid, False otherwise
        """
        pass
    
    def parse_file(self, file_path: str) -> List[TestScenario]:
        """Parse diagram from file.
        
        Args:
            file_path: Path to the diagram file
            
        Returns:
            List of test scenarios
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse(content)