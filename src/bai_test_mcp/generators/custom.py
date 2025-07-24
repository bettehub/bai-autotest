from typing import Dict, Any, List, Optional
import json
import yaml
from pathlib import Path
from string import Template

from .base import TestGenerator, GeneratedTest
from ..parsers.base import TestScenario, TestStep, StepType


class CustomGenerator(TestGenerator):
    """Customizable test generator using templates for any language/framework."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.template_path = config.get('template_path') if config else None
        self.language = config.get('language', 'unknown') if config else 'unknown'
        self.framework = config.get('framework', 'custom') if config else 'custom'
        self.file_extension = config.get('file_extension', '.test') if config else '.test'
        self.templates = self._load_templates()
    
    def get_language(self) -> str:
        """Get the programming language for generated tests."""
        return self.language
    
    def get_framework_name(self) -> str:
        """Get the name of the test framework."""
        return self.framework
    
    def _load_templates(self) -> Dict[str, str]:
        """Load templates from config or use defaults."""
        templates = {}
        
        # Load from template file if provided
        if self.template_path:
            template_file = Path(self.template_path)
            if template_file.exists():
                if template_file.suffix == '.yaml' or template_file.suffix == '.yml':
                    with open(template_file, 'r', encoding='utf-8') as f:
                        templates = yaml.safe_load(f)
                elif template_file.suffix == '.json':
                    with open(template_file, 'r', encoding='utf-8') as f:
                        templates = json.load(f)
        
        # Use built-in templates if not provided
        if not templates:
            templates = self._get_builtin_templates()
        
        return templates
    
    def _get_builtin_templates(self) -> Dict[str, str]:
        """Get built-in templates for common languages/frameworks."""
        lang_framework = f"{self.language}_{self.framework}".lower()
        
        templates = {
            # Java JUnit
            "java_junit": {
                "imports": """import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;""",
                "class_start": "public class ${test_name} {",
                "class_end": "}",
                "setup": """    @BeforeEach
    void setUp() {
        // Setup code here
    }""",
                "test_start": """    @Test
    @DisplayName("${description}")
    void ${method_name}() {""",
                "test_end": "    }",
                "user_action": "        // User action: ${action}",
                "api_call": "        // API Call: ${method} ${endpoint}",
                "assertion": "        // Assert: ${description}",
                "navigation": "        // Navigate: ${action}",
                "file_extension": ".java"
            },
            
            # Java Spring Boot Test
            "java_spring": {
                "imports": """import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import static org.assertj.core.api.Assertions.assertThat;""",
                "class_start": """@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class ${test_name} {""",
                "class_end": "}",
                "setup": """    @Autowired
    private TestRestTemplate restTemplate;""",
                "test_start": """    @Test
    void ${method_name}() {""",
                "test_end": "    }",
                "api_call": """        ResponseEntity<String> response = restTemplate.${method_lower}ForEntity(
            "${endpoint}", 
            ${payload}, 
            String.class
        );
        assertThat(response.getStatusCode().is2xxSuccessful()).isTrue();""",
                "file_extension": ".java"
            },
            
            # Python unittest
            "python_unittest": {
                "imports": """import unittest
import requests
from unittest.mock import patch, Mock""",
                "class_start": "class ${test_name}(unittest.TestCase):",
                "class_end": """\nif __name__ == '__main__':
    unittest.main()""",
                "setup": """    def setUp(self):
        self.base_url = "${base_url}"""",
                "test_start": """    def test_${method_name}(self):
        \"\"\"${description}\"\"\"""",
                "test_end": "",
                "api_call": """        response = requests.${method_lower}(f"{self.base_url}${endpoint}")
        self.assertEqual(response.status_code, 200)""",
                "file_extension": ".py"
            },
            
            # Ruby RSpec
            "ruby_rspec": {
                "imports": """require 'spec_helper'
require 'net/http'
require 'json'""",
                "class_start": "RSpec.describe '${test_name}' do",
                "class_end": "end",
                "test_start": """  it '${description}' do""",
                "test_end": "  end",
                "api_call": """    uri = URI('${base_url}${endpoint}')
    response = Net::HTTP.${method_lower}(uri)
    expect(response.code).to eq('200')""",
                "file_extension": ".rb"
            },
            
            # Go testing
            "go_testing": {
                "imports": """package ${package_name}

import (
    "testing"
    "net/http"
    "net/http/httptest"
)""",
                "test_start": """func Test${test_name}(t *testing.T) {""",
                "test_end": "}",
                "api_call": """    resp, err := http.${method}("${endpoint}", nil)
    if err != nil {
        t.Fatal(err)
    }
    if resp.StatusCode != http.StatusOK {
        t.Errorf("Expected status 200, got %d", resp.StatusCode)
    }""",
                "file_extension": ".go"
            },
            
            # PHP PHPUnit
            "php_phpunit": {
                "imports": """<?php
use PHPUnit\Framework\TestCase;""",
                "class_start": "class ${test_name} extends TestCase {",
                "class_end": "}",
                "test_start": """    public function test${method_name}() {""",
                "test_end": "    }",
                "api_call": """        $response = $this->client->${method_lower}('${endpoint}');
        $this->assertEquals(200, $response->getStatusCode());""",
                "file_extension": ".php"
            },
            
            # Default template
            "default": {
                "test_start": "// Test: ${description}",
                "test_end": "// End test",
                "user_action": "// User action: ${action}",
                "api_call": "// API Call: ${method} ${endpoint}",
                "assertion": "// Assert: ${description}",
                "file_extension": ".test"
            }
        }
        
        # Return specific template or default
        return templates.get(lang_framework, templates["default"])
    
    def generate(self, scenario: TestScenario) -> GeneratedTest:
        """Generate test from scenario using templates."""
        # Prepare template variables
        template_vars = {
            'test_name': self._to_class_name(scenario.name),
            'method_name': self._to_method_name(scenario.name),
            'description': scenario.description,
            'base_url': self.config.get('base_url', 'http://localhost:8080'),
            'package_name': self.config.get('package_name', 'tests')
        }
        
        # Build test code
        parts = []
        
        # Add imports
        if 'imports' in self.templates:
            parts.append(Template(self.templates['imports']).safe_substitute(template_vars))
            parts.append("")
        
        # Add class start
        if 'class_start' in self.templates:
            parts.append(Template(self.templates['class_start']).safe_substitute(template_vars))
            parts.append("")
        
        # Add setup
        if 'setup' in self.templates:
            parts.append(Template(self.templates['setup']).safe_substitute(template_vars))
            parts.append("")
        
        # Add test method
        if 'test_start' in self.templates:
            parts.append(Template(self.templates['test_start']).safe_substitute(template_vars))
        
        # Generate steps
        for step in scenario.steps:
            step_code = self.generate_step(step)
            if step_code:
                parts.append(step_code)
        
        # Add test end
        if 'test_end' in self.templates:
            parts.append(Template(self.templates['test_end']).safe_substitute(template_vars))
            parts.append("")
        
        # Add class end
        if 'class_end' in self.templates:
            parts.append(Template(self.templates['class_end']).safe_substitute(template_vars))
        
        # Determine file extension
        file_ext = self.templates.get('file_extension', self.file_extension)
        
        return GeneratedTest(
            name=f"{scenario.name}{file_ext}",
            code="\n".join(parts),
            language=self.language,
            framework=self.framework,
            imports=[],
            metadata={
                'scenario_name': scenario.name,
                'template_used': f"{self.language}_{self.framework}"
            }
        )
    
    def generate_step(self, step: TestStep) -> str:
        """Generate code for a single step using templates."""
        template_key = self._get_template_key(step.step_type)
        
        if template_key not in self.templates:
            return f"        // {step.description}"
        
        template_str = self.templates[template_key]
        
        # Prepare variables for template
        vars = {
            'action': step.action,
            'description': step.description,
            'actor': step.actor,
            'target': step.target or '',
            'method': step.data.get('method', 'GET'),
            'method_lower': step.data.get('method', 'GET').lower(),
            'endpoint': step.data.get('endpoint', '/'),
            'payload': step.data.get('payload', 'null'),
            'expected': step.expected or ''
        }
        
        return Template(template_str).safe_substitute(vars)
    
    def _get_template_key(self, step_type: StepType) -> str:
        """Map step type to template key."""
        mapping = {
            StepType.USER_ACTION: 'user_action',
            StepType.API_CALL: 'api_call',
            StepType.ASSERTION: 'assertion',
            StepType.NAVIGATION: 'navigation',
            StepType.WAIT: 'wait',
            StepType.NOTE: 'note'
        }
        return mapping.get(step_type, 'default')
    
    def _to_class_name(self, name: str) -> str:
        """Convert name to class name (PascalCase)."""
        return ''.join(word.capitalize() for word in name.split('_'))
    
    def _to_method_name(self, name: str) -> str:
        """Convert name to method name (camelCase or snake_case based on language)."""
        if self.language in ['java', 'javascript', 'typescript']:
            # camelCase for Java/JS
            words = name.split('_')
            return words[0].lower() + ''.join(w.capitalize() for w in words[1:])
        else:
            # snake_case for Python, Ruby, etc.
            return name.lower()