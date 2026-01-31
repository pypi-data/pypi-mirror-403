"""Tools package for digital employee core.

This package provides pre-configured Tool instances organized by category
for easy integration into Digital Employee implementations.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    NONE
"""

from digital_employee_core.connectors.tools.data_tools import (
    data_checker_tool,
    hybrid_vector_retrieval_tool,
    table_generator_tool,
)
from digital_employee_core.connectors.tools.development_tools import (
    e2b_sandbox_tool,
    python_repl_tool,
)
from digital_employee_core.connectors.tools.file_tools import (
    docx_reader_tool,
    download_file_tool,
    pdf_reader_tool,
    read_file_tool,
)
from digital_employee_core.connectors.tools.messaging_tools import (
    glchat_qiscus_whatsapp_tool,
)
from digital_employee_core.connectors.tools.utility_tools import (
    date_range_tool,
    time_tool,
)
from digital_employee_core.connectors.tools.web_tools import (
    browser_use_tool,
    curl_command_tool,
    web_search_tool,
)

__all__ = [
    # Web Tools
    "browser_use_tool",
    "curl_command_tool",
    "web_search_tool",
    # File Tools
    "docx_reader_tool",
    "download_file_tool",
    "pdf_reader_tool",
    "read_file_tool",
    # Development Tools
    "e2b_sandbox_tool",
    "python_repl_tool",
    # Data Tools
    "data_checker_tool",
    "hybrid_vector_retrieval_tool",
    "table_generator_tool",
    # Messaging Tools
    "glchat_qiscus_whatsapp_tool",
    # Utility Tools
    "date_range_tool",
    "time_tool",
]
