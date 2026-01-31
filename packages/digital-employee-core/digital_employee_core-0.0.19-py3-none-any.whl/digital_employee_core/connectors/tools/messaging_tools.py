"""Messaging tools for Digital Employee Core.

This module provides pre-configured Tool instances for messaging operations
that can be easily imported and used in Digital Employee implementations.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    NONE
"""

from glaip_sdk import Tool

from digital_employee_core.connectors.tools.glchat_qiscus_whatsapp_tools import GLChatQiscusWhatsAppTool

# GLChat Qiscus WhatsApp Tool
glchat_qiscus_whatsapp_tool: Tool = Tool.from_langchain(GLChatQiscusWhatsAppTool)
