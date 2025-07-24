from typing import Dict, Any, Optional
import json
import yaml
from pathlib import Path


class TemplateLoader:
    """Load and manage test templates for various languages and frameworks."""
    
    BUILTIN_TEMPLATES_DIR = Path(__file__).parent / "templates"
    
    @classmethod
    def load_template(cls, language: str, framework: str, custom_path: Optional[str] = None) -> Dict[str, Any]:
        """Load template for given language and framework."""
        if custom_path:
            return cls._load_custom_template(custom_path)
        
        # Try to load built-in template
        template_name = f"{language}_{framework}.yaml"
        template_path = cls.BUILTIN_TEMPLATES_DIR / template_name
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        # Return default template if not found
        return cls._get_default_template()
    
    @classmethod
    def _load_custom_template(cls, path: str) -> Dict[str, Any]:
        """Load custom template from file."""
        template_path = Path(path)
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {path}")
        
        if template_path.suffix in ['.yaml', '.yml']:
            with open(template_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        elif template_path.suffix == '.json':
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise ValueError(f"Unsupported template format: {template_path.suffix}")
    
    @classmethod
    def _get_default_template(cls) -> Dict[str, Any]:
        """Get default template."""
        return {
            "file_extension": ".test",
            "test_start": "// Test: ${description}",
            "test_end": "// End test",
            "user_action": "// User action: ${action}",
            "api_call": "// API Call: ${method} ${endpoint}",
            "assertion": "// Assert: ${description}",
            "navigation": "// Navigate: ${action}",
            "wait": "// Wait: ${timeout}ms",
            "note": "// Note: ${description}"
        }
    
    @classmethod
    def list_available_templates(cls) -> Dict[str, list]:
        """List all available built-in templates."""
        templates = {
            "java": ["junit", "spring", "testng"],
            "python": ["pytest", "unittest"],
            "javascript": ["jest", "mocha", "cypress"],
            "typescript": ["jest", "mocha", "cypress"],
            "ruby": ["rspec", "minitest"],
            "go": ["testing"],
            "php": ["phpunit"],
            "csharp": ["nunit", "xunit"],
            "kotlin": ["junit", "kotest"],
            "swift": ["xctest"]
        }
        return templates