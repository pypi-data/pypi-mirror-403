"""Data processing tools for Digital Employee Core.

This module provides pre-configured Tool instances for data processing and retrieval
that can be easily imported and used in Digital Employee implementations.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    NONE
"""

from glaip_sdk import Tool

# Data Checker Tool
try:
    data_checker_tool: Tool = Tool.from_native("data_checker")
except Exception as e:
    raise ImportError(f"Failed to load native tool 'data_checker': {e}") from e

# Hybrid Vector Retrieval Tool
try:
    hybrid_vector_retrieval_tool: Tool = Tool.from_native("hybrid_vector_retrieval_tool")
except Exception as e:
    raise ImportError(f"Failed to load native tool 'hybrid_vector_retrieval_tool': {e}") from e

# Table Generator Tool
try:
    table_generator_tool: Tool = Tool.from_native("table_generator")
except Exception as e:
    raise ImportError(f"Failed to load native tool 'table_generator': {e}") from e
