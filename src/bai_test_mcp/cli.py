import click
import asyncio
import json
from pathlib import Path
from typing import Optional

from .mcp.server import TestAutomationServer
from .mcp.client import TestAutomationClient
from .parsers import MermaidParser
from .generators import PlaywrightGenerator, PytestGenerator, CypressGenerator, JestRTLGenerator, CustomGenerator


@click.group()
def cli():
    """bai.ai.kr Test MCP - Test automation from diagrams."""
    pass


@cli.command()
def serve():
    """Start the MCP server."""
    click.echo("Starting bai.ai.kr Test MCP server...")
    server = TestAutomationServer()
    asyncio.run(server.run())


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output directory for generated tests')
@click.option('--framework', '-f', type=click.Choice(['playwright', 'pytest', 'cypress', 'jest-rtl', 'custom']), default='playwright')
@click.option('--language', '-l', help='Programming language for custom generator')
@click.option('--template', '-t', help='Template file path for custom generator')
@click.option('--base-url', help='Base URL for tests')
def generate(file_path: str, output: Optional[str], framework: str, base_url: Optional[str], language: Optional[str], template: Optional[str]):
    """Generate tests from a diagram file."""
    click.echo(f"Parsing diagram from {file_path}...")
    
    # Parse diagram
    parser = MermaidParser()
    content = Path(file_path).read_text()
    scenarios = parser.parse(content)
    
    if not scenarios:
        click.echo("No scenarios found in the diagram.")
        return
    
    click.echo(f"Found {len(scenarios)} scenario(s):")
    for i, scenario in enumerate(scenarios):
        click.echo(f"  {i+1}. {scenario.name} - {scenario.description}")
    
    # Generate tests
    config = {}
    if base_url:
        config['base_url'] = base_url
    
    if framework == 'playwright':
        generator = PlaywrightGenerator(config)
    elif framework == 'pytest':
        generator = PytestGenerator(config)
    elif framework == 'cypress':
        generator = CypressGenerator(config)
    elif framework == 'jest-rtl':
        generator = JestRTLGenerator(config)
    elif framework == 'custom':
        if not language:
            click.echo("Error: --language is required for custom generator")
            return
        config['language'] = language
        config['framework'] = language  # Default framework name to language
        if template:
            config['template_path'] = template
        generator = CustomGenerator(config)
    else:
        raise ValueError(f"Unknown framework: {framework}")
    
    output_dir = Path(output) if output else Path('tests')
    output_dir.mkdir(exist_ok=True)
    
    for scenario in scenarios:
        click.echo(f"\nGenerating {framework} test for {scenario.name}...")
        
        generated = generator.generate(scenario)
        output_file = output_dir / generated.name
        generated.save(output_file)
        
        click.echo(f"✓ Generated: {output_file}")


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def parse(file_path: str):
    """Parse a diagram and show extracted scenarios."""
    parser = MermaidParser()
    content = Path(file_path).read_text()
    scenarios = parser.parse(content)
    
    if not scenarios:
        click.echo("No scenarios found.")
        return
    
    for scenario in scenarios:
        click.echo(f"\nScenario: {scenario.name}")
        click.echo(f"Description: {scenario.description}")
        click.echo(f"Actors: {', '.join(scenario.get_actors())}")
        click.echo(f"Steps: {len(scenario.steps)}")
        
        click.echo("\nSteps:")
        for i, step in enumerate(scenario.steps, 1):
            click.echo(f"  {i}. [{step.step_type.value}] {step.description}")


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def analyze(file_path: str):
    """Analyze a diagram and provide insights."""
    async def run_analysis():
        async with TestAutomationClient() as client:
            content = Path(file_path).read_text()
            result = await client.analyze_diagram(content)
            
            click.echo("\nDiagram Analysis:")
            click.echo(f"Total Scenarios: {result['summary']['total_scenarios']}")
            click.echo(f"Total Steps: {result['summary']['total_steps']}")
            click.echo(f"Unique Actors: {', '.join(result['summary']['unique_actors'])}")
            
            if result['summary']['api_endpoints']:
                click.echo("\nAPI Endpoints:")
                for endpoint in result['summary']['api_endpoints']:
                    click.echo(f"  - {endpoint}")
            
            click.echo("\nRecommendations:")
            for rec in result['recommendations']:
                click.echo(f"  • {rec}")
    
    asyncio.run(run_analysis())


@cli.command()
def templates():
    """List available test templates."""
    from .generators.template_loader import TemplateLoader
    
    click.echo("\n📦 Available Test Templates:\n")
    
    templates = TemplateLoader.list_available_templates()
    for language, frameworks in templates.items():
        click.echo(f"🔹 {language.upper()}")
        for framework in frameworks:
            click.echo(f"   - {framework}")
    
    click.echo("\n💡 Usage:")
    click.echo("  # Use built-in template")
    click.echo("  bai-autotest generate auth.md -f custom -l java --template java_junit")
    click.echo("\n  # Use custom template file")
    click.echo("  bai-autotest generate auth.md -f custom -l kotlin --template ./my-template.yaml")
    click.echo("\n📑 Custom Template Example:")
    click.echo("  See: examples/custom_template.yaml")


@cli.command()
@click.option('--example', '-e', type=click.Choice(['login', 'api', 'e2e']), help='Show example diagram')
def examples(example: Optional[str]):
    """Show example diagrams and generated tests."""
    examples_map = {
        'login': {
            'name': 'Login Flow',
            'diagram': '''```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    
    User->>Frontend: Enter email and password
    User->>Frontend: Click "Login" button
    Frontend->>API: POST /api/v1/users/login
    API-->>Frontend: JWT tokens (cookies)
    Frontend->>Frontend: Redirect to dashboard
```'''
        },
        'api': {
            'name': 'API Test Flow',
            'diagram': '''```mermaid
sequenceDiagram
    participant Test
    participant API
    
    Test->>API: POST /api/users {"name": "John"}
    API-->>Test: 201 Created
    Test->>API: GET /api/users/1
    API-->>Test: User data
```'''
        },
        'e2e': {
            'name': 'E2E User Journey',
            'diagram': '''```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant Backend
    
    User->>Browser: Navigate to /signup
    User->>Browser: Fill registration form
    Browser->>Backend: POST /api/register
    Backend-->>Browser: Success response
    Browser->>Browser: Show success message
```'''
        }
    }
    
    if example:
        ex = examples_map[example]
        click.echo(f"\n{ex['name']} Example:")
        click.echo(ex['diagram'])
    else:
        click.echo("\nAvailable examples:")
        for key, ex in examples_map.items():
            click.echo(f"  - {key}: {ex['name']}")
        click.echo("\nUse --example <name> to see a specific example.")


def main():
    """Main CLI entry point."""
    cli()


if __name__ == '__main__':
    main()