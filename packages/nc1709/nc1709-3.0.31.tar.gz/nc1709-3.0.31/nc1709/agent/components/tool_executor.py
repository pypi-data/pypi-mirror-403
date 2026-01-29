"""
Tool Executor Component
Handles tool execution with visual feedback and error handling
"""

import json
import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..tools.base import Tool, ToolResult, ToolRegistry
    from ..core import ToolCall, AgentConfig

# Import CLI UI if available
try:
    from ...cli_ui import (
        ActionSpinner, Color, Icons,
        status, thinking, success, error, warning, info,
        log_action, log_output
    )
    HAS_CLI_UI = True
except ImportError:
    HAS_CLI_UI = False


@dataclass
class ExecutionResult:
    """Result of tool execution"""
    success: bool
    result: Optional['ToolResult'] = None
    error: Optional[str] = None
    duration: Optional[float] = None
    tool_name: Optional[str] = None


class ToolExecutor:
    """Handles tool execution with feedback and monitoring"""
    
    def __init__(self, tool_registry: 'ToolRegistry', config: 'AgentConfig'):
        self.registry = tool_registry
        self.config = config
        self.execution_count = 0
        self.total_execution_time = 0.0
        
    def execute_tool_call(self, tool_call: 'ToolCall') -> ExecutionResult:
        """Execute a single tool call with comprehensive error handling"""
        start_time = time.time()
        self.execution_count += 1
        
        # Get the tool
        tool = self.registry.get_tool(tool_call.tool_name)
        if not tool:
            error_msg = f"Tool '{tool_call.tool_name}' not found"
            if HAS_CLI_UI:
                error(error_msg)
            return ExecutionResult(
                success=False,
                error=error_msg,
                duration=time.time() - start_time,
                tool_name=tool_call.tool_name
            )
        
        try:
            # Show execution feedback
            if HAS_CLI_UI:
                with ActionSpinner(
                    f"Executing {tool_call.tool_name}",
                    success_msg=f"Completed {tool_call.tool_name}"
                ):
                    result = self._execute_with_monitoring(tool, tool_call)
            else:
                result = self._execute_with_monitoring(tool, tool_call)
            
            duration = time.time() - start_time
            self.total_execution_time += duration
            
            # Log successful execution
            if HAS_CLI_UI:
                log_action(f"✓ {tool_call.tool_name}", Color.GREEN)
                if result.output and len(result.output) < 200:
                    log_output(result.output[:200], Color.BLUE)
                elif result.output:
                    log_output(f"{result.output[:100]}... (truncated)", Color.BLUE)
            
            return ExecutionResult(
                success=True,
                result=result,
                duration=duration,
                tool_name=tool_call.tool_name
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Tool execution failed: {str(e)}"
            
            if HAS_CLI_UI:
                error(f"✗ {tool_call.tool_name}: {error_msg}")
            
            # Use custom exceptions if available
            try:
                from ...exceptions import AgentError
                raise AgentError(error_msg, agent_id=self.config.agent_id)
            except ImportError:
                pass
            
            return ExecutionResult(
                success=False,
                error=error_msg,
                duration=duration,
                tool_name=tool_call.tool_name
            )
    
    def execute_multiple(self, tool_calls: List['ToolCall']) -> List[ExecutionResult]:
        """Execute multiple tool calls"""
        results = []
        
        if HAS_CLI_UI:
            status(f"Executing {len(tool_calls)} tool calls...")
        
        for i, tool_call in enumerate(tool_calls, 1):
            if HAS_CLI_UI:
                info(f"[{i}/{len(tool_calls)}] {tool_call.tool_name}")
            
            result = self.execute_tool_call(tool_call)
            results.append(result)
            
            # Stop on critical failures if configured
            if not result.success and getattr(self.config, 'stop_on_error', False):
                if HAS_CLI_UI:
                    warning(f"Stopping execution due to error in {tool_call.tool_name}")
                break
        
        return results
    
    def _execute_with_monitoring(self, tool: 'Tool', tool_call: 'ToolCall') -> 'ToolResult':
        """Execute tool with monitoring and metrics"""
        try:
            # Record metrics if monitoring is available
            from ...monitoring.metrics import TOOL_EXECUTION_COUNT, TOOL_EXECUTION_DURATION
            from ...monitoring.metrics import time as metrics_time
            
            start_time = metrics_time()
            
            # Execute the tool
            result = tool.execute(**tool_call.parameters)
            
            # Record metrics
            duration = metrics_time() - start_time
            TOOL_EXECUTION_COUNT.inc(
                tool_name=tool_call.tool_name,
                status="success" if result.success else "failure"
            )
            TOOL_EXECUTION_DURATION.observe(duration, tool_name=tool_call.tool_name)
            
            return result
            
        except ImportError:
            # Monitoring not available, execute normally
            return tool.execute(**tool_call.parameters)
        except Exception as e:
            # Record failure metrics if available
            try:
                from ...monitoring.metrics import TOOL_EXECUTION_COUNT
                TOOL_EXECUTION_COUNT.inc(
                    tool_name=tool_call.tool_name,
                    status="error"
                )
            except ImportError:
                pass
            raise e
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            "total_executions": self.execution_count,
            "total_time": self.total_execution_time,
            "average_time": (
                self.total_execution_time / self.execution_count 
                if self.execution_count > 0 else 0
            ),
            "available_tools": len(self.registry.list_tools())
        }
    
    def reset_stats(self) -> None:
        """Reset execution statistics"""
        self.execution_count = 0
        self.total_execution_time = 0.0