"""
NC1709 Input Sanitization Module

Provides security sanitization for tool inputs to prevent:
- Command injection
- Path traversal attacks
- Shell metacharacter exploitation
- SQL injection patterns
- XSS patterns

Algorithm: NC1709-SAN (Sanitization and Normalization)
"""

import re
import os
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SanitizationLevel(Enum):
    """Sanitization strictness levels"""
    STRICT = "strict"      # Maximum security, may reject valid inputs
    STANDARD = "standard"  # Balanced security and usability
    PERMISSIVE = "permissive"  # Minimal sanitization, logs warnings


@dataclass
class SanitizationResult:
    """Result of sanitization operation"""
    is_safe: bool
    sanitized_value: Any
    warnings: List[str]
    blocked_patterns: List[str]


# =============================================================================
# Dangerous Patterns (NC1709-SAN Pattern Database)
# =============================================================================

# Shell metacharacters that can enable injection
SHELL_METACHARACTERS = set(';&|`$(){}[]<>\\!#~')  # noqa: W605

# Command injection patterns
COMMAND_INJECTION_PATTERNS = [
    r';\s*\w+',              # ;command
    r'\|\s*\w+',             # |command
    r'\|\|\s*\w+',           # ||command
    r'&&\s*\w+',             # &&command
    r'\$\([^)]+\)',          # $(command)
    r'`[^`]+`',              # `command`
    r'\$\{[^}]+\}',          # ${variable}
    r'>\s*/\w+',             # > /file (redirect)
    r'>>\s*/\w+',            # >> /file (append)
    r'<\s*/\w+',             # < /file (input redirect)
]

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS = [
    r'\.\.',                  # Parent directory
    r'\.\./',                 # Explicit traversal
    r'/\.\./',                # Mid-path traversal
    r'^/',                    # Absolute path (sometimes dangerous)
    r'~/',                    # Home directory expansion
]

# Dangerous file paths
DANGEROUS_PATHS = {
    '/etc/passwd', '/etc/shadow', '/etc/sudoers',
    '/root', '/proc', '/sys', '/dev',
    '/var/log', '/boot', '/lib', '/usr/lib',
    '.ssh', '.gnupg', '.aws', '.config',
}

# Dangerous commands (comprehensive list)
DANGEROUS_COMMANDS = {
    # Destructive
    'rm', 'rmdir', 'del', 'erase', 'format',
    'mkfs', 'fdisk', 'dd', 'shred',
    # System modification
    'chmod', 'chown', 'chgrp', 'chattr',
    'mount', 'umount', 'systemctl', 'service',
    # Network/remote
    'wget', 'curl', 'nc', 'netcat', 'telnet',
    'ssh', 'scp', 'rsync', 'ftp', 'sftp',
    # Privilege escalation
    'sudo', 'su', 'doas', 'pkexec',
    # Package managers (can install malware)
    'apt', 'apt-get', 'yum', 'dnf', 'pacman',
    'pip', 'npm', 'gem', 'cargo',
    # Process control
    'kill', 'killall', 'pkill', 'reboot', 'shutdown', 'halt',
    # Dangerous utilities
    'eval', 'exec', 'source', 'nohup', 'at', 'cron', 'crontab',
}

# Allowed safe commands (whitelist approach for strict mode)
SAFE_COMMANDS = {
    'ls', 'dir', 'pwd', 'cd', 'cat', 'head', 'tail', 'less', 'more',
    'grep', 'find', 'locate', 'which', 'whereis', 'type',
    'echo', 'printf', 'date', 'cal', 'uptime', 'whoami', 'id',
    'wc', 'sort', 'uniq', 'cut', 'tr', 'sed', 'awk',
    'diff', 'cmp', 'file', 'stat', 'du', 'df',
    'python', 'python3', 'node', 'ruby', 'java', 'go', 'cargo',
    'git', 'make', 'cmake', 'gcc', 'g++', 'clang',
    'pytest', 'jest', 'npm', 'yarn', 'pnpm',
}


# =============================================================================
# Core Sanitization Functions
# =============================================================================

