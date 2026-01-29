"""
Permission Manager Component
Handles tool execution permissions and approvals
"""

from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from ..core import ToolCall, AgentConfig

# Import permission UI if available
try:
    from ...permission_ui import (
        ask_permission, check_remembered, remember_approval,
        PermissionChoice, PermissionResult
    )
    HAS_PERMISSION_UI = True
except ImportError:
    HAS_PERMISSION_UI = False

# Import CLI UI for feedback
try:
    from ...cli_ui import warning, info, success
    HAS_CLI_UI = True
except ImportError:
    HAS_CLI_UI = False


class PermissionLevel(Enum):
    """Permission levels for tools"""
    ALWAYS_ALLOW = "always_allow"
    ASK_ONCE = "ask_once"
    ASK_ALWAYS = "ask_always" 
    NEVER_ALLOW = "never_allow"


@dataclass
class PermissionCheck:
    """Result of permission check"""
    granted: bool
    should_remember: bool = False
    message: Optional[str] = None


class PermissionManager:
    """Manages permissions for tool execution"""
    
    def __init__(self, config: 'AgentConfig'):
        self.config = config
        self.remembered_permissions: Dict[str, bool] = {}
        self.session_permissions: Dict[str, bool] = {}
        self.tool_permissions: Dict[str, PermissionLevel] = {}
        
        # Load permission configuration
        self._load_permission_config()
    
    def check_permission(self, tool_call: 'ToolCall') -> PermissionCheck:
        """Check if tool execution is permitted"""
        tool_name = tool_call.tool_name
        
        # Check tool-specific permission level
        permission_level = self.tool_permissions.get(tool_name, PermissionLevel.ASK_ONCE)
        
        if permission_level == PermissionLevel.ALWAYS_ALLOW:
            return PermissionCheck(granted=True, message="Tool always allowed")
        
        if permission_level == PermissionLevel.NEVER_ALLOW:
            return PermissionCheck(granted=False, message="Tool never allowed by configuration")
        
        # Check remembered permissions
        permission_key = self._get_permission_key(tool_call)
        
        if permission_key in self.remembered_permissions:
            granted = self.remembered_permissions[permission_key]
            return PermissionCheck(
                granted=granted,
                message="Using remembered permission" if granted else "Blocked by remembered permission"
            )
        
        # Check session permissions for ASK_ONCE
        if permission_level == PermissionLevel.ASK_ONCE:
            if permission_key in self.session_permissions:
                granted = self.session_permissions[permission_key]
                return PermissionCheck(
                    granted=granted,
                    message="Using session permission" if granted else "Blocked by session permission"
                )
        
        # Need to ask user
        return self._request_permission(tool_call)
    
    def _request_permission(self, tool_call: 'ToolCall') -> PermissionCheck:
        """Request permission from user"""
        if not HAS_PERMISSION_UI:
            # No permission UI available, default to allow with warning
            if HAS_CLI_UI:
                warning(f"Permission UI not available - allowing {tool_call.tool_name}")
            return PermissionCheck(granted=True, message="Permission UI not available")
        
        try:
            # Get command details for user
            command_display = self._format_command_for_permission(tool_call)
            
            # Ask for permission
            result = ask_permission(
                tool_name=tool_call.tool_name,
                command=command_display,
                risk_level=self._assess_risk_level(tool_call)
            )
            
            if result.choice == PermissionChoice.ALLOW:
                granted = True
                message = "User granted permission"
            elif result.choice == PermissionChoice.DENY:
                granted = False
                message = "User denied permission"
            elif result.choice == PermissionChoice.ALLOW_ALL:
                granted = True
                message = "User granted permission for all similar commands"
                # Remember this permission
                self._remember_permission(tool_call, True, session_only=False)
            else:  # DENY_ALL
                granted = False
                message = "User denied permission for all similar commands" 
                # Remember this denial
                self._remember_permission(tool_call, False, session_only=False)
            
            # Handle session-only permissions
            if result.choice in [PermissionChoice.ALLOW, PermissionChoice.DENY]:
                permission_level = self.tool_permissions.get(tool_call.tool_name, PermissionLevel.ASK_ONCE)
                if permission_level == PermissionLevel.ASK_ONCE:
                    self._remember_permission(tool_call, granted, session_only=True)
            
            if HAS_CLI_UI:
                if granted:
                    success(f"Permission granted for {tool_call.tool_name}")
                else:
                    warning(f"Permission denied for {tool_call.tool_name}")
            
            return PermissionCheck(granted=granted, message=message)
            
        except Exception as e:
            if HAS_CLI_UI:
                warning(f"Permission request failed: {e}")
            # Default to allow on error
            return PermissionCheck(granted=True, message=f"Permission request failed: {e}")
    
    def _get_permission_key(self, tool_call: 'ToolCall') -> str:
        """Generate a key for permission caching"""
        # Create key based on tool and sensitive parameters
        if tool_call.tool_name == 'Bash':
            # For bash commands, use the command itself as key
            command = tool_call.parameters.get('command', '')
            return f"bash:{command}"
        elif tool_call.tool_name in ['Write', 'Edit']:
            # For file operations, use file path
            file_path = tool_call.parameters.get('file_path', '')
            return f"{tool_call.tool_name.lower()}:{file_path}"
        else:
            # For other tools, use tool name only
            return tool_call.tool_name
    
    def _format_command_for_permission(self, tool_call: 'ToolCall') -> str:
        """Format command for user display"""
        if tool_call.tool_name == 'Bash':
            return tool_call.parameters.get('command', 'Unknown command')
        elif tool_call.tool_name == 'Write':
            file_path = tool_call.parameters.get('file_path', 'unknown file')
            return f"Write to {file_path}"
        elif tool_call.tool_name == 'Edit':
            file_path = tool_call.parameters.get('file_path', 'unknown file')
            return f"Edit {file_path}"
        elif tool_call.tool_name == 'Read':
            file_path = tool_call.parameters.get('file_path', 'unknown file')
            return f"Read {file_path}"
        else:
            return f"{tool_call.tool_name} with parameters: {tool_call.parameters}"
    
    def _assess_risk_level(self, tool_call: 'ToolCall') -> str:
        """Assess risk level of the tool call"""
        if tool_call.tool_name == 'Bash':
            command = tool_call.parameters.get('command', '').lower()
            if any(dangerous in command for dangerous in ['rm ', 'sudo ', 'chmod ', 'del ']):
                return "high"
            elif any(moderate in command for moderate in ['git ', 'npm ', 'pip ', 'curl ']):
                return "medium"
            else:
                return "low"
        elif tool_call.tool_name in ['Write', 'Edit']:
            return "medium"
        elif tool_call.tool_name == 'WebFetch':
            return "medium" 
        else:
            return "low"
    
    def _remember_permission(self, tool_call: 'ToolCall', granted: bool, session_only: bool = False) -> None:
        """Remember permission decision"""
        permission_key = self._get_permission_key(tool_call)
        
        if session_only:
            self.session_permissions[permission_key] = granted
        else:
            self.remembered_permissions[permission_key] = granted
            # Persist to file if permission UI is available
            if HAS_PERMISSION_UI:
                try:
                    remember_approval(permission_key, granted)
                except Exception as e:
                    if HAS_CLI_UI:
                        warning(f"Failed to persist permission: {e}")
    
    def _load_permission_config(self) -> None:
        """Load permission configuration"""
        # Set default permissions based on config
        permission_config = getattr(self.config, 'tool_permissions', {})
        
        for tool_name, level in permission_config.items():
            if isinstance(level, str):
                try:
                    self.tool_permissions[tool_name] = PermissionLevel(level)
                except ValueError:
                    if HAS_CLI_UI:
                        warning(f"Invalid permission level '{level}' for tool '{tool_name}'")
                    self.tool_permissions[tool_name] = PermissionLevel.ASK_ONCE
        
        # Load remembered permissions if UI is available
        if HAS_PERMISSION_UI:
            try:
                # This would load from persistent storage
                # Implementation depends on the permission UI system
                pass
            except Exception as e:
                if HAS_CLI_UI:
                    warning(f"Failed to load remembered permissions: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get permission statistics"""
        return {
            "remembered_permissions": len(self.remembered_permissions),
            "session_permissions": len(self.session_permissions),
            "tool_permissions": {k: v.value for k, v in self.tool_permissions.items()},
            "has_permission_ui": HAS_PERMISSION_UI
        }
    
    def reset_session(self) -> None:
        """Reset session permissions"""
        self.session_permissions.clear()
    
    def clear_remembered(self) -> None:
        """Clear all remembered permissions"""
        self.remembered_permissions.clear()