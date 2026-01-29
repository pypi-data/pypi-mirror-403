"""
Response Formatter Component  
Handles formatting of tool results and agent responses
"""

import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..tools.base import ToolResult


@dataclass
class FormattedResponse:
    """Formatted response with metadata"""
    content: str
    tool_results_count: int = 0
    has_errors: bool = False
    truncated: bool = False


class ResponseFormatter:
    """Formats tool results and agent responses"""
    
    def __init__(self, max_output_length: int = 2000):
        self.max_output_length = max_output_length
    
    def format_tool_results(self, results: List['ToolResult']) -> FormattedResponse:
        """Format multiple tool results into a cohesive response"""
        if not results:
            return FormattedResponse(content="No tool results to display.")
        
        formatted_parts = []
        has_errors = False
        total_length = 0
        
        for i, result in enumerate(results, 1):
            formatted_result = self._format_single_result(result, i, len(results))
            formatted_parts.append(formatted_result.content)
            
            if formatted_result.has_errors:
                has_errors = True
            
            total_length += len(formatted_result.content)
            
            # Check if we're approaching the limit
            if total_length > self.max_output_length:
                remaining_results = len(results) - i
                if remaining_results > 0:
                    formatted_parts.append(f"\n... and {remaining_results} more results (truncated)")
                break
        
        content = "\n\n".join(formatted_parts)
        
        return FormattedResponse(
            content=content,
            tool_results_count=len(results),
            has_errors=has_errors,
            truncated=total_length > self.max_output_length
        )
    
    def _format_single_result(self, result: 'ToolResult', index: int, total: int) -> FormattedResponse:
        """Format a single tool result"""
        has_errors = not result.success
        
        # Create header
        if total > 1:
            header = f"[{index}/{total}] {result.tool_name}"
        else:
            header = result.tool_name
        
        if result.success:
            header += " ✓"
        else:
            header += " ✗"
        
        # Format the main content
        if result.success:
            if result.output:
                content = self._format_output(result.output)
            else:
                content = "(No output)"
        else:
            content = f"Error: {result.error or 'Unknown error'}"
        
        # Add metadata if present
        metadata_parts = []
        if hasattr(result, 'duration') and result.duration:
            metadata_parts.append(f"took {result.duration:.2f}s")
        if hasattr(result, 'file_path') and result.file_path:
            metadata_parts.append(f"file: {result.file_path}")
        
        if metadata_parts:
            metadata = f" ({', '.join(metadata_parts)})"
        else:
            metadata = ""
        
        formatted = f"{header}{metadata}:\n{content}"
        
        return FormattedResponse(
            content=formatted,
            has_errors=has_errors,
            truncated=len(content) > self.max_output_length
        )
    
    def _format_output(self, output: str) -> str:
        """Format tool output for display"""
        if not output:
            return "(Empty output)"
        
        # Truncate if too long
        if len(output) > self.max_output_length:
            truncated_output = output[:self.max_output_length - 50]
            return f"{truncated_output}\n... (output truncated - {len(output)} total characters)"
        
        # Clean up common formatting issues
        cleaned = self._clean_output(output)
        
        # Add code block formatting for certain outputs
        if self._looks_like_code_or_data(cleaned):
            return f"```\n{cleaned}\n```"
        
        return cleaned
    
    def _clean_output(self, output: str) -> str:
        """Clean up output formatting"""
        # Remove excessive newlines
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', output)
        
        # Remove trailing whitespace from lines
        cleaned = '\n'.join(line.rstrip() for line in cleaned.split('\n'))
        
        # Strip leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _looks_like_code_or_data(self, text: str) -> bool:
        """Determine if text looks like code or structured data"""
        # Check for common code/data patterns
        code_indicators = [
            '{', '}',  # JSON/code blocks
            '<?xml', '<!DOCTYPE',  # XML
            'def ', 'class ', 'function ',  # Python/JS functions
            '#include', 'import ',  # Includes/imports
            'SELECT ', 'CREATE ', 'UPDATE ',  # SQL
            'HTTP/', 'Content-Type:',  # HTTP
        ]
        
        text_lower = text.lower()
        return any(indicator.lower() in text_lower for indicator in code_indicators)
    
    def clean_llm_response(self, response: str) -> str:
        """Clean up LLM response formatting"""
        # Remove common artifacts
        cleaned = response.strip()
        
        # Remove excessive spacing
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        
        # Remove markdown artifacts that might leak through
        cleaned = re.sub(r'^```[\w]*\n?', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'\n?```$', '', cleaned, flags=re.MULTILINE)
        
        # Remove repetitive patterns
        cleaned = self._remove_repetitive_patterns(cleaned)
        
        return cleaned.strip()
    
    def _remove_repetitive_patterns(self, text: str) -> str:
        """Remove obvious repetitive patterns"""
        lines = text.split('\n')
        
        # Remove duplicate consecutive lines
        filtered_lines = []
        last_line = None
        repeat_count = 0
        
        for line in lines:
            if line == last_line:
                repeat_count += 1
                if repeat_count <= 1:  # Allow one repeat
                    filtered_lines.append(line)
            else:
                filtered_lines.append(line)
                repeat_count = 0
                last_line = line
        
        return '\n'.join(filtered_lines)
    
    def format_error_response(self, error_message: str, context: Optional[str] = None) -> str:
        """Format an error response"""
        formatted = f"❌ Error: {error_message}"
        
        if context:
            formatted += f"\n\nContext: {context}"
        
        return formatted
    
    def format_success_response(self, message: str, details: Optional[str] = None) -> str:
        """Format a success response"""
        formatted = f"✅ {message}"
        
        if details:
            formatted += f"\n\n{details}"
        
        return formatted
    
    def summarize_results(self, results: List['ToolResult']) -> str:
        """Create a summary of tool execution results"""
        if not results:
            return "No tools executed."
        
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        summary = f"Executed {len(results)} tool(s): {successful} successful"
        if failed > 0:
            summary += f", {failed} failed"
        
        # Add tool breakdown
        tool_counts = {}
        for result in results:
            tool_counts[result.tool_name] = tool_counts.get(result.tool_name, 0) + 1
        
        if tool_counts:
            tool_list = [f"{tool}({count})" for tool, count in tool_counts.items()]
            summary += f" - Tools used: {', '.join(tool_list)}"
        
        return summary