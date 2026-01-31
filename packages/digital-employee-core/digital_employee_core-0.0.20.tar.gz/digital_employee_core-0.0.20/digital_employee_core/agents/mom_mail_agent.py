"""Minute of Meeting (MoM) Agents with Email Capabilities for Digital Employee Core.

This module provides pre-configured Agent instances for generating meeting minutes
using the Meemo platform and distributing them via email using Google Mail MCP.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    NONE
"""

from importlib.resources import files

from glaip_sdk import Agent

from digital_employee_core.connectors.mcps import google_mail_mcp, meemo_mcp
from digital_employee_core.connectors.tools import time_tool
from digital_employee_core.constants.models import GPT_5_2_MODEL_NAME

# Load base instructions from mom_agent.md
_BASE_INSTRUCTIONS_FILE = files(__package__) / "mom_agent.md"
_EMAIL_EXTENSION_FILE = files(__package__) / "mom_email_extension.md"

_base_instructions = _BASE_INSTRUCTIONS_FILE.read_text(encoding="utf-8")
_email_extension = _EMAIL_EXTENSION_FILE.read_text(encoding="utf-8")

# Combine base instructions with email extension
_MOM_MAIL_AGENT_INSTRUCTIONS = f"{_base_instructions}\n\n{_email_extension}"


mom_mail_agent = Agent(
    name="mom_mail_agent",
    description=(
        "Agent specialized in generating meeting minutes using the Meemo platform "
        "and distributing them via email using Google Mail"
    ),
    instruction=_MOM_MAIL_AGENT_INSTRUCTIONS,
    tools=[time_tool],
    mcps=[meemo_mcp, google_mail_mcp],
    model=GPT_5_2_MODEL_NAME,
)
