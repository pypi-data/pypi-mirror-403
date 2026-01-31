"""Development and execution tools for Digital Employee Core.

This module provides pre-configured Tool instances for code execution and development
that can be easily imported and used in Digital Employee implementations.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    NONE
"""

from glaip_sdk import Tool

# Python REPL Tool
try:
    python_repl_tool: Tool = Tool.from_native("python_repl")
except Exception as e:
    raise ImportError(f"Failed to load native tool 'python_repl': {e}") from e

# E2B Sandbox Tool
try:
    e2b_sandbox_tool: Tool = Tool.from_native("e2b_sandbox_tool")
except Exception as e:
    raise ImportError(f"Failed to load native tool 'e2b_sandbox_tool': {e}") from e
