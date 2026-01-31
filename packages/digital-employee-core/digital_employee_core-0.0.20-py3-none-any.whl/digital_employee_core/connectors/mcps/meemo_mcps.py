"""Meemo MCPs for Digital Employee Core.

This module provides pre-configured MCP instances for Meemo services
that can be easily imported and used in Digital Employee implementations.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    NONE
"""

from glaip_sdk import MCP

meemo_mcp = MCP(
    name="digital_employee_meemo_mcp",
    description="MCP for Meemo Operation for DE",
    transport="http",
    config={"url": "https://default.com/meemo/mcp"},
)
