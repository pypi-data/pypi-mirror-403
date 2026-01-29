#!/usr/bin/env python3
"""
NC1709 Enhanced CLI - Combining NC1709 with ECHO's advanced features
Integrates local LLM optimization, cognitive architecture, and performance benchmarking
"""

import asyncio
import click
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
import logging
from typing import Optional, Dict, Any
import json

# Import NC1709 core components
try:
    from .cli import NC1709CLI
    from .llm_adapter import LLMAdapter
    from .reasoning_engine import ReasoningEngine
    from .task_classifier import TaskClassifier
except ImportError:
    # Fallback for development
    pass

# Import ECHO enhanced components
from .models.local_llm_v2 import LocalLLMAdapter, TaskCategory
from .cognitive.system import CognitiveSystem
from .performance.benchmark import Benchmark

# Setup console and logging
console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom style for the prompt
prompt_style = Style.from_dict({
    'prompt': '#00aa00 bold',
    'nc1709': '#0087ff bold',
    'echo': '#ff6b6b bold',
})

class NC1709Enhanced:
    """Enhanced NC1709 CLI with ECHO's advanced features"""
    
    def __init__(self, mode: str = "hybrid"):
        """
        Initialize enhanced CLI
        
        Args:
            mode: "local" for local-only, "remote" for remote-only, "hybrid" for both
        """
        self.mode = mode
        self.session = PromptSession(style=prompt_style)
        self.console = Console()
        
        # Initialize components based on mode
        if mode in ["local", "hybrid"]:
            self.local_llm = LocalLLMAdapter()
            self.cognitive_system = CognitiveSystem(self.local_llm)
            self.benchmark = Benchmark(self.local_llm)
        
        if mode in ["remote", "hybrid"]:
            # Initialize original NC1709 components
            self.remote_adapter = None  # Will be initialized when needed
        
        self.history = []
        self.session_stats = {
            "requests": 0,
            "local_requests": 0,
            "remote_requests": 0,
            "avg_response_time": 0,
            "total_tokens": 0
        }
    
    async def process_request(self, prompt: str) -> str:
        """Process a user request with intelligent routing"""
        
        self.session_stats["requests"] += 1
        
        # Classify the task
        complexity = self.estimate_complexity(prompt)
        category = self.classify_task(prompt)
        
        # Show routing decision
        self.console.print(f"[dim]Task: {category.value}, Complexity: {complexity:.2f}[/dim]")
        
        # Route based on mode and complexity
        if self.mode == "local" or (self.mode == "hybrid" and complexity < 0.7):
            return await self.process_local(prompt, category, complexity)
        elif self.mode == "remote" or (self.mode == "hybrid" and complexity >= 0.7):
            return await self.process_remote(prompt)
        
    async def process_local(self, prompt: str, category: TaskCategory, complexity: float) -> str:
        """Process request using local models with cognitive enhancement"""
        
        self.session_stats["local_requests"] += 1
        
        # Use cognitive system for complex requests
        if complexity > 0.5:
            self.console.print("[dim]Engaging cognitive system...[/dim]")
            response = await self.cognitive_system.process(prompt)
            return response.content
        else:
            # Direct local LLM processing
            response = await self.local_llm.complete(prompt, category=category)
            return response
    
    async def process_remote(self, prompt: str) -> str:
        """Process request using remote models (original NC1709)"""
        
        self.session_stats["remote_requests"] += 1
        
        # This would connect to the original NC1709 server
        # For now, return a placeholder
        return "Remote processing not yet implemented. Please use local mode."
    
    def estimate_complexity(self, prompt: str) -> float:
        """Estimate task complexity (0.0-1.0)"""
        
        factors = {
            "length": min(len(prompt) / 500, 1.0) * 0.2,
            "code_indicators": 0.3 if any(kw in prompt.lower() for kw in 
                ["implement", "create", "build", "refactor", "optimize"]) else 0,
            "analysis_indicators": 0.2 if any(kw in prompt.lower() for kw in 
                ["analyze", "explain", "compare", "evaluate"]) else 0,
            "multi_step": 0.2 if any(kw in prompt.lower() for kw in 
                ["first", "then", "finally", "step", "stages"]) else 0,
            "technical_depth": 0.1 if any(kw in prompt.lower() for kw in 
                ["algorithm", "architecture", "pattern", "framework"]) else 0
        }
        
        return sum(factors.values())
    
    def classify_task(self, prompt: str) -> TaskCategory:
        """Classify the task type"""
        
        prompt_lower = prompt.lower()
        
        if any(kw in prompt_lower for kw in ["code", "implement", "function", "class", "debug"]):
            return TaskCategory.CODE_GENERATION
        elif any(kw in prompt_lower for kw in ["analyze", "review", "explain", "understand"]):
            return TaskCategory.CODE_ANALYSIS
        elif any(kw in prompt_lower for kw in ["chat", "tell", "what", "who", "when"]):
            return TaskCategory.GENERAL_CHAT
        elif any(kw in prompt_lower for kw in ["reason", "think", "solve", "figure"]):
            return TaskCategory.REASONING
        else:
            return TaskCategory.GENERAL_CHAT
    
    async def run_benchmark(self):
        """Run performance benchmark"""
        
        self.console.print("\n[bold cyan]Running Performance Benchmark...[/bold cyan]\n")
        results = await self.benchmark.run_suite()
        
        # Display results
        table = Table(title="Benchmark Results")
        table.add_column("Task", style="cyan")
        table.add_column("Model", style="magenta")
        table.add_column("Time (s)", style="yellow")
        table.add_column("Tokens/s", style="green")
        
        for result in results.results:
            table.add_row(
                result.task_name,
                result.model,
                f"{result.total_time:.2f}",
                f"{result.tokens_per_second:.1f}"
            )
        
        self.console.print(table)
        
        if results.summary:
            self.console.print(f"\n[bold]Summary:[/bold] {results.summary}")
    
    async def interactive_shell(self):
        """Run the interactive shell"""
        
        # Display welcome banner
        welcome = Panel.fit(
            "[bold cyan]NC1709 Enhanced[/bold cyan] - Advanced AI Assistant\n"
            "[dim]Combining NC1709 with ECHO's cognitive architecture[/dim]\n\n"
            f"Mode: [bold yellow]{self.mode}[/bold yellow] | "
            "Type [bold green]/help[/bold green] for commands, [bold red]/exit[/bold red] to quit",
            title="Welcome",
            border_style="cyan"
        )
        self.console.print(welcome)
        
        while True:
            try:
                # Get user input
                user_input = await self.session.prompt_async(
                    HTML('<nc1709>nc1709</nc1709> <prompt>▶</prompt> ')
                )
                
                if not user_input.strip():
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    await self.handle_command(user_input)
                    continue
                
                # Process the request
                self.console.print("[dim]Processing...[/dim]")
                response = await self.process_request(user_input)
                
                # Display response
                self.console.print("\n" + Markdown(response) + "\n")
                
                # Update history
                self.history.append({"prompt": user_input, "response": response})
                
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
    
    async def handle_command(self, command: str):
        """Handle slash commands"""
        
        cmd = command.lower().strip()
        
        if cmd == "/exit" or cmd == "/quit":
            self.console.print("[yellow]Goodbye![/yellow]")
            sys.exit(0)
        elif cmd == "/help":
            help_text = """
[bold cyan]Available Commands:[/bold cyan]

[bold]/help[/bold]       - Show this help message
[bold]/exit[/bold]       - Exit the application
[bold]/stats[/bold]      - Show session statistics
[bold]/benchmark[/bold]  - Run performance benchmark
[bold]/mode[/bold]       - Switch between local/remote/hybrid modes
[bold]/history[/bold]    - Show conversation history
[bold]/clear[/bold]      - Clear conversation history
[bold]/models[/bold]     - Show available models
"""
            self.console.print(help_text)
        elif cmd == "/stats":
            self.show_statistics()
        elif cmd == "/benchmark":
            await self.run_benchmark()
        elif cmd.startswith("/mode"):
            parts = cmd.split()
            if len(parts) > 1 and parts[1] in ["local", "remote", "hybrid"]:
                self.mode = parts[1]
                self.console.print(f"[green]Mode switched to: {self.mode}[/green]")
            else:
                self.console.print(f"Current mode: [yellow]{self.mode}[/yellow]")
                self.console.print("Usage: /mode [local|remote|hybrid]")
        elif cmd == "/history":
            for i, item in enumerate(self.history[-10:], 1):
                self.console.print(f"\n[bold]#{i}[/bold] {item['prompt'][:50]}...")
        elif cmd == "/clear":
            self.history = []
            self.console.print("[green]History cleared[/green]")
        elif cmd == "/models":
            self.show_available_models()
        else:
            self.console.print(f"[red]Unknown command: {command}[/red]")
    
    def show_statistics(self):
        """Display session statistics"""
        
        stats_panel = Panel.fit(
            f"[bold]Session Statistics[/bold]\n\n"
            f"Total Requests: {self.session_stats['requests']}\n"
            f"Local Requests: {self.session_stats['local_requests']}\n"
            f"Remote Requests: {self.session_stats['remote_requests']}\n"
            f"Avg Response Time: {self.session_stats['avg_response_time']:.2f}s\n"
            f"Total Tokens: {self.session_stats['total_tokens']:,}",
            title="Statistics",
            border_style="yellow"
        )
        self.console.print(stats_panel)
    
    def show_available_models(self):
        """Show available models"""
        
        if hasattr(self, 'local_llm'):
            table = Table(title="Available Local Models")
            table.add_column("Model", style="cyan")
            table.add_column("Tier", style="magenta")
            table.add_column("Speed", style="yellow")
            table.add_column("Context", style="green")
            
            for model_name, config in self.local_llm.models.items():
                table.add_row(
                    model_name,
                    config.tier,
                    config.speed,
                    f"{config.context_window}"
                )
            
            self.console.print(table)
        else:
            self.console.print("[yellow]No local models available in current mode[/yellow]")

@click.command()
@click.option('--mode', '-m', 
              type=click.Choice(['local', 'remote', 'hybrid']),
              default='local',
              help='Operation mode')
@click.option('--benchmark', '-b', is_flag=True, 
              help='Run benchmark on startup')
def main(mode: str, benchmark: bool):
    """NC1709 Enhanced - Advanced AI Assistant"""
    
    cli = NC1709Enhanced(mode=mode)
    
    async def run():
        if benchmark:
            await cli.run_benchmark()
        await cli.interactive_shell()
    
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()