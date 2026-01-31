"""Minute of Meeting (MoM) Agents for Digital Employee Core.

This module provides pre-configured Agent instances for generating meeting minutes
using the Meemo platform.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    NONE
"""

from importlib.resources import files

from glaip_sdk import Agent

from digital_employee_core.connectors.mcps import meemo_mcp
from digital_employee_core.connectors.tools import time_tool
from digital_employee_core.constants.models import GPT_5_2_MODEL_NAME

# Load instructions from markdown file
_INSTRUCTIONS_FILE = files(__package__) / "mom_agent.md"
_MOM_AGENT_INSTRUCTIONS = _INSTRUCTIONS_FILE.read_text(encoding="utf-8")


mom_agent = Agent(
    name="mom_agent",
    description="Agent specialized in generating and managing meeting minutes using the Meemo platform",
    instruction=_MOM_AGENT_INSTRUCTIONS,
    tools=[time_tool],
    mcps=[meemo_mcp],
    model=GPT_5_2_MODEL_NAME,
)
