"""Dependency management package for digital employee.

This package provides types and utilities for managing digital employee
dependencies including tools and MCPs.
"""

from digital_employee_core.digital_employee.dependencies.dependency_bundle import DependencyBundle
from digital_employee_core.digital_employee.dependencies.types import MCPConfigBuilder, ToolConfigBuilder

__all__ = [
    "DependencyBundle",
    "ToolConfigBuilder",
    "MCPConfigBuilder",
]
