"""
Loop Detector Component
Detects and prevents infinite loops and repetitive behavior
"""

import hashlib
from collections import Counter, deque
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..core import ToolCall


@dataclass
class LoopDetectionResult:
    """Result of loop detection analysis"""
    is_loop: bool
    loop_type: Optional[str] = None
    message: Optional[str] = None
    suggested_action: Optional[str] = None


class LoopDetector:
    """Detects various types of loops and repetitive patterns"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.execution_history: deque = deque(maxlen=max_history)
        self.command_signatures: deque = deque(maxlen=max_history)
        self.success_commands: Set[str] = set()
        self.failure_commands: Set[str] = set()
        self.alternating_threshold = 3
        self.repetition_threshold = 5
        
    def check_for_loops(self, tool_call: 'ToolCall') -> LoopDetectionResult:
        """Comprehensive loop detection"""
        # Get command signature
        signature = self._get_command_signature(tool_call)
        
        # Check for direct repetition
        direct_loop = self._check_direct_repetition(signature)
        if direct_loop.is_loop:
            return direct_loop
            
        # Check for alternating pattern
        alternating_loop = self._check_alternating_pattern()
        if alternating_loop.is_loop:
            return alternating_loop
            
        # Check for semantic loops
        semantic_loop = self._check_semantic_loops(tool_call)
        if semantic_loop.is_loop:
            return semantic_loop
            
        # Check for failure loops
        failure_loop = self._check_failure_loops(signature)
        if failure_loop.is_loop:
            return failure_loop
        
        # Add to history
        self.execution_history.append(tool_call)
        self.command_signatures.append(signature)
        
        return LoopDetectionResult(is_loop=False)
    
    def _get_command_signature(self, tool_call: 'ToolCall') -> str:
        """Generate a signature for the tool call"""
        # Create a hash of the tool name and key parameters
        key_params = {}
        
        # Include important parameters based on tool type
        if tool_call.tool_name in ['Read', 'Write', 'Edit']:
            key_params['file_path'] = tool_call.parameters.get('file_path', '')
        elif tool_call.tool_name == 'Bash':
            key_params['command'] = tool_call.parameters.get('command', '')
        elif tool_call.tool_name in ['Grep', 'Glob']:
            key_params['pattern'] = tool_call.parameters.get('pattern', '')
            key_params['path'] = tool_call.parameters.get('path', '')
        else:
            # For other tools, include all parameters
            key_params = tool_call.parameters
        
        # Create signature
        signature_data = f"{tool_call.tool_name}:{json.dumps(key_params, sort_keys=True)}"
        return hashlib.md5(signature_data.encode()).hexdigest()[:8]
    
    def _check_direct_repetition(self, signature: str) -> LoopDetectionResult:
        """Check for direct command repetition"""
        if len(self.command_signatures) < self.repetition_threshold:
            return LoopDetectionResult(is_loop=False)
        
        # Count recent occurrences
        recent_signatures = list(self.command_signatures)[-10:]
        signature_counts = Counter(recent_signatures)
        
        if signature_counts[signature] >= self.repetition_threshold:
            return LoopDetectionResult(
                is_loop=True,
                loop_type="direct_repetition",
                message=f"Detected repeated execution of the same command ({signature_counts[signature]} times)",
                suggested_action="Try a different approach or check if the command is actually needed"
            )
        
        return LoopDetectionResult(is_loop=False)
    
    def _check_alternating_pattern(self) -> LoopDetectionResult:
        """Check for alternating command patterns"""
        if len(self.command_signatures) < 6:
            return LoopDetectionResult(is_loop=False)
        
        recent = list(self.command_signatures)[-6:]
        
        # Check for A-B-A-B pattern
        if (len(recent) >= 4 and 
            recent[-1] == recent[-3] and 
            recent[-2] == recent[-4] and 
            recent[-1] != recent[-2]):
            
            return LoopDetectionResult(
                is_loop=True,
                loop_type="alternating_pattern",
                message="Detected alternating pattern between two commands",
                suggested_action="Break the cycle by trying a different approach or checking preconditions"
            )
        
        # Check for A-B-C-A-B-C pattern  
        if (len(recent) == 6 and
            recent[0] == recent[3] and
            recent[1] == recent[4] and
            recent[2] == recent[5]):
            
            return LoopDetectionResult(
                is_loop=True,
                loop_type="three_way_alternation",
                message="Detected three-way alternating pattern",
                suggested_action="Step back and reassess the approach"
            )
        
        return LoopDetectionResult(is_loop=False)
    
    def _check_semantic_loops(self, tool_call: 'ToolCall') -> LoopDetectionResult:
        """Check for semantic loops (similar operations on same files/paths)"""
        if len(self.execution_history) < 5:
            return LoopDetectionResult(is_loop=False)
        
        recent_calls = list(self.execution_history)[-5:]
        
        # Check for file operation loops
        if tool_call.tool_name in ['Read', 'Write', 'Edit']:
            current_file = tool_call.parameters.get('file_path', '')
            file_operations = [
                call for call in recent_calls 
                if (call.tool_name in ['Read', 'Write', 'Edit'] and 
                    call.parameters.get('file_path', '') == current_file)
            ]
            
            if len(file_operations) >= 3:
                return LoopDetectionResult(
                    is_loop=True,
                    loop_type="file_operation_loop",
                    message=f"Multiple operations on the same file: {current_file}",
                    suggested_action="Consider if all these file operations are necessary"
                )
        
        # Check for search operation loops
        if tool_call.tool_name in ['Grep', 'Glob']:
            current_pattern = tool_call.parameters.get('pattern', '')
            search_operations = [
                call for call in recent_calls 
                if (call.tool_name in ['Grep', 'Glob'] and 
                    call.parameters.get('pattern', '') == current_pattern)
            ]
            
            if len(search_operations) >= 3:
                return LoopDetectionResult(
                    is_loop=True,
                    loop_type="search_loop",
                    message=f"Repeated searches for the same pattern: {current_pattern}",
                    suggested_action="The search pattern might be incorrect or the target doesn't exist"
                )
        
        return LoopDetectionResult(is_loop=False)
    
    def _check_failure_loops(self, signature: str) -> LoopDetectionResult:
        """Check for loops involving repeated failures"""
        if signature in self.failure_commands:
            failure_count = sum(1 for sig in list(self.command_signatures)[-10:] if sig == signature)
            if failure_count >= 3:
                return LoopDetectionResult(
                    is_loop=True,
                    loop_type="failure_loop", 
                    message=f"Repeatedly executing a command that has failed before ({failure_count} times)",
                    suggested_action="This command seems to be failing consistently - try a different approach"
                )
        
        return LoopDetectionResult(is_loop=False)
    
    def record_success(self, tool_call: 'ToolCall') -> None:
        """Record a successful tool execution"""
        signature = self._get_command_signature(tool_call)
        self.success_commands.add(signature)
        self.failure_commands.discard(signature)  # Remove from failures if present
    
    def record_failure(self, tool_call: 'ToolCall') -> None:
        """Record a failed tool execution"""
        signature = self._get_command_signature(tool_call)
        self.failure_commands.add(signature)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get loop detection statistics"""
        return {
            "total_executions": len(self.execution_history),
            "successful_commands": len(self.success_commands),
            "failed_commands": len(self.failure_commands),
            "recent_signatures": list(self.command_signatures)[-10:],
            "alternating_threshold": self.alternating_threshold,
            "repetition_threshold": self.repetition_threshold
        }
    
    def reset(self) -> None:
        """Reset loop detection state"""
        self.execution_history.clear()
        self.command_signatures.clear()
        self.success_commands.clear()
        self.failure_commands.clear()


# Import json for signature generation
import json