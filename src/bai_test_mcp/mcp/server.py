import asyncio
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from ..parsers import MermaidParser
from ..generators import PlaywrightGenerator, PytestGenerator, CypressGenerator, JestRTLGenerator
from ..parsers.base import TestScenario


class TestAutomationServer:
    """MCP server for test automation."""
    
    def __init__(self):
        self.server = Server("bai-test-automation")
        self.parser = MermaidParser()
        self.generators = {
            "playwright": PlaywrightGenerator(),
            "pytest": PytestGenerator(),
            "cypress": CypressGenerator(),
            "jest-rtl": JestRTLGenerator()
        }
        self.scenarios: Dict[str, TestScenario] = {}
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="parse_diagram",
                    description="Parse a Mermaid sequence diagram to extract test scenarios",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Mermaid diagram content or markdown with diagrams"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Path to file containing diagram (alternative to content)"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="generate_test",
                    description="Generate test code from a parsed scenario",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "scenario_name": {
                                "type": "string",
                                "description": "Name of the scenario to generate test for"
                            },
                            "framework": {
                                "type": "string",
                                "enum": ["playwright", "pytest", "cypress", "jest-rtl"],
                                "description": "Test framework to use"
                            },
                            "output_path": {
                                "type": "string",
                                "description": "Path to save generated test file"
                            },
                            "config": {
                                "type": "object",
                                "description": "Framework-specific configuration"
                            }
                        },
                        "required": ["scenario_name", "framework"]
                    }
                ),
                types.Tool(
                    name="list_scenarios",
                    description="List all parsed test scenarios",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="analyze_diagram",
                    description="Analyze a diagram and provide insights",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Mermaid diagram content"
                            }
                        },
                        "required": ["content"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Optional[Dict[str, Any]]
        ) -> list[types.TextContent]:
            if name == "parse_diagram":
                return await self._parse_diagram(arguments)
            elif name == "generate_test":
                return await self._generate_test(arguments)
            elif name == "list_scenarios":
                return await self._list_scenarios()
            elif name == "analyze_diagram":
                return await self._analyze_diagram(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _parse_diagram(self, args: Dict[str, Any]) -> list[types.TextContent]:
        """Parse diagram and extract scenarios."""
        content = args.get("content")
        file_path = args.get("file_path")
        
        if not content and not file_path:
            return [types.TextContent(
                type="text",
                text="Error: Either 'content' or 'file_path' must be provided"
            )]
        
        if file_path and not content:
            try:
                content = Path(file_path).read_text(encoding='utf-8')
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=f"Error reading file: {e}"
                )]
        
        try:
            scenarios = self.parser.parse(content)
            
            # Store scenarios
            for scenario in scenarios:
                self.scenarios[scenario.name] = scenario
            
            # Format response
            result = {
                "parsed_scenarios": len(scenarios),
                "scenarios": [
                    {
                        "name": s.name,
                        "description": s.description,
                        "steps": len(s.steps),
                        "actors": s.get_actors()
                    }
                    for s in scenarios
                ]
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error parsing diagram: {e}"
            )]
    
    async def _generate_test(self, args: Dict[str, Any]) -> list[types.TextContent]:
        """Generate test code from scenario."""
        scenario_name = args.get("scenario_name")
        framework = args.get("framework")
        output_path = args.get("output_path")
        config = args.get("config", {})
        
        if scenario_name not in self.scenarios:
            return [types.TextContent(
                type="text",
                text=f"Error: Scenario '{scenario_name}' not found. Available: {list(self.scenarios.keys())}"
            )]
        
        if framework not in self.generators:
            return [types.TextContent(
                type="text",
                text=f"Error: Framework '{framework}' not supported. Available: {list(self.generators.keys())}"
            )]
        
        try:
            scenario = self.scenarios[scenario_name]
            generator = self.generators[framework]
            
            # Update generator config
            if config:
                generator.config.update(config)
            
            # Generate test
            generated = generator.generate(scenario)
            
            # Save if output path provided
            if output_path:
                generated.save(Path(output_path))
                message = f"Test generated and saved to: {output_path}"
            else:
                message = "Test generated successfully"
            
            result = {
                "message": message,
                "test_name": generated.name,
                "framework": generated.framework,
                "code_preview": generated.code[:500] + "..." if len(generated.code) > 500 else generated.code
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error generating test: {e}"
            )]
    
    async def _list_scenarios(self) -> list[types.TextContent]:
        """List all available scenarios."""
        if not self.scenarios:
            return [types.TextContent(
                type="text",
                text="No scenarios parsed yet. Use 'parse_diagram' first."
            )]
        
        result = {
            "total_scenarios": len(self.scenarios),
            "scenarios": [
                {
                    "name": name,
                    "description": scenario.description,
                    "steps": len(scenario.steps),
                    "actors": scenario.get_actors(),
                    "api_calls": len(scenario.get_api_calls()),
                    "user_actions": len(scenario.get_user_actions())
                }
                for name, scenario in self.scenarios.items()
            ]
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def _analyze_diagram(self, args: Dict[str, Any]) -> list[types.TextContent]:
        """Analyze diagram and provide insights."""
        content = args.get("content")
        
        if not content:
            return [types.TextContent(
                type="text",
                text="Error: 'content' is required"
            )]
        
        try:
            scenarios = self.parser.parse(content)
            
            # Analyze the scenarios
            total_steps = sum(len(s.steps) for s in scenarios)
            all_actors = set()
            api_endpoints = set()
            user_actions = []
            
            for scenario in scenarios:
                all_actors.update(scenario.get_actors())
                
                for step in scenario.get_api_calls():
                    if 'endpoint' in step.data:
                        api_endpoints.add(f"{step.data['method']} {step.data['endpoint']}")
                
                for step in scenario.get_user_actions():
                    user_actions.append(step.action)
            
            analysis = {
                "summary": {
                    "total_scenarios": len(scenarios),
                    "total_steps": total_steps,
                    "unique_actors": list(all_actors),
                    "api_endpoints": list(api_endpoints)
                },
                "complexity": {
                    "average_steps_per_scenario": total_steps / len(scenarios) if scenarios else 0,
                    "has_api_calls": bool(api_endpoints),
                    "has_user_interactions": bool(user_actions)
                },
                "recommendations": self._get_recommendations(scenarios)
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(analysis, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error analyzing diagram: {e}"
            )]
    
    def _get_recommendations(self, scenarios: List[TestScenario]) -> List[str]:
        """Get test recommendations based on scenarios."""
        recommendations = []
        
        for scenario in scenarios:
            if len(scenario.steps) > 20:
                recommendations.append(f"Scenario '{scenario.name}' has {len(scenario.steps)} steps. Consider breaking it down.")
            
            api_calls = scenario.get_api_calls()
            if api_calls and not any('assertion' in str(s.step_type).lower() for s in scenario.steps):
                recommendations.append(f"Scenario '{scenario.name}' has API calls but no assertions.")
            
            if not scenario.get_user_actions() and not api_calls:
                recommendations.append(f"Scenario '{scenario.name}' has no clear actions to test.")
        
        if not recommendations:
            recommendations.append("Scenarios look well-structured for testing.")
        
        return recommendations
    
    async def run(self):
        """Run the MCP server."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="bai-test-automation",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


def main():
    """Main entry point for the server."""
    server = TestAutomationServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()