"""Email escalation channel implementation.

Authors:
    Vio Albert Ferdinand (vio.a.ferdinand@gdplabs.id)

References:
    NONE
"""

from typing import Any

from glaip_sdk import MCP, Tool

from digital_employee_core.connectors.mcps import google_mail_mcp
from digital_employee_core.escalation.base_escalation_channel import EscalationChannel
from digital_employee_core.identity.identity import DigitalEmployeeSupervisor


class GoogleMailMCPEscalationChannel(EscalationChannel):
    """Email-based escalation channel using Google Mail MCP."""

    def get_required_mcps(self) -> list[MCP]:
        """Returns the MCPs required for this channel.

        Returns:
            list[MCP]: List containing the Google Mail MCP.
        """
        return [google_mail_mcp]

    def get_required_tools(self) -> list[Tool]:
        """Returns any Tools required by this channel.

        Returns:
            list[Tool]: Empty list as email escalation is performed via MCP.
        """
        return []

    def get_prompt_header(self, **kwargs: Any) -> str:
        """Returns the prompt instruction header for this escalation channel.

        Args:
            **kwargs (Any): Additional keyword arguments to be used in the prompt header.

        Returns:
            str: The prompt instruction header.
        """
        return "Email Escalation via Google Mail"

    def get_prompt_body(self, supervisor: DigitalEmployeeSupervisor, **kwargs: Any) -> str:
        """Returns the prompt instruction body for this escalation channel.

        Args:
            supervisor (DigitalEmployeeSupervisor): The supervisor to send escalation emails to.
            **kwargs (Any): The additional keyword arguments to be used in the prompt body.

        Returns:
            str: The prompt instruction body.
        """
        prompt_body = (
            f"Send an escalation email to {supervisor.name} ({supervisor.email}) "
            "using the `google_mail_send_email` tool with the following HTML structure:\n\n"
            "**Subject Format:**\n"
            "  ESCALATION: [Brief, specific summary of the incident in 5-10 words]\n\n"
            "**Body Format (HTML):**\n"
            "  ```html\n"
            "  Dear <b>[SUPERVISOR_NAME]</b>,<br><br>\n\n"
            "  An escalation has been triggered that requires your attention.<br><br>\n"
            "  ---<br><br>\n"
            "  <b>Incident Details:</b><br><br>\n"
            "  1. <b>Timestamp:</b> [YYYY-MM-DD HH:MM:SS UTC]<br>\n"
            "  2. <b>Failed Action:</b> [Description of the specific action or task that failed]<br>\n"
            "  3. <b>Tools/Resources Accessed:</b> "
            "[List tools, documents, or resources used during the failed attempt]<br>\n"
            "  4. <b>Escalation Reason:</b> "
            "[Clear explanation of why this action failed and why human intervention is required]<br><br>\n"
            "  ---<br><br>\n"
            "  Best regards,<br><br>\n"
            "  --<br>\n"
            "  [DE Name]<br>\n"
            "  Digital Employee\n"
            "  ```\n"
        )
        return prompt_body
