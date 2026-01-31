"""Web operation tools for Digital Employee Core.

This module provides pre-configured Tool instances for web operations
that can be easily imported and used in Digital Employee implementations.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    NONE
"""

from glaip_sdk import Tool

# Browser Use Tool
try:
    browser_use_tool: Tool = Tool.from_native("browser_use_tool")
except Exception as e:
    raise ImportError(f"Failed to load native tool 'browser_use_tool': {e}") from e

# Web Search Tool
try:
    web_search_tool: Tool = Tool.from_native("web_search_tool")
except Exception as e:
    raise ImportError(f"Failed to load native tool 'web_search_tool': {e}") from e

# cURL Command Tool
try:
    curl_command_tool: Tool = Tool.from_native("curl_command_tool")
except Exception as e:
    raise ImportError(f"Failed to load native tool 'curl_command_tool': {e}") from e
