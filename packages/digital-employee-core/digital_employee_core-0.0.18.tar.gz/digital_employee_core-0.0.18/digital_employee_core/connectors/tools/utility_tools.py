"""Utility tools for Digital Employee Core.

This module provides pre-configured Tool instances for utility operations
that can be easily imported and used in Digital Employee implementations.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    NONE
"""

from glaip_sdk import Tool

# Date Range Tool
try:
    date_range_tool: Tool = Tool.from_native("date_range_tool")
except Exception as e:
    raise ImportError(f"Failed to load native tool 'date_range_tool': {e}") from e

# Time Tool
try:
    time_tool: Tool = Tool.from_native("time_tool")
except Exception as e:
    raise ImportError(f"Failed to load native tool 'time_tool': {e}") from e
