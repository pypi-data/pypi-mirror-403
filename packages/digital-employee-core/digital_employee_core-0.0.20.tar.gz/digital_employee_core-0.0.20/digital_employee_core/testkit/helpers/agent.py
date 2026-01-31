"""Common utilities for agent tests.

Authors:
    Gunawan Christianto (gunawan.christianto@gdplabs.id)

References:
    NONE
"""

from glaip_sdk import Agent

from .client_manager import ClientManager


def find_agent_by_name(name: str) -> Agent:
    """Find an agent by exact name match.

    Args:
        name (str): The name of the agent to find.

    Returns:
        Agent: The agent if found.

    Raises:
        ValueError: If no agent with the given name is found.
    """
    client = ClientManager.get_client()
    for a in client.find_agents(name):
        if a.name == name:
            return a
    raise ValueError(f"Agent with name '{name}' not found")