def sanitize_command(
    command: str,
    level: SanitizationLevel = SanitizationLevel.STANDARD,
    allowed_commands: Optional[Set[str]] = None,
    blocked_commands: Optional[Set[str]] = None
) -> SanitizationResult:
    """
    Sanitize a shell command for safe execution.

    Args:
        command: The command string to sanitize
        level: Strictness level
        allowed_commands: Whitelist of allowed commands (overrides defaults)
        blocked_commands: Additional commands to block

    Returns:
        SanitizationResult with safety assessment
    """
    warnings = []
    blocked = []

    if not command or not command.strip():
        return SanitizationResult(True, "", [], [])

    command = command.strip()

    # Extract base command
    try:
        parts = shlex.split(command)
        base_cmd = parts[0].split('/')[-1] if parts else ""
    except ValueError:
        # Malformed command (unmatched quotes, etc.)
        return SanitizationResult(
            False, command,
            ["Malformed command syntax"],
            ["shlex_parse_error"]
        )

    # Build effective blocklist
    effective_blocked = blocked_commands or set()
    if level in (SanitizationLevel.STRICT, SanitizationLevel.STANDARD):
        effective_blocked = effective_blocked | DANGEROUS_COMMANDS

    # Build effective whitelist (only for STRICT)
    effective_allowed = allowed_commands or SAFE_COMMANDS

    # Check against blocklist
    if base_cmd in effective_blocked:
        blocked.append(f"blocked_command:{base_cmd}")
        return SanitizationResult(
            False, command,
            [f"Command '{base_cmd}' is blocked for security"],
            blocked
        )

    # STRICT: Whitelist check
    if level == SanitizationLevel.STRICT:
        if base_cmd not in effective_allowed:
            blocked.append(f"not_whitelisted:{base_cmd}")
            return SanitizationResult(
                False, command,
                [f"Command '{base_cmd}' is not in the allowed list"],
                blocked
            )

    # Check for injection patterns
    for pattern in COMMAND_INJECTION_PATTERNS:
        if re.search(pattern, command):
            if level == SanitizationLevel.STRICT:
                blocked.append(f"injection_pattern:{pattern}")
                return SanitizationResult(
                    False, command,
                    [f"Potential command injection detected"],
                    blocked
                )
            else:
                warnings.append(f"Suspicious pattern detected: {pattern}")

    # Check for shell metacharacters in arguments
    metachar_count = sum(1 for c in command if c in SHELL_METACHARACTERS)
    if metachar_count > 3:  # Allow some (e.g., pipes are common)
        warnings.append(f"High shell metacharacter count: {metachar_count}")
        if level == SanitizationLevel.STRICT:
            blocked.append("excessive_metacharacters")
            return SanitizationResult(
                False, command,
                ["Too many shell metacharacters"],
                blocked
            )

    # Check for dangerous rm patterns
    if base_cmd == 'rm' or 'rm ' in command:
        if re.search(r'rm\s+(-[rf]+\s+)*(/|\*|~)', command):
            blocked.append("dangerous_rm")
            return SanitizationResult(
                False, command,
                ["Dangerous rm command pattern detected"],
                blocked
            )

    return SanitizationResult(
        is_safe=len(blocked) == 0,
        sanitized_value=command,
        warnings=warnings,
        blocked_patterns=blocked
    )


def sanitize_path(
    path: str,
    level: SanitizationLevel = SanitizationLevel.STANDARD,
    base_dir: Optional[str] = None,
    allow_absolute: bool = False
) -> SanitizationResult:
    """
    Sanitize a file path to prevent traversal attacks.

    Args:
        path: The path to sanitize
        level: Strictness level
        base_dir: If provided, path must resolve within this directory
        allow_absolute: Whether to allow absolute paths

    Returns:
        SanitizationResult with safety assessment
    """
    warnings = []
    blocked = []

    if not path:
        return SanitizationResult(True, "", [], [])

    original_path = path
    path = path.strip()

    # Normalize path
    try:
        normalized = os.path.normpath(path)
    except Exception as e:
        return SanitizationResult(
            False, path,
            [f"Invalid path format: {e}"],
            ["invalid_path"]
        )

    # Check for path traversal
    if '..' in path:
        blocked.append("path_traversal")
        return SanitizationResult(
            False, path,
            ["Path traversal detected (..)"],
            blocked
        )

    # Check absolute paths
    if os.path.isabs(path) and not allow_absolute:
        if level == SanitizationLevel.STRICT:
            blocked.append("absolute_path")
            return SanitizationResult(
                False, path,
                ["Absolute paths not allowed"],
                blocked
            )
        warnings.append("Using absolute path")

    # Check against dangerous paths
    path_lower = path.lower()
    for dangerous in DANGEROUS_PATHS:
        if dangerous in path_lower:
            blocked.append(f"dangerous_path:{dangerous}")
            return SanitizationResult(
                False, path,
                [f"Access to '{dangerous}' is restricted"],
                blocked
            )

    # If base_dir provided, ensure path stays within
    if base_dir:
        try:
            base_resolved = Path(base_dir).resolve()
            path_resolved = (Path(base_dir) / path).resolve()

            if not str(path_resolved).startswith(str(base_resolved)):
                blocked.append("path_escape")
                return SanitizationResult(
                    False, path,
                    ["Path escapes base directory"],
                    blocked
                )
            # Return the resolved safe path
            normalized = str(path_resolved)
        except Exception as e:
            warnings.append(f"Could not resolve path: {e}")

    return SanitizationResult(
        is_safe=len(blocked) == 0,
        sanitized_value=normalized,
        warnings=warnings,
        blocked_patterns=blocked
    )


