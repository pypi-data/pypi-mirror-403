"""
History Tracker Component
Tracks agent execution history and provides analysis
"""

import json
import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, asdict
from collections import defaultdict

if TYPE_CHECKING:
    from ..tools.base import ToolResult
    from ..core import ToolCall


@dataclass
class ExecutionRecord:
    """Record of a single tool execution"""
    timestamp: float
    tool_name: str
    parameters: Dict[str, Any]
    success: bool
    duration: Optional[float] = None
    output_length: Optional[int] = None
    error: Optional[str] = None


@dataclass
class SessionStats:
    """Statistics for an agent session"""
    start_time: float
    total_executions: int
    successful_executions: int
    failed_executions: int
    total_duration: float
    tools_used: Dict[str, int]
    avg_execution_time: float


class HistoryTracker:
    """Tracks and analyzes agent execution history"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.execution_history: List[ExecutionRecord] = []
        self.session_start = time.time()
        self.total_duration = 0.0
        
    def record_execution(
        self, 
        tool_call: 'ToolCall', 
        result: 'ToolResult',
        duration: Optional[float] = None
    ) -> None:
        """Record a tool execution"""
        record = ExecutionRecord(
            timestamp=time.time(),
            tool_name=tool_call.tool_name,
            parameters=tool_call.parameters.copy(),
            success=result.success,
            duration=duration,
            output_length=len(result.output) if result.output else 0,
            error=result.error if not result.success else None
        )
        
        self.execution_history.append(record)
        
        # Maintain max history
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history:]
        
        # Update total duration
        if duration:
            self.total_duration += duration
    
    def get_session_stats(self) -> SessionStats:
        """Get statistics for the current session"""
        if not self.execution_history:
            return SessionStats(
                start_time=self.session_start,
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                total_duration=0.0,
                tools_used={},
                avg_execution_time=0.0
            )
        
        successful = sum(1 for record in self.execution_history if record.success)
        failed = len(self.execution_history) - successful
        
        # Count tool usage
        tools_used = defaultdict(int)
        for record in self.execution_history:
            tools_used[record.tool_name] += 1
        
        avg_time = (
            self.total_duration / len(self.execution_history)
            if self.execution_history else 0.0
        )
        
        return SessionStats(
            start_time=self.session_start,
            total_executions=len(self.execution_history),
            successful_executions=successful,
            failed_executions=failed,
            total_duration=self.total_duration,
            tools_used=dict(tools_used),
            avg_execution_time=avg_time
        )
    
    def get_recent_history(self, count: int = 10) -> List[ExecutionRecord]:
        """Get the most recent execution records"""
        return self.execution_history[-count:]
    
    def get_tool_history(self, tool_name: str) -> List[ExecutionRecord]:
        """Get history for a specific tool"""
        return [
            record for record in self.execution_history 
            if record.tool_name == tool_name
        ]
    
    def get_failed_executions(self) -> List[ExecutionRecord]:
        """Get all failed executions"""
        return [
            record for record in self.execution_history 
            if not record.success
        ]
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze execution patterns"""
        if not self.execution_history:
            return {"message": "No execution history available"}
        
        analysis = {}
        
        # Success rate by tool
        tool_stats = defaultdict(lambda: {'total': 0, 'successful': 0})
        for record in self.execution_history:
            tool_stats[record.tool_name]['total'] += 1
            if record.success:
                tool_stats[record.tool_name]['successful'] += 1
        
        tool_success_rates = {}
        for tool, stats in tool_stats.items():
            success_rate = stats['successful'] / stats['total'] if stats['total'] > 0 else 0
            tool_success_rates[tool] = {
                'success_rate': success_rate,
                'total_executions': stats['total']
            }
        
        analysis['tool_success_rates'] = tool_success_rates
        
        # Identify most problematic tools
        problematic_tools = [
            tool for tool, stats in tool_success_rates.items()
            if stats['success_rate'] < 0.8 and stats['total_executions'] >= 3
        ]
        analysis['problematic_tools'] = problematic_tools
        
        # Time-based analysis
        if len(self.execution_history) >= 2:
            recent_records = self.execution_history[-10:]
            durations = [r.duration for r in recent_records if r.duration]
            if durations:
                analysis['recent_avg_duration'] = sum(durations) / len(durations)
                analysis['longest_recent_execution'] = max(durations)
        
        # Execution frequency
        session_duration = time.time() - self.session_start
        if session_duration > 0:
            analysis['executions_per_minute'] = len(self.execution_history) / (session_duration / 60)
        
        return analysis
    
    def export_history(self, format: str = 'json') -> str:
        """Export execution history in specified format"""
        if format.lower() == 'json':
            return json.dumps([asdict(record) for record in self.execution_history], indent=2)
        elif format.lower() == 'csv':
            if not self.execution_history:
                return "timestamp,tool_name,success,duration,error\n"
            
            lines = ["timestamp,tool_name,success,duration,error"]
            for record in self.execution_history:
                error = record.error.replace(',', ';') if record.error else ""
                lines.append(
                    f"{record.timestamp},{record.tool_name},{record.success},"
                    f"{record.duration or ''},{error}"
                )
            return '\n'.join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def find_similar_executions(self, tool_call: 'ToolCall', limit: int = 5) -> List[ExecutionRecord]:
        """Find similar previous executions"""
        similar = []
        
        for record in self.execution_history:
            if record.tool_name == tool_call.tool_name:
                # Calculate similarity based on parameters
                similarity = self._calculate_similarity(tool_call.parameters, record.parameters)
                if similarity > 0.7:  # 70% similarity threshold
                    similar.append(record)
        
        # Sort by timestamp (most recent first) and limit
        similar.sort(key=lambda x: x.timestamp, reverse=True)
        return similar[:limit]
    
    def _calculate_similarity(self, params1: Dict[str, Any], params2: Dict[str, Any]) -> float:
        """Calculate similarity between two parameter sets"""
        if not params1 and not params2:
            return 1.0
        
        if not params1 or not params2:
            return 0.0
        
        # Simple similarity based on common keys and values
        all_keys = set(params1.keys()) | set(params2.keys())
        common_keys = set(params1.keys()) & set(params2.keys())
        
        if not all_keys:
            return 1.0
        
        key_similarity = len(common_keys) / len(all_keys)
        
        # Check value similarity for common keys
        value_matches = 0
        for key in common_keys:
            if params1[key] == params2[key]:
                value_matches += 1
        
        value_similarity = value_matches / len(common_keys) if common_keys else 0
        
        return (key_similarity + value_similarity) / 2
    
    def clear_history(self) -> None:
        """Clear all execution history"""
        self.execution_history.clear()
        self.total_duration = 0.0
        self.session_start = time.time()
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the session"""
        stats = self.get_session_stats()
        
        if stats.total_executions == 0:
            return "No tools executed in this session."
        
        session_duration = time.time() - self.session_start
        
        summary = [
            f"Session Summary:",
            f"  Duration: {session_duration:.1f}s",
            f"  Total executions: {stats.total_executions}",
            f"  Successful: {stats.successful_executions} ({stats.successful_executions/stats.total_executions*100:.1f}%)",
            f"  Failed: {stats.failed_executions}",
            f"  Average execution time: {stats.avg_execution_time:.2f}s",
            f"  Tools used: {', '.join(f'{tool}({count})' for tool, count in stats.tools_used.items())}"
        ]
        
        return '\n'.join(summary)