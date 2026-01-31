"""File operation tools for Digital Employee Core.

This module provides pre-configured Tool instances for file operations
that can be easily imported and used in Digital Employee implementations.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    NONE
"""

from glaip_sdk import Tool

# DOCX Reader Tool
try:
    docx_reader_tool: Tool = Tool.from_native("docx_reader_tool")
except Exception as e:
    raise ImportError(f"Failed to load native tool 'docx_reader_tool': {e}") from e

# PDF Reader Tool
try:
    pdf_reader_tool: Tool = Tool.from_native("pdf_reader_tool")
except Exception as e:
    raise ImportError(f"Failed to load native tool 'pdf_reader_tool': {e}") from e

# Read File Tool
try:
    read_file_tool: Tool = Tool.from_native("read_file")
except Exception as e:
    raise ImportError(f"Failed to load native tool 'read_file': {e}") from e

# Download File Tool
try:
    download_file_tool: Tool = Tool.from_native("download_file")
except Exception as e:
    raise ImportError(f"Failed to load native tool 'download_file': {e}") from e