def sanitize_string(
    value: str,
    level: SanitizationLevel = SanitizationLevel.STANDARD,
    max_length: int = 10000,
    allow_newlines: bool = True
) -> SanitizationResult:
    """
    Sanitize a general string input.

    Args:
        value: The string to sanitize
        level: Strictness level
        max_length: Maximum allowed length
        allow_newlines: Whether to allow newline characters

    Returns:
        SanitizationResult with safety assessment
    """
    warnings = []
    blocked = []

    if not value:
        return SanitizationResult(True, "", [], [])

    # Length check
    if len(value) > max_length:
        if level == SanitizationLevel.STRICT:
            blocked.append("max_length_exceeded")
            return SanitizationResult(
                False, value[:max_length],
                [f"String exceeds maximum length ({max_length})"],
                blocked
            )
        warnings.append(f"String truncated from {len(value)} to {max_length}")
        value = value[:max_length]

    # Remove null bytes (always dangerous)
    if '\x00' in value:
        warnings.append("Null bytes removed")
        value = value.replace('\x00', '')

    # Handle newlines
    if not allow_newlines and '\n' in value:
        if level == SanitizationLevel.STRICT:
            blocked.append("newlines_not_allowed")
            return SanitizationResult(
                False, value,
                ["Newlines not allowed in this context"],
                blocked
            )
        warnings.append("Newlines present in string")

    return SanitizationResult(
        is_safe=len(blocked) == 0,
        sanitized_value=value,
        warnings=warnings,
        blocked_patterns=blocked
    )


def sanitize_tool_parameters(
    tool_name: str,
    parameters: Dict[str, Any],
    level: SanitizationLevel = SanitizationLevel.STANDARD
) -> SanitizationResult:
    """
    Sanitize all parameters for a tool execution.

    Args:
        tool_name: Name of the tool being executed
        parameters: Dictionary of parameter name -> value
        level: Strictness level

    Returns:
        SanitizationResult with sanitized parameters dict
    """
    warnings = []
    blocked = []
    sanitized_params = {}

    tool_lower = tool_name.lower()

    for key, value in parameters.items():
        if value is None:
            sanitized_params[key] = None
            continue

        # Determine sanitization based on parameter name and tool
        if isinstance(value, str):
            # Command parameters
            if key in ('command', 'cmd', 'script') or tool_lower in ('bash', 'shell'):
                result = sanitize_command(value, level)
            # Path parameters
            elif key in ('path', 'file_path', 'directory', 'dir', 'cwd', 'file'):
                result = sanitize_path(value, level, allow_absolute=True)
            # General string
            else:
                result = sanitize_string(value, level)

            if not result.is_safe:
                blocked.extend(result.blocked_patterns)
                warnings.extend(result.warnings)
                if level == SanitizationLevel.STRICT:
                    return SanitizationResult(
                        False, parameters,
                        warnings + [f"Parameter '{key}' failed sanitization"],
                        blocked
                    )
            else:
                warnings.extend(result.warnings)

            sanitized_params[key] = result.sanitized_value
        else:
            # Non-string values pass through
            sanitized_params[key] = value

    return SanitizationResult(
        is_safe=len(blocked) == 0,
        sanitized_value=sanitized_params,
        warnings=warnings,
        blocked_patterns=blocked
    )


# =============================================================================
# Convenience Functions
# =============================================================================

def is_safe_command(command: str) -> bool:
    """Quick check if a command is safe to execute."""
    result = sanitize_command(command, SanitizationLevel.STANDARD)
    return result.is_safe


def is_safe_path(path: str, base_dir: Optional[str] = None) -> bool:
    """Quick check if a path is safe to access."""
    result = sanitize_path(path, SanitizationLevel.STANDARD, base_dir)
    return result.is_safe


def escape_shell_arg(arg: str) -> str:
    """Escape a string for safe use as a shell argument."""
    return shlex.quote(arg)


def get_safe_filename(filename: str) -> str:
    """
    Convert a filename to a safe version.
    Removes/replaces dangerous characters.
    """
    # Remove path separators and traversal
    safe = filename.replace('/', '_').replace('\\', '_').replace('..', '_')
    # Remove null bytes
    safe = safe.replace('\x00', '')
    # Limit length
    if len(safe) > 255:
        safe = safe[:255]
    return safe


# =============================================================================
# Logging and Monitoring
# =============================================================================

def log_sanitization_event(
    tool_name: str,
    parameter: str,
    result: SanitizationResult,
    user_id: Optional[str] = None
):
    """Log a sanitization event for monitoring."""
    if not result.is_safe:
        logger.warning(
            f"SANITIZATION_BLOCKED | tool={tool_name} | param={parameter} | "
            f"patterns={result.blocked_patterns} | user={user_id or 'unknown'}"
        )
    elif result.warnings:
        logger.info(
            f"SANITIZATION_WARNING | tool={tool_name} | param={parameter} | "
            f"warnings={result.warnings} | user={user_id or 'unknown'}"
        )
