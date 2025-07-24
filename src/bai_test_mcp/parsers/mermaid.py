import re
from typing import List, Dict, Tuple, Optional
from lark import Lark, Tree, Token
from lark.visitors import Interpreter

from .base import DiagramParser, TestScenario, TestStep, StepType


MERMAID_GRAMMAR = r"""
    ?start: "sequenceDiagram" _NL+ sequence
    
    sequence: (declaration | interaction | note)*
    
    declaration: "participant" actor ("as" alias)? _NL+
    
    interaction: actor arrow actor ":" message _NL+
               | actor arrow actor _NL+
    
    note: "Note" position actor ":" message _NL+
    
    arrow: "->>" | "-->>" | "->>+" | "-->>+" | "<<-" | "<<--" | "-x" | "--x"
    
    position: "over" | "left of" | "right of"
    
    actor: WORD
    alias: STRING | PHRASE
    message: STRING | PHRASE | REST_OF_LINE
    
    WORD: /[a-zA-Z_][a-zA-Z0-9_]*/
    STRING: /"[^"]*"/
    PHRASE: /[^\n]+/
    REST_OF_LINE: /[^\n]+/
    
    _NL: /\r?\n/
    
    %import common.WS
    %ignore WS
"""


class MermaidInterpreter(Interpreter):
    """Interpreter for Mermaid sequence diagrams."""
    
    def __init__(self):
        self.actors = {}
        self.steps = []
    
    def declaration(self, tree):
        actor = str(tree.children[0])
        alias = str(tree.children[1]) if len(tree.children) > 1 else actor
        self.actors[actor] = alias
    
    def interaction(self, tree):
        source = str(tree.children[0])
        arrow = str(tree.children[1])
        target = str(tree.children[2])
        message = str(tree.children[3]).strip('"') if len(tree.children) > 3 else ""
        
        # Determine step type based on arrow and message
        step_type = self._determine_step_type(source, target, arrow, message)
        
        # Extract data from message if it's an API call
        data = {}
        if step_type == StepType.API_CALL:
            data = self._extract_api_data(message)
        
        step = TestStep(
            step_type=step_type,
            actor=source,
            target=target,
            action=message,
            data=data
        )
        
        self.steps.append(step)
    
    def note(self, tree):
        position = str(tree.children[0])
        actor = str(tree.children[1])
        message = str(tree.children[2]).strip('"')
        
        step = TestStep(
            step_type=StepType.NOTE,
            actor=actor,
            action=f"Note {position}: {message}",
            description=message
        )
        
        self.steps.append(step)
    
    def _determine_step_type(self, source: str, target: str, arrow: str, message: str) -> StepType:
        """Determine the type of step based on actors and message."""
        message_lower = message.lower()
        
        # Check for API calls
        if any(method in message_lower for method in ['get ', 'post ', 'put ', 'delete ', 'patch ']):
            return StepType.API_CALL
        
        # Check for user actions
        if source.lower() in ['user', 'client', 'browser']:
            if any(action in message_lower for action in ['click', 'type', 'enter', 'select', 'submit']):
                return StepType.USER_ACTION
            elif any(nav in message_lower for nav in ['navigate', 'go to', 'visit', 'open']):
                return StepType.NAVIGATION
        
        # Check for assertions (return arrows)
        if arrow.startswith('--'):
            return StepType.ASSERTION
        
        # Default to user action for other cases
        return StepType.USER_ACTION
    
    def _extract_api_data(self, message: str) -> Dict:
        """Extract API method and endpoint from message."""
        data = {}
        
        # Extract HTTP method and endpoint
        match = re.match(r'(GET|POST|PUT|DELETE|PATCH)\s+([^\s]+)', message, re.IGNORECASE)
        if match:
            data['method'] = match.group(1).upper()
            data['endpoint'] = match.group(2)
        
        # Extract JSON payload if present
        json_match = re.search(r'\{.*\}', message)
        if json_match:
            data['payload'] = json_match.group(0)
        
        return data


class MermaidParser(DiagramParser):
    """Parser for Mermaid sequence diagrams."""
    
    def __init__(self):
        self.parser = Lark(MERMAID_GRAMMAR, start='start', parser='lalr')
    
    def parse(self, content: str) -> List[TestScenario]:
        """Parse Mermaid sequence diagram and extract test scenarios."""
        scenarios = []
        
        # Extract all Mermaid blocks from content
        mermaid_blocks = self._extract_mermaid_blocks(content)
        
        for idx, block in enumerate(mermaid_blocks):
            if not self.validate(block):
                continue
            
            try:
                # Parse the diagram
                tree = self.parser.parse(block)
                
                # Interpret the tree
                interpreter = MermaidInterpreter()
                interpreter.visit(tree)
                
                # Create scenario from interpreted steps
                scenario = self._create_scenario(interpreter, idx)
                scenarios.append(scenario)
                
            except Exception as e:
                # Log error but continue with other blocks
                print(f"Error parsing block {idx}: {e}")
                continue
        
        return scenarios
    
    def validate(self, content: str) -> bool:
        """Validate if content is a valid Mermaid sequence diagram."""
        # Check if it contains sequenceDiagram declaration
        if 'sequenceDiagram' not in content:
            return False
        
        try:
            self.parser.parse(content)
            return True
        except:
            return False
    
    def _extract_mermaid_blocks(self, content: str) -> List[str]:
        """Extract Mermaid code blocks from markdown content."""
        blocks = []
        
        # Pattern for code blocks with mermaid language
        pattern = r'```mermaid\s*\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)
        blocks.extend(matches)
        
        # If no code blocks found, try to parse the entire content
        if not blocks and 'sequenceDiagram' in content:
            blocks.append(content)
        
        return blocks
    
    def _create_scenario(self, interpreter: MermaidInterpreter, idx: int) -> TestScenario:
        """Create test scenario from interpreted data."""
        # Generate scenario name based on actors or index
        actors = list(interpreter.actors.keys())
        if actors:
            name = f"{actors[0]}_flow_{idx}"
        else:
            name = f"scenario_{idx}"
        
        # Analyze steps to create description
        api_calls = [s for s in interpreter.steps if s.step_type == StepType.API_CALL]
        user_actions = [s for s in interpreter.steps if s.step_type == StepType.USER_ACTION]
        
        description_parts = []
        if user_actions:
            description_parts.append(f"{len(user_actions)} user actions")
        if api_calls:
            description_parts.append(f"{len(api_calls)} API calls")
        
        description = f"Test scenario with {', '.join(description_parts)}" if description_parts else "Test scenario"
        
        scenario = TestScenario(
            name=name,
            description=description,
            steps=interpreter.steps,
            metadata={
                'actors': interpreter.actors,
                'total_steps': len(interpreter.steps)
            }
        )
        
        return scenario