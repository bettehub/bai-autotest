import asyncio
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class TestAutomationClient:
    """MCP client for test automation."""
    
    def __init__(self, server_script_path: str = "bai-test-mcp"):
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
    
    async def connect(self):
        """Connect to the MCP server."""
        server_params = StdioServerParameters(
            command=self.server_script_path,
            args=["serve"],
            env={}
        )
        
        self.session = await stdio_client(server_params)
        return self
    
    async def disconnect(self):
        """Disconnect from the server."""
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None
    
    async def parse_diagram(self, content: Optional[str] = None, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Parse a diagram to extract test scenarios."""
        if not self.session:
            raise RuntimeError("Not connected to server. Call connect() first.")
        
        args = {}
        if content:
            args["content"] = content
        if file_path:
            args["file_path"] = file_path
        
        result = await self.session.call_tool("parse_diagram", args)
        return json.loads(result.content[0].text)
    
    async def generate_test(
        self,
        scenario_name: str,
        framework: str,
        output_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate test code from a scenario."""
        if not self.session:
            raise RuntimeError("Not connected to server. Call connect() first.")
        
        args = {
            "scenario_name": scenario_name,
            "framework": framework
        }
        
        if output_path:
            args["output_path"] = output_path
        if config:
            args["config"] = config
        
        result = await self.session.call_tool("generate_test", args)
        return json.loads(result.content[0].text)
    
    async def list_scenarios(self) -> Dict[str, Any]:
        """List all available scenarios."""
        if not self.session:
            raise RuntimeError("Not connected to server. Call connect() first.")
        
        result = await self.session.call_tool("list_scenarios", {})
        return json.loads(result.content[0].text)
    
    async def analyze_diagram(self, content: str) -> Dict[str, Any]:
        """Analyze a diagram and get insights."""
        if not self.session:
            raise RuntimeError("Not connected to server. Call connect() first.")
        
        result = await self.session.call_tool("analyze_diagram", {"content": content})
        return json.loads(result.content[0].text)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


async def example_usage():
    """Example of how to use the client."""
    # Using context manager
    async with TestAutomationClient() as client:
        # Parse a diagram file
        result = await client.parse_diagram(file_path="auth_flow.md")
        print(f"Parsed {result['parsed_scenarios']} scenarios")
        
        # List scenarios
        scenarios = await client.list_scenarios()
        for scenario in scenarios['scenarios']:
            print(f"- {scenario['name']}: {scenario['description']}")
        
        # Generate Playwright test
        test_result = await client.generate_test(
            scenario_name=scenarios['scenarios'][0]['name'],
            framework="playwright",
            output_path="tests/test_auth.py",
            config={"base_url": "https://bai.example.com"}
        )
        print(f"Generated test: {test_result['message']}")


if __name__ == "__main__":
    asyncio.run(example_usage())