"""
DeepFabric Data Generator - Creates 1M+ high-quality tool-calling examples
Generates synthetic data with real-world patterns for 99% accuracy training
"""

import json
import random
import asyncio
import hashlib
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from pathlib import Path
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Tool taxonomy with detailed parameter specifications
TOOL_TAXONOMY = {
    "file_operations": {
        "read_file": {
            "params": ["file_path", "encoding", "start_line", "end_line"],
            "required": ["file_path"],
            "types": {"file_path": "str", "encoding": "str", "start_line": "int", "end_line": "int"}
        },
        "write_file": {
            "params": ["file_path", "content", "encoding", "create_dirs"],
            "required": ["file_path", "content"],
            "types": {"file_path": "str", "content": "str", "encoding": "str", "create_dirs": "bool"}
        },
        "edit_file": {
            "params": ["file_path", "old_content", "new_content", "regex", "multiline"],
            "required": ["file_path", "old_content", "new_content"],
            "types": {"file_path": "str", "old_content": "str", "new_content": "str", "regex": "bool", "multiline": "bool"}
        },
        "delete_file": {
            "params": ["file_path", "recursive", "force"],
            "required": ["file_path"],
            "types": {"file_path": "str", "recursive": "bool", "force": "bool"}
        },
        "search_files": {
            "params": ["pattern", "path", "file_type", "max_results", "case_sensitive"],
            "required": ["pattern"],
            "types": {"pattern": "str", "path": "str", "file_type": "str", "max_results": "int", "case_sensitive": "bool"}
        }
    },
    "code_operations": {
        "generate_function": {
            "params": ["description", "language", "name", "params", "return_type", "docstring"],
            "required": ["description", "language"],
            "types": {"description": "str", "language": "str", "name": "str", "params": "list", "return_type": "str", "docstring": "str"}
        },
        "refactor_code": {
            "params": ["code", "refactor_type", "target", "new_name"],
            "required": ["code", "refactor_type"],
            "types": {"code": "str", "refactor_type": "str", "target": "str", "new_name": "str"}
        },
        "analyze_code": {
            "params": ["code", "analysis_type", "metrics", "language"],
            "required": ["code"],
            "types": {"code": "str", "analysis_type": "str", "metrics": "list", "language": "str"}
        },
        "debug_code": {
            "params": ["code", "error", "stack_trace", "context"],
            "required": ["code", "error"],
            "types": {"code": "str", "error": "str", "stack_trace": "str", "context": "dict"}
        },
        "write_tests": {
            "params": ["code", "test_framework", "coverage_target", "test_types"],
            "required": ["code"],
            "types": {"code": "str", "test_framework": "str", "coverage_target": "float", "test_types": "list"}
        }
    },
    "git_operations": {
        "git_commit": {
            "params": ["message", "files", "amend", "author"],
            "required": ["message"],
            "types": {"message": "str", "files": "list", "amend": "bool", "author": "str"}
        },
        "git_branch": {
            "params": ["action", "branch_name", "base_branch"],
            "required": ["action", "branch_name"],
            "types": {"action": "str", "branch_name": "str", "base_branch": "str"}
        },
        "git_merge": {
            "params": ["source_branch", "target_branch", "strategy", "squash"],
            "required": ["source_branch"],
            "types": {"source_branch": "str", "target_branch": "str", "strategy": "str", "squash": "bool"}
        }
    },
    "system_operations": {
        "run_command": {
            "params": ["command", "args", "cwd", "env", "timeout"],
            "required": ["command"],
            "types": {"command": "str", "args": "list", "cwd": "str", "env": "dict", "timeout": "int"}
        },
        "install_package": {
            "params": ["package", "version", "manager", "global", "dev"],
            "required": ["package"],
            "types": {"package": "str", "version": "str", "manager": "str", "global": "bool", "dev": "bool"}
        }
    }
}

@dataclass
class ToolCall:
    """Represents a single tool call with parameters"""
    tool_category: str
    tool_name: str
    parameters: Dict[str, Any]
    expected_output: Any
    confidence: float
    reasoning: str
    alternatives: List[Tuple[str, Dict[str, Any], float]]

@dataclass
class TrainingExample:
    """A complete training example for tool-calling"""
    id: str
    user_input: str
    intent: str
    tool_calls: List[ToolCall]
    execution_order: List[int]
    dependencies: Dict[int, List[int]]
    expected_output: Any
    metadata: Dict[str, Any]
    complexity: float
    
class ComplexityLevel(Enum):
    """Task complexity levels"""
    SIMPLE = 1      # Single tool, straightforward params
    MODERATE = 2    # 2-3 tools, some logic
    COMPLEX = 3     # 4+ tools, dependencies
    EXPERT = 4      # Complex workflow, error handling

