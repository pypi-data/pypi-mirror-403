"""
Dependency Injection Enabled Agent
Agent implementation using dependency injection for better testability
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from enum import Enum

# Import DI framework
from ..di import injectable, inject, get_container, DIContainer
from ..di.providers import factory, conditional, configuration

# Import components (these will be injected)
from .components import (
    LLMInterface, ToolExecutor, PermissionManager,
    LoopDetector, ResponseFormatter, HistoryTracker
)

# Import base classes
from .tools.base import ToolRegistry
from .core import AgentConfig, ToolCall, AgentState

# Import CLI UI if available
try:
    from ..cli_ui import status, thinking, success, error, warning, info
    HAS_CLI_UI = True
except ImportError:
    HAS_CLI_UI = False

if TYPE_CHECKING:
    from .tools.base import ToolResult


@injectable
class DIAgent:
    """
    Dependency Injection enabled Agent
    
    This agent uses dependency injection for all its components,
    making it highly testable and modular.
    """
    
    def __init__(
        self,
        config: AgentConfig,
        tool_registry: ToolRegistry,
        llm_interface: LLMInterface,
        tool_executor: ToolExecutor,
        permission_manager: PermissionManager,
        loop_detector: LoopDetector,
        response_formatter: ResponseFormatter,
        history_tracker: HistoryTracker
    ):
        self.config = config
        self.tool_registry = tool_registry
        self.llm_interface = llm_interface
        self.tool_executor = tool_executor
        self.permission_manager = permission_manager
        self.loop_detector = loop_detector
        self.response_formatter = response_formatter
        self.history_tracker = history_tracker
        
        # Agent state
        self.state = AgentState.IDLE
        self.iteration_count = 0
    
    @inject
    def run(self, user_request: str) -> str:
        """
        Main execution loop with dependency injection
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
                
                # Execute tool calls with all the safety checks
                execution_results = self._execute_tools_safely(tool_calls)
                
                # Format results for context
                tool_results = [
                    result.result for result in execution_results 
                    if result.success and result.result
                ]
                
                if tool_results:
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
            
            # Use custom exceptions if available
            try:
                from ..exceptions import AgentError
                raise AgentError(str(e), agent_id=getattr(self.config, 'agent_id', 'unknown'))
            except ImportError:
                pass
            
            return error_response
    
    def _parse_tool_calls(self, response: str) -> List[ToolCall]:
        """Parse tool calls from LLM response"""
        import re
        import json
        
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
    
    def _execute_tools_safely(self, tool_calls: List[ToolCall]) -> List:
        """Execute tools with comprehensive safety checks"""
        results = []
        
        for tool_call in tool_calls:
            # Loop detection
            loop_result = self.loop_detector.check_for_loops(tool_call)
            if loop_result.is_loop:
                if HAS_CLI_UI:
                    warning(f"Loop detected: {loop_result.message}")
                continue
            
            # Permission check
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
            
            # Update loop detector state
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
        import json
        
        session_data = {
            "stats": self.get_stats(),
            "execution_history": self.history_tracker.export_history(format='json'),
            "conversation_history": self.llm_interface.get_history()
        }
        
        if format.lower() == 'json':
            return json.dumps(session_data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")


class DIAgentFactory:
    """Factory for creating DI-enabled agents with proper configuration"""
    
    @staticmethod
    def create_agent(
        config: Optional[AgentConfig] = None,
        container: Optional[DIContainer] = None,
        **config_kwargs
    ) -> DIAgent:
        """
        Create a DI-enabled agent with proper dependency setup
        
        Args:
            config: Agent configuration
            container: DI container to use (will use global if None)
            **config_kwargs: Additional configuration parameters
            
        Returns:
            Configured DIAgent instance
        """
        if container is None:
            container = get_container()
        
        # Setup default configuration
        if config is None:
            config = AgentConfig(**config_kwargs)
        
        # Register agent configuration
        container.register_singleton(AgentConfig, config)
        
        # Register default tool registry
        if not container.is_registered(ToolRegistry):
            from .tools.base import get_default_registry
            from .tools.file_tools import register_file_tools
            from .tools.search_tools import register_search_tools
            from .tools.bash_tool import register_bash_tools
            from .tools.task_tool import register_task_tools
            from .tools.web_tools import register_web_tools
            from .tools.notebook_tools import register_notebook_tools
            
            def create_registry():
                registry = get_default_registry()
                register_file_tools(registry)
                register_search_tools(registry)
                register_bash_tools(registry)
                register_task_tools(registry)
                register_web_tools(registry)
                register_notebook_tools(registry)
                return registry
            
            container.register_singleton(ToolRegistry, factory(create_registry))
        
        # Register components if not already registered
        component_classes = [
            LLMInterface,
            ToolExecutor,
            PermissionManager,
            LoopDetector,
            ResponseFormatter,
            HistoryTracker
        ]
        
        for component_class in component_classes:
            if not container.is_registered(component_class):
                container.register_singleton(component_class)
        
        # Create and return agent
        return container.resolve(DIAgent)
    
    @staticmethod
    def create_test_agent(
        config: Optional[AgentConfig] = None,
        mock_llm: Optional[Any] = None,
        mock_tools: Optional[Dict[str, Any]] = None,
        **config_kwargs
    ) -> DIAgent:
        """
        Create an agent for testing with mocked dependencies
        
        Args:
            config: Agent configuration
            mock_llm: Mock LLM to use
            mock_tools: Mock tools to register
            **config_kwargs: Additional configuration parameters
            
        Returns:
            DIAgent configured for testing
        """
        # Create test container
        test_container = DIContainer("test")
        
        # Setup test configuration
        if config is None:
            test_config = AgentConfig(
                max_iterations=5,
                max_history=50,
                **config_kwargs
            )
        else:
            test_config = config
        
        if mock_llm:
            test_config.llm = mock_llm
        
        return DIAgentFactory.create_agent(test_config, test_container)


# Convenience functions
def create_di_agent(**kwargs) -> DIAgent:
    """Create a DI-enabled agent with default configuration"""
    return DIAgentFactory.create_agent(**kwargs)


def create_test_agent(**kwargs) -> DIAgent:
    """Create a DI-enabled agent for testing"""
    return DIAgentFactory.create_test_agent(**kwargs)