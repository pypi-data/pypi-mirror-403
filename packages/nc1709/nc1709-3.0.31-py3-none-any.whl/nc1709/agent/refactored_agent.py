"""
Refactored Agent Core
Modular agent implementation using component architecture
"""

import re
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from enum import Enum

# Import components
from .components import (
    LLMInterface, ToolExecutor, PermissionManager, 
    LoopDetector, ResponseFormatter, HistoryTracker
)

# Import base classes
from .tools.base import Tool, ToolResult, ToolRegistry, get_default_registry
from .core import AgentConfig, ToolCall, AgentState

# Import CLI UI if available
try:
    from ..cli_ui import status, thinking, success, error, warning, info
    HAS_CLI_UI = True
except ImportError:
    HAS_CLI_UI = False


class ModularAgent:
    """
    Refactored Agent using component architecture
    
    This replaces the monolithic 728-line Agent class with a modular design
    that separates concerns into focused components.
    """
    
    def __init__(
        self,
        llm: Optional[Callable] = None,
        tool_registry: Optional[ToolRegistry] = None,
        config: Optional[AgentConfig] = None,
        **config_kwargs
    ):
        # Setup configuration
        if config is None:
            config = AgentConfig(llm=llm, **config_kwargs)
        self.config = config
        
        # Initialize tool registry
        if tool_registry is None:
            tool_registry = self._create_default_registry()
        self.tool_registry = tool_registry
        
        # Initialize components
        self.llm_interface = LLMInterface(config)
        self.tool_executor = ToolExecutor(tool_registry, config)
        self.permission_manager = PermissionManager(config)
        self.loop_detector = LoopDetector(max_history=config.max_history)
        self.response_formatter = ResponseFormatter(max_output_length=config.max_output_length)
        self.history_tracker = HistoryTracker(max_history=config.max_history)
        
        # Agent state
        self.state = AgentState.IDLE
        self.iteration_count = 0
        
    def _create_default_registry(self) -> ToolRegistry:
        """Create default tool registry with all available tools"""
        from .tools.file_tools import register_file_tools
        from .tools.search_tools import register_search_tools
        from .tools.bash_tool import register_bash_tools
        from .tools.task_tool import register_task_tools
        from .tools.web_tools import register_web_tools
        from .tools.notebook_tools import register_notebook_tools
        
        registry = get_default_registry()
        register_file_tools(registry)
        register_search_tools(registry)
        register_bash_tools(registry)
        register_task_tools(registry)
        register_web_tools(registry)
        register_notebook_tools(registry)
        
        return registry
    
    def run(self, user_request: str) -> str:
        """
        Main execution loop - simplified and focused
        """
        if HAS_CLI_UI:
            status(f"Processing request: {user_request[:100]}...")
        
        self.state = AgentState.THINKING
        self.iteration_count = 0
        context_messages = []
        
        try:
            while self.iteration_count < self.config.max_iterations:
                self.iteration_count += 1
                
                if HAS_CLI_UI:
                    thinking(f"Iteration {self.iteration_count}")
                
                # Get LLM response
                context = "\n".join(context_messages) if context_messages else ""
                llm_response = self.llm_interface.get_response(user_request, context)
                
                # Parse tool calls
                tool_calls = self._parse_tool_calls(llm_response.content)
                
                if not tool_calls:
                    # No tools to execute, return the response
                    final_response = self.response_formatter.clean_llm_response(llm_response.content)
                    self.state = AgentState.IDLE
                    
                    if HAS_CLI_UI:
                        success(f"Completed in {self.iteration_count} iteration(s)")
                    
                    return final_response
                
                # Execute tool calls
                execution_results = self._execute_tools(tool_calls)
                
                # Format results for context
                tool_results = [result.result for result in execution_results if result.success and result.result]
                formatted_results = self.response_formatter.format_tool_results(tool_results)
                context_messages.append(f"Tool Results:\n{formatted_results.content}")
                
                # Check if we should continue
                if self._should_stop_execution(execution_results):
                    break
            
            # Generate final response
            final_context = "\n".join(context_messages)
            final_llm_response = self.llm_interface.get_response(
                "Please provide a final summary of what was accomplished.", 
                final_context
            )
            
            final_response = self.response_formatter.clean_llm_response(final_llm_response.content)
            self.state = AgentState.IDLE
            
            if HAS_CLI_UI:
                success(f"Completed after {self.iteration_count} iterations")
            
            return final_response
            
        except Exception as e:
            self.state = AgentState.IDLE
            error_response = self.response_formatter.format_error_response(str(e))
            
            if HAS_CLI_UI:
                error(f"Agent execution failed: {e}")
            
            return error_response
    
    def _parse_tool_calls(self, response: str) -> List[ToolCall]:
        """Parse tool calls from LLM response"""
        tool_calls = []
        
        # Pattern to match tool calls: <tool_name>...parameters...</tool_name>
        pattern = r'<(\w+)>(.*?)</\1>'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for tool_name, params_text in matches:
            # Parse parameters
            parameters = {}
            
            # Simple parameter parsing (key: value)
            param_lines = params_text.strip().split('\n')
            for line in param_lines:
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Try to parse as JSON for complex values
                    try:
                        if value.startswith('{') or value.startswith('[') or value.startswith('"'):
                            value = json.loads(value)
                    except json.JSONDecodeError:
                        pass  # Keep as string
                    
                    parameters[key] = value
            
            if tool_name and parameters:
                tool_calls.append(ToolCall(tool_name=tool_name, parameters=parameters))
        
        return tool_calls
    
    def _execute_tools(self, tool_calls: List[ToolCall]) -> List:
        """Execute tools with comprehensive checking"""
        results = []
        
        for tool_call in tool_calls:
            # Check for loops
            loop_result = self.loop_detector.check_for_loops(tool_call)
            if loop_result.is_loop:
                if HAS_CLI_UI:
                    warning(f"Loop detected: {loop_result.message}")
                # Skip this execution
                continue
            
            # Check permissions
            permission_check = self.permission_manager.check_permission(tool_call)
            if not permission_check.granted:
                if HAS_CLI_UI:
                    warning(f"Permission denied: {permission_check.message}")
                continue
            
            # Execute tool
            start_time = time.time()
            execution_result = self.tool_executor.execute_tool_call(tool_call)
            duration = time.time() - start_time
            
            # Record in history
            if execution_result.result:
                self.history_tracker.record_execution(tool_call, execution_result.result, duration)
            
            # Update loop detector
            if execution_result.success:
                self.loop_detector.record_success(tool_call)
            else:
                self.loop_detector.record_failure(tool_call)
            
            results.append(execution_result)
        
        return results
    
    def _should_stop_execution(self, execution_results) -> bool:
        """Determine if execution should stop"""
        # Stop if all tools failed
        if execution_results and all(not result.success for result in execution_results):
            if HAS_CLI_UI:
                warning("All tool executions failed, stopping")
            return True
        
        # Stop if we hit the iteration limit
        if self.iteration_count >= self.config.max_iterations:
            if HAS_CLI_UI:
                warning(f"Reached maximum iterations ({self.config.max_iterations})")
            return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive agent statistics"""
        return {
            "agent_state": self.state.value,
            "iteration_count": self.iteration_count,
            "session_stats": self.history_tracker.get_session_stats(),
            "tool_executor_stats": self.tool_executor.get_stats(),
            "loop_detector_stats": self.loop_detector.get_stats(),
            "permission_stats": self.permission_manager.get_stats(),
            "conversation_history_length": len(self.llm_interface.get_history())
        }
    
    def reset(self) -> None:
        """Reset agent to initial state"""
        self.state = AgentState.IDLE
        self.iteration_count = 0
        self.llm_interface.clear_history()
        self.history_tracker.clear_history()
        self.loop_detector.reset()
        self.permission_manager.reset_session()
        self.tool_executor.reset_stats()
    
    def export_session(self, format: str = 'json') -> str:
        """Export session data"""
        session_data = {
            "stats": self.get_stats(),
            "execution_history": self.history_tracker.export_history(format='json'),
            "conversation_history": self.llm_interface.get_history()
        }
        
        if format.lower() == 'json':
            return json.dumps(session_data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Factory function for backward compatibility
def create_modular_agent(llm=None, **config_kwargs) -> ModularAgent:
    """Create a modular agent instance"""
    return ModularAgent(llm=llm, **config_kwargs)


# Alias for easier migration from the original Agent class
RefactoredAgent = ModularAgent