class DataGenerator:
    """
    Generates high-quality synthetic training data for tool-calling
    Creates 1M+ examples across different complexity levels
    """
    
    def __init__(self, output_dir: str = "./training_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics tracking
        self.stats = {
            "total_generated": 0,
            "by_complexity": {level.name: 0 for level in ComplexityLevel},
            "by_category": {},
            "avg_tools_per_example": 0
        }
        
        # Load templates and patterns
        self.templates = self._load_templates()
        self.patterns = self._load_patterns()
        
        logger.info(f"DataGenerator initialized, output: {self.output_dir}")
    
    async def generate_dataset(self, 
                              num_examples: int = 1_000_000,
                              complexity_distribution: Optional[Dict[str, float]] = None) -> str:
        """
        Generate complete training dataset
        
        Args:
            num_examples: Total number of examples to generate
            complexity_distribution: Distribution of complexity levels
            
        Returns:
            Path to generated dataset
        """
        if complexity_distribution is None:
            complexity_distribution = {
                "SIMPLE": 0.4,      # 400,000 examples
                "MODERATE": 0.35,   # 350,000 examples
                "COMPLEX": 0.2,     # 200,000 examples
                "EXPERT": 0.05      # 50,000 examples
            }
        
        logger.info(f"Generating {num_examples:,} training examples...")
        
        # Calculate examples per complexity level
        examples_per_level = {}
        for level, ratio in complexity_distribution.items():
            examples_per_level[level] = int(num_examples * ratio)
        
        # Generate examples in batches
        batch_size = 1000
        all_examples = []
        
        for complexity, count in examples_per_level.items():
            level = ComplexityLevel[complexity]
            
            for batch_num in range(0, count, batch_size):
                batch_examples = await self._generate_batch(
                    level, 
                    min(batch_size, count - batch_num)
                )
                all_examples.extend(batch_examples)
                
                # Save intermediate results
                if len(all_examples) % 10000 == 0:
                    await self._save_checkpoint(all_examples)
                    logger.info(f"Generated {len(all_examples):,} examples...")
        
        # Shuffle for better training
        random.shuffle(all_examples)
        
        # Split into train/val/test
        dataset = self._split_dataset(all_examples)
        
        # Save final dataset
        dataset_path = await self._save_dataset(dataset)
        
        # Generate statistics report
        self._generate_report(dataset)
        
        logger.info(f"Dataset generation complete: {dataset_path}")
        return dataset_path
    
    async def _generate_batch(self, complexity: ComplexityLevel, batch_size: int) -> List[TrainingExample]:
        """Generate a batch of examples at specified complexity"""
        batch = []
        
        for _ in range(batch_size):
            if complexity == ComplexityLevel.SIMPLE:
                example = await self._generate_simple_example()
            elif complexity == ComplexityLevel.MODERATE:
                example = await self._generate_moderate_example()
            elif complexity == ComplexityLevel.COMPLEX:
                example = await self._generate_complex_example()
            else:  # EXPERT
                example = await self._generate_expert_example()
            
            batch.append(example)
            self.stats["total_generated"] += 1
            self.stats["by_complexity"][complexity.name] += 1
        
        return batch
    
    async def _generate_simple_example(self) -> TrainingExample:
        """Generate a simple single-tool example"""
        # Select random tool category and tool
        category = random.choice(list(TOOL_TAXONOMY.keys()))
        tool_name = random.choice(list(TOOL_TAXONOMY[category].keys()))
        tool_spec = TOOL_TAXONOMY[category][tool_name]
        
        # Generate user input
        user_input = self._generate_user_input(category, tool_name, ComplexityLevel.SIMPLE)
        
        # Extract parameters
        params = self._extract_parameters(user_input, tool_spec)
        
        # Create tool call
        tool_call = ToolCall(
            tool_category=category,
            tool_name=tool_name,
            parameters=params,
            expected_output=self._simulate_output(tool_name, params),
            confidence=0.95 + random.random() * 0.05,  # 95-100% confidence
            reasoning=self._generate_reasoning(user_input, tool_name),
            alternatives=[]
        )
        
        # Create training example
        example = TrainingExample(
            id=self._generate_id(),
            user_input=user_input,
            intent=self._extract_intent(user_input),
            tool_calls=[tool_call],
            execution_order=[0],
            dependencies={},
            expected_output=tool_call.expected_output,
            metadata={
                "complexity": ComplexityLevel.SIMPLE.value,
                "category": category,
                "timestamp": datetime.now().isoformat()
            },
            complexity=0.2 + random.random() * 0.2  # 0.2-0.4
        )
        
        return example
    
    async def _generate_moderate_example(self) -> TrainingExample:
        """Generate a moderate multi-tool example"""
        num_tools = random.randint(2, 3)
        tool_calls = []
        
        # Create a coherent workflow
        workflow = self._generate_workflow(num_tools, ComplexityLevel.MODERATE)
        user_input = workflow["user_input"]
        
        for i, step in enumerate(workflow["steps"]):
            tool_call = ToolCall(
                tool_category=step["category"],
                tool_name=step["tool"],
                parameters=step["params"],
                expected_output=self._simulate_output(step["tool"], step["params"]),
                confidence=0.9 + random.random() * 0.1,
                reasoning=step["reasoning"],
                alternatives=self._generate_alternatives(step, 0.1)
            )
            tool_calls.append(tool_call)
        
        # Define execution order and dependencies
        execution_order = list(range(num_tools))
        dependencies = self._generate_dependencies(workflow, num_tools)
        
        example = TrainingExample(
            id=self._generate_id(),
            user_input=user_input,
            intent=workflow["intent"],
            tool_calls=tool_calls,
            execution_order=execution_order,
            dependencies=dependencies,
            expected_output=self._combine_outputs(tool_calls),
            metadata={
                "complexity": ComplexityLevel.MODERATE.value,
                "workflow_type": workflow["type"],
                "timestamp": datetime.now().isoformat()
            },
            complexity=0.4 + random.random() * 0.3  # 0.4-0.7
        )
        
        return example
    
    async def _generate_complex_example(self) -> TrainingExample:
        """Generate a complex multi-tool example with dependencies"""
        num_tools = random.randint(4, 7)
        
        # Generate a complex scenario
        scenario = self._generate_complex_scenario()
        tool_calls = []
        
        for step in scenario["steps"]:
            tool_call = ToolCall(
                tool_category=step["category"],
                tool_name=step["tool"],
                parameters=step["params"],
                expected_output=self._simulate_output(step["tool"], step["params"]),
                confidence=0.85 + random.random() * 0.15,
                reasoning=step["reasoning"],
                alternatives=self._generate_alternatives(step, 0.2)
            )
            tool_calls.append(tool_call)
        
        # Complex dependencies
        dependencies = scenario["dependencies"]
        execution_order = self._topological_sort(dependencies, num_tools)
        
        example = TrainingExample(
            id=self._generate_id(),
            user_input=scenario["user_input"],
            intent=scenario["intent"],
            tool_calls=tool_calls,
            execution_order=execution_order,
            dependencies=dependencies,
            expected_output=scenario["expected_output"],
            metadata={
                "complexity": ComplexityLevel.COMPLEX.value,
                "scenario_type": scenario["type"],
                "has_parallelism": scenario.get("parallel", False),
                "timestamp": datetime.now().isoformat()
            },
            complexity=0.7 + random.random() * 0.2  # 0.7-0.9
        )
        
        return example
    
    async def _generate_expert_example(self) -> TrainingExample:
        """Generate an expert-level example with error handling and recovery"""
        # Expert examples include error scenarios and recovery
        scenario = self._generate_expert_scenario()
        
        tool_calls = []
        for step in scenario["steps"]:
            # Include potential errors and recovery strategies
            tool_call = ToolCall(
                tool_category=step["category"],
                tool_name=step["tool"],
                parameters=step["params"],
                expected_output=step.get("output", self._simulate_output(step["tool"], step["params"])),
                confidence=0.8 + random.random() * 0.2,
                reasoning=step["reasoning"],
                alternatives=self._generate_alternatives(step, 0.3)
            )
            
            # Add error handling metadata
            if "error_handling" in step:
                tool_call.error_handling = step["error_handling"]
            
            tool_calls.append(tool_call)
        
        example = TrainingExample(
            id=self._generate_id(),
            user_input=scenario["user_input"],
            intent=scenario["intent"],
            tool_calls=tool_calls,
            execution_order=scenario["execution_order"],
            dependencies=scenario["dependencies"],
            expected_output=scenario["expected_output"],
            metadata={
                "complexity": ComplexityLevel.EXPERT.value,
                "scenario_type": scenario["type"],
                "has_error_recovery": True,
                "recovery_strategies": scenario.get("recovery_strategies", []),
                "timestamp": datetime.now().isoformat()
            },
            complexity=0.9 + random.random() * 0.1  # 0.9-1.0
        )
        
        return example
    
    def _generate_user_input(self, category: str, tool: str, complexity: ComplexityLevel) -> str:
        """Generate realistic user input for a tool"""
        templates = {
            "file_operations": {
                "read_file": [
                    "Read the file {file_path}",
                    "Show me the contents of {file_path}",
                    "Can you open {file_path} and display it?",
                    "I need to see what's in {file_path}",
                    "Display {file_path} from line {start} to {end}"
                ],
                "write_file": [
                    "Create a file {file_path} with content: {content}",
                    "Write {content} to {file_path}",
                    "Save this to {file_path}: {content}",
                    "Make a new file at {file_path} containing {content}"
                ],
                "search_files": [
                    "Search for {pattern} in all files",
                    "Find files containing {pattern}",
                    "Look for {pattern} in {file_type} files",
                    "Search {pattern} recursively in {path}"
                ]
            },
            "code_operations": {
                "generate_function": [
                    "Create a {language} function that {description}",
                    "Write a function to {description} in {language}",
                    "Generate a {language} function called {name} that {description}",
                    "I need a function that {description}"
                ],
                "refactor_code": [
                    "Refactor this code: {code}",
                    "Rename {target} to {new_name} in this code",
                    "Extract method {target} from this code",
                    "Improve this code structure: {code}"
                ]
            }
        }
        
        # Get templates for this category/tool
        if category in templates and tool in templates[category]:
            template = random.choice(templates[category][tool])
            
            # Fill in placeholders
            params = self._generate_realistic_params(category, tool)
            return template.format(**params)
        
        # Fallback to generic
        return f"Please {tool.replace('_', ' ')} with appropriate parameters"
    
    def _generate_realistic_params(self, category: str, tool: str) -> Dict[str, Any]:
        """Generate realistic parameters for a tool"""
        params = {}
        
        if category == "file_operations":
            params["file_path"] = random.choice([
                "src/main.py",
                "tests/test_app.py",
                "README.md",
                "config/settings.json",
                "lib/utils.js",
                "app/models/user.rb"
            ])
            params["content"] = random.choice([
                "def hello_world():\\n    print('Hello, World!')",
                "# TODO: Implement this function",
                "import numpy as np\\nimport pandas as pd",
                "const express = require('express');",
                "class User < ApplicationRecord\\nend"
            ])
            params["pattern"] = random.choice([
                "TODO", "FIXME", "import", "function", "class", "error"
            ])
            params["start"] = random.randint(1, 50)
            params["end"] = params["start"] + random.randint(10, 100)
            params["file_type"] = random.choice(["py", "js", "ts", "java", "go"])
            params["path"] = random.choice(["./src", "./tests", ".", "./lib"])
            
        elif category == "code_operations":
            params["language"] = random.choice(["python", "javascript", "typescript", "java", "go"])
            params["description"] = random.choice([
                "calculates fibonacci numbers",
                "sorts an array in place",
                "validates email addresses",
                "connects to a database",
                "processes CSV files"
            ])
            params["name"] = random.choice(["process", "calculate", "validate", "transform", "analyze"])
            params["code"] = "def example():\\n    pass  # TODO: implement"
            params["target"] = "example"
            params["new_name"] = "better_example"
        
        return params
    
    def _extract_parameters(self, user_input: str, tool_spec: Dict) -> Dict[str, Any]:
        """Extract parameters from user input based on tool specification"""
        params = {}
        
        # Initialize with required parameters
        for param in tool_spec["required"]:
            param_type = tool_spec["types"][param]
            
            # Try to extract from user input
            extracted = self._extract_param_from_text(user_input, param, param_type)
            if extracted is not None:
                params[param] = extracted
            else:
                # Generate default based on type
                params[param] = self._generate_default_param(param, param_type)
        
        # Add optional parameters with some probability
        for param in tool_spec["params"]:
            if param not in params and random.random() > 0.7:  # 30% chance
                param_type = tool_spec["types"][param]
                params[param] = self._generate_default_param(param, param_type)
        
        return params
    
    def _extract_param_from_text(self, text: str, param: str, param_type: str) -> Any:
        """Try to extract a parameter value from text"""
        # Simple regex patterns for common parameters
        patterns = {
            "file_path": r'["\']?([/\w\-_\.]+\.\w+)["\']?',
            "pattern": r'["\']([^"\']+)["\']',
            "message": r'["\']([^"\']+)["\']',
            "command": r'`([^`]+)`',
        }
        
        if param in patterns:
            match = re.search(patterns[param], text)
            if match:
                value = match.group(1)
                # Cast to correct type
                if param_type == "int":
                    try:
                        return int(value)
                    except ValueError:
                        pass
                elif param_type == "bool":
                    return value.lower() in ["true", "yes", "1"]
                return value
        
        return None
    
    def _generate_default_param(self, param: str, param_type: str) -> Any:
        """Generate a default parameter value based on type"""
        defaults = {
            "str": {
                "file_path": "src/main.py",
                "content": "# Generated content",
                "pattern": "TODO",
                "message": "Auto-generated commit",
                "command": "echo 'test'",
                "encoding": "utf-8"
            },
            "int": {
                "start_line": 1,
                "end_line": 100,
                "max_results": 10,
                "timeout": 30
            },
            "bool": {
                "recursive": True,
                "force": False,
                "case_sensitive": True,
                "create_dirs": True
            },
            "list": [],
            "dict": {}
        }
        
        if param_type in defaults:
            if isinstance(defaults[param_type], dict) and param in defaults[param_type]:
                return defaults[param_type][param]
            elif not isinstance(defaults[param_type], dict):
                return defaults[param_type]
        
        # Ultimate fallback
        if param_type == "str":
            return f"default_{param}"
        elif param_type == "int":
            return 1
        elif param_type == "bool":
            return False
        elif param_type == "list":
            return []
        else:
            return {}
    
    def _simulate_output(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Simulate realistic output for a tool call"""
        outputs = {
            "read_file": lambda p: f"File contents of {p.get('file_path', 'unknown')}:\n[file content here]",
            "write_file": lambda p: f"Successfully wrote {len(p.get('content', ''))} bytes to {p.get('file_path', 'unknown')}",
            "search_files": lambda p: [
                f"Found in file1.py:10: {p.get('pattern', 'match')}",
                f"Found in file2.py:25: {p.get('pattern', 'match')}"
            ],
            "generate_function": lambda p: f"def generated_function():\n    # Implementation for: {p.get('description', 'task')}\n    pass",
            "run_command": lambda p: f"Command output: [stdout from {p.get('command', 'cmd')}]",
            "git_commit": lambda p: f"Committed with hash: {hashlib.md5(str(p).encode()).hexdigest()[:8]}"
        }
        
        if tool_name in outputs:
            return outputs[tool_name](params)
        
        return f"Success: {tool_name} completed"
    
    def _generate_reasoning(self, user_input: str, tool_name: str) -> str:
        """Generate reasoning for why this tool was selected"""
        templates = [
            f"Based on the request '{user_input[:50]}...', {tool_name} is the appropriate tool",
            f"User wants to {tool_name.replace('_', ' ')}, which requires the {tool_name} tool",
            f"Analyzing the input, the intent is to {tool_name.replace('_', ' ')}",
            f"The {tool_name} tool matches the user's request for this operation"
        ]
        
        return random.choice(templates)
    
    def _generate_alternatives(self, step: Dict, probability: float) -> List[Tuple[str, Dict, float]]:
        """Generate alternative tool choices with confidence scores"""
        if random.random() > probability:
            return []
        
        alternatives = []
        # Generate 1-3 alternatives
        num_alts = random.randint(1, 3)
        
        for _ in range(num_alts):
            # Pick a related tool
            alt_tool = self._get_related_tool(step["tool"])
            if alt_tool:
                alt_params = self._modify_params(step["params"])
                confidence = 0.5 + random.random() * 0.3  # 50-80% confidence
                alternatives.append((alt_tool, alt_params, confidence))
        
        return alternatives
    
    def _get_related_tool(self, tool: str) -> Optional[str]:
        """Get a related/similar tool"""
        related = {
            "read_file": ["search_files", "analyze_code"],
            "write_file": ["edit_file", "create_file"],
            "generate_function": ["refactor_code", "write_tests"],
            "git_commit": ["git_add", "git_push"],
            "run_command": ["install_package", "execute_script"]
        }
        
        if tool in related:
            return random.choice(related[tool])
        return None
    
    def _modify_params(self, params: Dict) -> Dict:
        """Slightly modify parameters"""
        modified = params.copy()
        # Randomly modify one parameter
        if modified and random.random() > 0.5:
            key = random.choice(list(modified.keys()))
            if isinstance(modified[key], str):
                modified[key] = modified[key] + "_modified"
            elif isinstance(modified[key], int):
                modified[key] += random.randint(-5, 5)
        return modified
    
    def _generate_workflow(self, num_tools: int, complexity: ComplexityLevel) -> Dict[str, Any]:
        """Generate a coherent multi-tool workflow"""
        workflows = {
            "feature_implementation": {
                "user_input": "Create a new user authentication feature with tests",
                "intent": "implement_feature",
                "type": "feature",
                "steps": [
                    {
                        "category": "code_operations",
                        "tool": "generate_function",
                        "params": {"description": "authenticate user", "language": "python"},
                        "reasoning": "First, generate the authentication function"
                    },
                    {
                        "category": "code_operations",
                        "tool": "write_tests",
                        "params": {"code": "[generated code]", "test_framework": "pytest"},
                        "reasoning": "Write tests for the authentication function"
                    },
                    {
                        "category": "file_operations",
                        "tool": "write_file",
                        "params": {"file_path": "auth/authenticate.py", "content": "[generated]"},
                        "reasoning": "Save the implementation to a file"
                    }
                ]
            },
            "bug_fix": {
                "user_input": "Fix the TypeError in user.py and update tests",
                "intent": "fix_bug",
                "type": "bugfix",
                "steps": [
                    {
                        "category": "file_operations",
                        "tool": "read_file",
                        "params": {"file_path": "user.py"},
                        "reasoning": "Read the file to understand the error"
                    },
                    {
                        "category": "code_operations",
                        "tool": "debug_code",
                        "params": {"code": "[file content]", "error": "TypeError"},
                        "reasoning": "Identify and fix the TypeError"
                    },
                    {
                        "category": "file_operations",
                        "tool": "edit_file",
                        "params": {"file_path": "user.py", "old_content": "[buggy]", "new_content": "[fixed]"},
                        "reasoning": "Apply the fix to the file"
                    }
                ]
            }
        }
        
        # Select or generate a workflow
        workflow_type = random.choice(list(workflows.keys()))
        base_workflow = workflows[workflow_type].copy()
        
        # Adjust to match requested number of tools
        while len(base_workflow["steps"]) < num_tools:
            # Add more steps
            base_workflow["steps"].append(self._generate_workflow_step())
        
        base_workflow["steps"] = base_workflow["steps"][:num_tools]
        
        return base_workflow
    
    def _generate_workflow_step(self) -> Dict[str, Any]:
        """Generate a single workflow step"""
        category = random.choice(list(TOOL_TAXONOMY.keys()))
        tool = random.choice(list(TOOL_TAXONOMY[category].keys()))
        
        return {
            "category": category,
            "tool": tool,
            "params": self._generate_realistic_params(category, tool),
            "reasoning": f"Execute {tool} as part of the workflow"
        }
    
    def _generate_dependencies(self, workflow: Dict, num_tools: int) -> Dict[int, List[int]]:
        """Generate dependencies between tools"""
        dependencies = {}
        
        # Linear dependencies for simple workflows
        if workflow.get("type") == "linear":
            for i in range(1, num_tools):
                dependencies[i] = [i - 1]
        else:
            # More complex dependencies
            for i in range(num_tools):
                deps = []
                # Add dependency on previous tool with 70% probability
                if i > 0 and random.random() > 0.3:
                    deps.append(i - 1)
                # Add dependency on earlier tool with 30% probability
                if i > 1 and random.random() > 0.7:
                    deps.append(random.randint(0, i - 2))
                
                if deps:
                    dependencies[i] = list(set(deps))
        
        return dependencies
    
    def _generate_complex_scenario(self) -> Dict[str, Any]:
        """Generate a complex multi-step scenario"""
        scenarios = [
            self._generate_refactoring_scenario(),
            self._generate_feature_scenario(),
            self._generate_debugging_scenario(),
            self._generate_deployment_scenario()
        ]
        
        return random.choice(scenarios)
    
    def _generate_refactoring_scenario(self) -> Dict[str, Any]:
        """Generate a code refactoring scenario"""
        return {
            "user_input": "Refactor the user service to use async/await and add proper error handling",
            "intent": "refactor_service",
            "type": "refactoring",
            "steps": [
                {
                    "category": "file_operations",
                    "tool": "search_files",
                    "params": {"pattern": "class UserService", "file_type": "py"},
                    "reasoning": "Find the user service implementation"
                },
                {
                    "category": "file_operations",
                    "tool": "read_file",
                    "params": {"file_path": "services/user_service.py"},
                    "reasoning": "Read the current implementation"
                },
                {
                    "category": "code_operations",
                    "tool": "analyze_code",
                    "params": {"code": "[content]", "analysis_type": "async_compatibility"},
                    "reasoning": "Analyze what needs to be converted to async"
                },
                {
                    "category": "code_operations",
                    "tool": "refactor_code",
                    "params": {"code": "[content]", "refactor_type": "async_conversion"},
                    "reasoning": "Convert synchronous code to async/await"
                },
                {
                    "category": "code_operations",
                    "tool": "generate_function",
                    "params": {"description": "error handler for async operations"},
                    "reasoning": "Generate proper error handling code"
                },
                {
                    "category": "file_operations",
                    "tool": "write_file",
                    "params": {"file_path": "services/user_service.py", "content": "[refactored]"},
                    "reasoning": "Save the refactored code"
                },
                {
                    "category": "code_operations",
                    "tool": "write_tests",
                    "params": {"code": "[refactored]", "test_framework": "pytest-asyncio"},
                    "reasoning": "Update tests for async code"
                }
            ],
            "dependencies": {
                1: [0],
                2: [1],
                3: [2],
                4: [2],
                5: [3, 4],
                6: [5]
            },
            "expected_output": "Refactored user service with async/await and error handling"
        }
    
    def _generate_feature_scenario(self) -> Dict[str, Any]:
        """Generate a feature implementation scenario"""
        return {
            "user_input": "Implement a rate limiting feature for the API with Redis backend",
            "intent": "implement_rate_limiting",
            "type": "feature",
            "steps": [
                {
                    "category": "system_operations",
                    "tool": "install_package",
                    "params": {"package": "redis", "manager": "pip"},
                    "reasoning": "Install Redis client library"
                },
                {
                    "category": "code_operations",
                    "tool": "generate_function",
                    "params": {"description": "rate limiter with Redis", "language": "python"},
                    "reasoning": "Generate rate limiting logic"
                },
                {
                    "category": "code_operations",
                    "tool": "generate_function",
                    "params": {"description": "rate limit decorator", "language": "python"},
                    "reasoning": "Create a decorator for easy application"
                },
                {
                    "category": "file_operations",
                    "tool": "write_file",
                    "params": {"file_path": "middleware/rate_limiter.py", "content": "[generated]"},
                    "reasoning": "Save the rate limiter implementation"
                },
                {
                    "category": "file_operations",
                    "tool": "search_files",
                    "params": {"pattern": "@app.route", "file_type": "py"},
                    "reasoning": "Find API endpoints to apply rate limiting"
                },
                {
                    "category": "file_operations",
                    "tool": "edit_file",
                    "params": {"file_path": "api/endpoints.py", "old_content": "@app.route", "new_content": "@rate_limit\\n@app.route"},
                    "reasoning": "Apply rate limiting to endpoints"
                }
            ],
            "dependencies": {
                1: [0],
                2: [0],
                3: [1, 2],
                4: [1],
                5: [3, 4]
            },
            "expected_output": "Rate limiting feature implemented with Redis backend",
            "parallel": True
        }
    
    def _generate_debugging_scenario(self) -> Dict[str, Any]:
        """Generate a debugging scenario"""
        return {
            "user_input": "Debug and fix the memory leak in the data processing pipeline",
            "intent": "debug_memory_leak",
            "type": "debugging",
            "steps": [
                {
                    "category": "system_operations",
                    "tool": "run_command",
                    "params": {"command": "python", "args": ["-m", "memory_profiler", "pipeline.py"]},
                    "reasoning": "Profile memory usage to identify the leak"
                },
                {
                    "category": "file_operations",
                    "tool": "read_file",
                    "params": {"file_path": "pipeline.py"},
                    "reasoning": "Read the pipeline code"
                },
                {
                    "category": "code_operations",
                    "tool": "analyze_code",
                    "params": {"code": "[content]", "analysis_type": "memory_analysis"},
                    "reasoning": "Analyze code for memory leak patterns"
                },
                {
                    "category": "code_operations",
                    "tool": "debug_code",
                    "params": {"code": "[content]", "error": "MemoryError"},
                    "reasoning": "Identify the source of the memory leak"
                },
                {
                    "category": "code_operations",
                    "tool": "refactor_code",
                    "params": {"code": "[problematic_section]", "refactor_type": "memory_optimization"},
                    "reasoning": "Fix the memory leak"
                },
                {
                    "category": "file_operations",
                    "tool": "edit_file",
                    "params": {"file_path": "pipeline.py", "old_content": "[leak]", "new_content": "[fixed]"},
                    "reasoning": "Apply the fix"
                },
                {
                    "category": "system_operations",
                    "tool": "run_command",
                    "params": {"command": "python", "args": ["-m", "memory_profiler", "pipeline.py"]},
                    "reasoning": "Verify the fix by re-profiling"
                }
            ],
            "dependencies": {
                1: [0],
                2: [0],
                3: [1, 2],
                4: [3],
                5: [4],
                6: [5]
            },
            "expected_output": "Memory leak fixed and verified"
        }
    
    def _generate_deployment_scenario(self) -> Dict[str, Any]:
        """Generate a deployment scenario"""
        return {
            "user_input": "Deploy the application to production with zero downtime",
            "intent": "deploy_production",
            "type": "deployment",
            "steps": [
                {
                    "category": "code_operations",
                    "tool": "write_tests",
                    "params": {"code": "[app_code]", "test_framework": "pytest"},
                    "reasoning": "Ensure all tests pass before deployment"
                },
                {
                    "category": "system_operations",
                    "tool": "run_command",
                    "params": {"command": "pytest", "args": ["--cov=app"]},
                    "reasoning": "Run test suite with coverage"
                },
                {
                    "category": "git_operations",
                    "tool": "git_commit",
                    "params": {"message": "Release v2.0.0", "files": ["*"]},
                    "reasoning": "Commit all changes"
                },
                {
                    "category": "git_operations",
                    "tool": "git_branch",
                    "params": {"action": "create", "branch_name": "release/v2.0.0"},
                    "reasoning": "Create release branch"
                },
                {
                    "category": "system_operations",
                    "tool": "run_command",
                    "params": {"command": "docker", "args": ["build", "-t", "app:v2.0.0", "."]},
                    "reasoning": "Build Docker image"
                },
                {
                    "category": "system_operations",
                    "tool": "run_command",
                    "params": {"command": "kubectl", "args": ["set", "image", "deployment/app", "app=app:v2.0.0"]},
                    "reasoning": "Deploy using rolling update"
                }
            ],
            "dependencies": {
                1: [0],
                2: [1],
                3: [2],
                4: [3],
                5: [4]
            },
            "expected_output": "Application deployed to production with zero downtime"
        }
    
    def _generate_expert_scenario(self) -> Dict[str, Any]:
        """Generate an expert-level scenario with error recovery"""
        base_scenario = self._generate_complex_scenario()
        
        # Add error handling and recovery strategies
        base_scenario["recovery_strategies"] = [
            "retry_with_exponential_backoff",
            "fallback_to_alternative_tool",
            "rollback_on_failure",
            "graceful_degradation"
        ]
        
        # Add error scenarios to some steps
        for i, step in enumerate(base_scenario["steps"]):
            if random.random() > 0.7:  # 30% chance of error
                step["error_handling"] = {
                    "potential_error": random.choice([
                        "FileNotFoundError",
                        "PermissionError",
                        "NetworkError",
                        "TimeoutError",
                        "ValidationError"
                    ]),
                    "recovery_action": random.choice([
                        "retry",
                        "use_alternative",
                        "create_missing_resource",
                        "request_user_input",
                        "skip_and_continue"
                    ]),
                    "max_retries": random.randint(1, 3)
                }
        
        # Add complex execution order (parallel + sequential)
        base_scenario["execution_order"] = self._generate_complex_execution_order(
            len(base_scenario["steps"]),
            base_scenario["dependencies"]
        )
        
        return base_scenario
    
    def _generate_complex_execution_order(self, num_steps: int, dependencies: Dict) -> List[int]:
        """Generate execution order considering parallelism"""
        # Topological sort with parallelism detection
        return self._topological_sort(dependencies, num_steps)
    
    def _topological_sort(self, dependencies: Dict[int, List[int]], num_nodes: int) -> List[int]:
        """Perform topological sort on dependencies"""
        # Calculate in-degree for each node
        in_degree = [0] * num_nodes
        for deps in dependencies.values():
            for dep in deps:
                if dep < num_nodes:
                    in_degree[dep] += 1
        
        # Find nodes with no dependencies
        queue = [i for i in range(num_nodes) if in_degree[i] == 0]
        result = []
        
        while queue:
            # Process nodes that can run in parallel
            parallel_batch = queue[:]
            queue = []
            
            for node in parallel_batch:
                result.append(node)
                
                # Reduce in-degree for dependent nodes
                for i, deps in dependencies.items():
                    if node in deps and i < num_nodes:
                        in_degree[i] -= 1
                        if in_degree[i] == 0:
                            queue.append(i)
        
        return result if len(result) == num_nodes else list(range(num_nodes))
    
    def _combine_outputs(self, tool_calls: List[ToolCall]) -> Any:
        """Combine outputs from multiple tool calls"""
        if len(tool_calls) == 1:
            return tool_calls[0].expected_output
        
        # Combine as list or structured output
        return {
            "combined_output": [tc.expected_output for tc in tool_calls],
            "success": True,
            "tools_executed": len(tool_calls)
        }
    
    def _extract_intent(self, user_input: str) -> str:
        """Extract high-level intent from user input"""
        # Simple keyword-based intent extraction
        intents = {
            "create": ["create", "make", "generate", "build"],
            "read": ["read", "show", "display", "get", "fetch"],
            "update": ["update", "modify", "edit", "change", "refactor"],
            "delete": ["delete", "remove", "clean", "clear"],
            "analyze": ["analyze", "check", "inspect", "review"],
            "execute": ["run", "execute", "perform", "do"],
            "search": ["search", "find", "look", "locate"],
            "debug": ["debug", "fix", "solve", "troubleshoot"],
            "deploy": ["deploy", "release", "publish", "ship"],
            "test": ["test", "verify", "validate", "check"]
        }
        
        lower_input = user_input.lower()
        for intent, keywords in intents.items():
            for keyword in keywords:
                if keyword in lower_input:
                    return intent
        
        return "general"
    
    def _generate_id(self) -> str:
        """Generate unique ID for training example"""
        timestamp = datetime.now().timestamp()
        random_part = random.randint(1000000, 9999999)
        return f"ex_{int(timestamp)}_{random_part}"
    
    def _load_templates(self) -> Dict:
        """Load input templates for variety"""
        # In production, load from files
        return {}
    
    def _load_patterns(self) -> Dict:
        """Load common patterns for generation"""
        # In production, load from files
        return {}
    
    def _split_dataset(self, examples: List[TrainingExample], 
                      train_ratio: float = 0.8,
                      val_ratio: float = 0.1,
                      test_ratio: float = 0.1) -> Dict[str, List[TrainingExample]]:
        """Split dataset into train/val/test"""
        n = len(examples)
        train_size = int(n * train_ratio)
        val_size = int(n * val_ratio)
        
        return {
            "train": examples[:train_size],
            "validation": examples[train_size:train_size + val_size],
            "test": examples[train_size + val_size:]
        }
    
    async def _save_checkpoint(self, examples: List[TrainingExample]):
        """Save intermediate checkpoint"""
        checkpoint_path = self.output_dir / f"checkpoint_{len(examples)}.jsonl"
        
        with open(checkpoint_path, "w") as f:
            for example in examples:
                f.write(json.dumps(asdict(example)) + "\n")
        
        logger.info(f"Checkpoint saved: {checkpoint_path}")
    
    async def _save_dataset(self, dataset: Dict[str, List[TrainingExample]]) -> str:
        """Save final dataset"""
        dataset_dir = self.output_dir / "final_dataset"
        dataset_dir.mkdir(exist_ok=True)
        
        for split_name, examples in dataset.items():
            split_path = dataset_dir / f"{split_name}.jsonl"
            
            with open(split_path, "w") as f:
                for example in examples:
                    f.write(json.dumps(asdict(example)) + "\n")
            
            logger.info(f"Saved {split_name}: {len(examples)} examples to {split_path}")
        
        # Save metadata
        metadata = {
            "total_examples": sum(len(ex) for ex in dataset.values()),
            "splits": {k: len(v) for k, v in dataset.items()},
            "statistics": self.stats,
            "generated_at": datetime.now().isoformat()
        }
        
        metadata_path = dataset_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        return str(dataset_dir)
    
    def _generate_report(self, dataset: Dict[str, List[TrainingExample]]):
        """Generate detailed statistics report"""
        report = []
        report.append("=" * 80)
        report.append("DATASET GENERATION REPORT")
        report.append("=" * 80)
        report.append(f"\nGenerated at: {datetime.now().isoformat()}")
        report.append(f"Total examples: {self.stats['total_generated']:,}")
        
        report.append("\nComplexity Distribution:")
        for level, count in self.stats["by_complexity"].items():
            percentage = (count / self.stats["total_generated"]) * 100
            report.append(f"  {level:10} {count:8,} ({percentage:5.1f}%)")
        
        report.append("\nDataset Splits:")
        for split, examples in dataset.items():
            report.append(f"  {split:10} {len(examples):8,} examples")
        
        report.append("\nTool Category Distribution:")
        category_counts = {}
        for split_examples in dataset.values():
            for ex in split_examples:
                for tool_call in ex.tool_calls:
                    category_counts[tool_call.tool_category] = category_counts.get(tool_call.tool_category, 0) + 1
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {category:20} {count:8,}")
        
        report.append("\n" + "=" * 80)
        
        report_path = self.output_dir / "generation_report.txt"
        with open(report_path, "w") as f:
            f.write("\n".join(report))
        
        logger.info(f"Report saved to {report_path}")
        print("\n".join(report))


async def main():
    """Generate the complete training dataset"""
    generator = DataGenerator()
    
    # Generate 1M examples
    dataset_path = await generator.generate_dataset(
        num_examples=1_000_000,
        complexity_distribution={
            "SIMPLE": 0.4,      # 400,000
            "MODERATE": 0.35,   # 350,000  
            "COMPLEX": 0.2,     # 200,000
            "EXPERT": 0.05      # 50,000
        }
    )
    
    print(f"\n✓ Dataset generated successfully: {dataset_path}")
    print(f"Ready for training on A100 GPU!")


if __name__ == "__main__":
    asyncio.run(main())