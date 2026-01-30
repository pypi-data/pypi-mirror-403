"""
Security hooks for PreToolUse integration with Claude Code.

Provides intelligent detection of dangerous patterns, bypass attempts,
and encoded commands that AI agents might try to execute.
"""

import base64
import binascii
import re
import urllib.parse
from typing import Optional, Tuple


# Dangerous command patterns
DANGEROUS_PATTERNS = [
    # File destruction
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+~",
    r"rm\s+-rf\s+\*",
    r"del\s+/[sS]\s+",
    # System modification
    r"sudo\s+rm",
    r"chmod\s+777",
    r"chown\s+root",
    # Network exfiltration
    r"curl.*\|\s*bash",
    r"wget.*\|\s*sh",
    r"nc\s+-[el]",
    r"netcat\s+-[el]",
    # Code execution
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__\s*\(",
    # Shell spawning
    r"os\.system\s*\(",
    r"subprocess\.call\s*\(",
    r"subprocess\.run\s*\([^,]*shell\s*=\s*True",
    # Privilege escalation
    r"sudo\s+su",
    r"sudo\s+-i",
    # Package installation (potential malware)
    r"pip\s+install\s+.*-i\s+http",  # Custom index
    r"npm\s+install.*--registry",
    # Docker escapes
    r"docker\s+run.*--privileged",
    r"docker\s+exec.*root",
]


# Encoding bypass patterns
ENCODING_PATTERNS = {
    "base64": r"(?:echo|cat)\s+[A-Za-z0-9+/=]{20,}\s*\|\s*base64\s+-d",
    "hex": r"\\x[0-9a-fA-F]{2}",
    "octal": r"\\[0-7]{3}",
    "unicode": r"\\u[0-9a-fA-F]{4}",
    "url": r"%[0-9a-fA-F]{2}",
}


# Environment variable bypass patterns
ENV_BYPASS_PATTERNS = [
    r"\$\{.*:-.*\}",  # ${VAR:-default} parameter expansion
    r"\$\([^)]+\)",  # Command substitution
    r"`[^`]+`",  # Backtick command substitution
]


def detect_dangerous_command(command: str) -> Tuple[bool, Optional[str]]:
    """
    Detect dangerous command patterns.

    Args:
        command: The command string to analyze

    Returns:
        (is_dangerous, reason) tuple
    """
    # Check direct dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, f"Dangerous pattern detected: {pattern}"

    return False, None


def detect_encoding_bypass(command: str) -> Tuple[bool, Optional[str]]:
    """
    Detect encoded commands that might be bypass attempts.

    Args:
        command: The command string to analyze

    Returns:
        (is_bypass, decoded_content) tuple
    """
    # Check for base64 encoding
    if re.search(ENCODING_PATTERNS["base64"], command):
        # Try to decode and check for dangerous patterns
        try:
            # Extract base64 content
            match = re.search(r"[A-Za-z0-9+/=]{20,}", command)
            if match:
                decoded = base64.b64decode(match.group()).decode('utf-8', errors='ignore')
                is_dangerous, reason = detect_dangerous_command(decoded)
                if is_dangerous:
                    return True, f"Base64-encoded dangerous command: {decoded[:50]}..."
        except (binascii.Error, UnicodeDecodeError):
            pass

    # Check for hex encoding
    hex_matches = re.findall(ENCODING_PATTERNS["hex"], command)
    if len(hex_matches) > 5:  # Multiple hex characters
        try:
            decoded = bytes.fromhex(''.join(m[2:] for m in hex_matches)).decode('utf-8', errors='ignore')
            is_dangerous, reason = detect_dangerous_command(decoded)
            if is_dangerous:
                return True, f"Hex-encoded dangerous command: {decoded[:50]}..."
        except (ValueError, UnicodeDecodeError):
            pass

    # Check for URL encoding
    if "%" in command and re.search(ENCODING_PATTERNS["url"], command):
        try:
            decoded = urllib.parse.unquote(command)
            if decoded != command:  # Something was decoded
                is_dangerous, reason = detect_dangerous_command(decoded)
                if is_dangerous:
                    return True, f"URL-encoded dangerous command: {decoded[:50]}..."
        except Exception:
            pass

    return False, None


def detect_env_bypass(command: str) -> Tuple[bool, Optional[str]]:
    """
    Detect environment variable manipulation bypass attempts.

    Args:
        command: The command string to analyze

    Returns:
        (is_bypass, reason) tuple
    """
    for pattern in ENV_BYPASS_PATTERNS:
        if re.search(pattern, command):
            # Check if the substitution might hide dangerous commands
            # Extract the substituted part
            match = re.search(pattern, command)
            if match:
                substitution = match.group()
                return True, f"Suspicious environment variable manipulation: {substitution}"

    return False, None


def detect_obfuscation(command: str) -> Tuple[bool, Optional[str]]:
    """
    Detect command obfuscation techniques.

    Args:
        command: The command string to analyze

    Returns:
        (is_obfuscated, reason) tuple
    """
    # Check for excessive quoting/escaping
    quote_count = command.count("'") + command.count('"') + command.count("\\")
    if quote_count > len(command) * 0.3:  # 30% of characters are quotes/escapes
        return True, "Excessive quoting/escaping detected (potential obfuscation)"

    # Check for character concatenation obfuscation
    # Example: "r""m" + " " + "-rf"
    if re.search(r'["\'][^"\']{1,2}["\'](\s*\+\s*["\'][^"\']{1,2}["\']){3,}', command):
        return True, "String concatenation obfuscation detected"

    # Check for variable name obfuscation
    if re.search(r'[_O0Il]{5,}', command):  # Variables like ___OO0Il
        return True, "Obfuscated variable names detected"

    return False, None


def analyze_command(command: str, tool_name: str = "bash") -> Tuple[bool, str]:
    """
    Comprehensive command analysis for security threats.

    Args:
        command: The command to analyze
        tool_name: Name of the tool being used (bash, python, etc.)

    Returns:
        (is_safe, reason) tuple. If not safe, reason explains why.
    """
    warnings = []

    # 1. Check direct dangerous patterns (BLOCK)
    is_dangerous, reason = detect_dangerous_command(command)
    if is_dangerous:
        return False, f"BLOCK: {reason}"

    # 2. Check encoding bypass attempts (BLOCK)
    is_bypass, decoded = detect_encoding_bypass(command)
    if is_bypass:
        return False, f"BLOCK: {decoded}"

    # 3. Check environment variable bypasses (BLOCK)
    is_env_bypass, reason = detect_env_bypass(command)
    if is_env_bypass:
        return False, f"BLOCK: {reason}"

    # 4. Check obfuscation (WARNING only - no block)
    is_obfuscated, reason = detect_obfuscation(command)
    if is_obfuscated:
        warnings.append(f"WARNING: {reason}")

    # 5. Tool-specific checks
    if tool_name == "bash" or tool_name == "sh":
        # Check for pipe chains that might hide intent (WARNING only)
        pipe_count = command.count("|")
        if pipe_count >= 4:  # Increased threshold to reduce false positives
            warnings.append(f"WARNING: Complex pipe chain detected ({pipe_count} pipes)")

    if tool_name == "python":
        # Check for dangerous Python patterns (BLOCK)
        if "__import__" in command or "exec(" in command or "eval(" in command:
            return False, "BLOCK: Dangerous Python code execution detected"

    # If we have warnings but no blocks, allow with warnings
    if warnings:
        return True, "; ".join(warnings)

    return True, "Command appears safe"


def suggest_safe_alternative(command: str) -> Optional[str]:
    """
    Suggest safer alternatives for dangerous commands.

    Args:
        command: The dangerous command

    Returns:
        Suggested safe alternative or None if no alternative available
    """
    # rm -rf suggestions
    if re.search(r"rm\s+-rf", command):
        return "Consider using 'trash' or 'rm -i' for interactive deletion, or be more specific with paths"

    # os.system suggestions
    if "os.system" in command:
        return "Use subprocess.run() with shell=False and proper argument escaping instead"

    # eval/exec suggestions
    if "eval(" in command or "exec(" in command:
        return "Avoid eval/exec - use safer alternatives like ast.literal_eval() or explicit function calls"

    # sudo suggestions
    if re.search(r"sudo\s+", command):
        return "Run commands with minimum required privileges - avoid sudo when possible"

    # chmod 777 suggestions
    if "chmod 777" in command or "chmod -R 777" in command:
        return "Use more restrictive permissions like 755 or 644 instead of 777"

    return None
