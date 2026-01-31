"""Custom tool for sending WhatsApp messages via GLChat Qiscus Messaging API.

Authors:
    Muhammad Wachid Kusuma (muhammad.w.kusuma@gdplabs.id)
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    [1] GLChat Messaging - https://github.com/GDP-ADMIN/glchat-messaging/blob/main/applications/glchat-messaging/glchat_messaging/api/router/qiscus.py
"""

from typing import Any

import requests
from gllm_plugin.tools import tool_plugin
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

REQUEST_TIMEOUT_SECONDS = 30


class GLChatQiscusWhatsAppToolInput(BaseModel):
    """Input schema for GLChat Qiscus WhatsApp tool."""

    recipient_phone_number: str = Field(
        ..., description="The phone number of the message recipient (e.g., +6281234567890)"
    )
    message: str = Field(..., description="The message content to send")


class QiscusConfig(BaseModel):
    """Configuration schema for Qiscus authentication."""

    base_url: str = Field(..., description="The base URL for the GLChat messaging API")
    api_key: str = Field(..., description="API key for Qiscus authentication")
    channel_id: str = Field(..., description="Channel ID for Qiscus provider config")


@tool_plugin(version="1.0.0")
class GLChatQiscusWhatsAppTool(BaseTool):
    """Tool for sending WhatsApp messages via GLChat messaging API."""

    name: str = "glchat_qiscus_whatsapp_tool"
    description: str = "Send WhatsApp messages via GLChat messaging API to phone number"
    args_schema: type[BaseModel] = GLChatQiscusWhatsAppToolInput
    tool_config_schema: type[BaseModel] = QiscusConfig

    def _run(self, recipient_phone_number: str, message: str, config: RunnableConfig = None, **_kwargs: Any) -> str:
        """Send a WhatsApp message via GLChat messaging API.

        Args:
            recipient_phone_number (str): Phone number of the recipient.
            message (str): Message content to send.
            config (RunnableConfig): Runnable configuration containing tool configuration.
            **_kwargs (Any): Additional keyword arguments.

        Returns:
            str: Result message indicating success or failure.
        """
        tool_config = self.get_tool_config(config)
        base_url = tool_config.base_url.rstrip("/")
        url = f"{base_url}/qiscus/send-message"

        headers = {"x-api-key": tool_config.api_key, "Content-Type": "application/json"}

        payload = {
            "recipient_phone_number": recipient_phone_number,
            "message": message,
            "provider_config": {"channel_id": tool_config.channel_id},
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()

            return f"Message sent successfully to {recipient_phone_number}. Response: {response.text}"

        except requests.HTTPError as e:
            return f"Failed to send message. Status code: {e.response.status_code}, Response: {e.response.text}"

        except Exception as e:
            return f"Error sending message: {str(e)}"
