"""Dependency management types for digital employee.

This module provides type definitions for building tool and MCP configurations.

Authors:
    Vio Albert Ferdinand (vio.a.ferdinand@gdplabs.id)

References:
    NONE
"""

from typing import Any, Callable

from glaip_sdk import MCP, Tool

from digital_employee_core.configuration.configuration import DigitalEmployeeConfiguration

ToolConfigBuilder = Callable[[list[DigitalEmployeeConfiguration], list[Tool]], dict[str, dict[str, Any]]]
"""Type alias for functions that build tool configurations."""

MCPConfigBuilder = Callable[[list[DigitalEmployeeConfiguration], list[MCP]], dict[str, dict[str, Any]]]
"""Type alias for functions that build MCP configurations."""
