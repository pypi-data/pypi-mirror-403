"""Abstract base class for escalation channels.

Authors:
    Vio Albert Ferdinand (vio.a.ferdinand@gdplabs.id)

References:
    NONE
"""

from abc import ABC, abstractmethod
from typing import Any

from glaip_sdk import MCP, Tool

from digital_employee_core.identity.identity import DigitalEmployeeSupervisor


class EscalationChannel(ABC):
    """Abstract base class for escalation channels.

    Defines the interface that all escalation channel implementations must follow.
    Each channel provides its required MCPs, tools, and prompt instructions.
    """

    @abstractmethod
    def get_required_mcps(self) -> list[MCP]:
        """Returns any MCPs required by this channel.

        Returns:
            list[MCP]: List of MCP instances required for this channel.

        Raises:
            NotImplementedError: If method is not implemented in subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def get_prompt_header(self, **kwargs: Any) -> str:
        """Returns the prompt instruction header for this escalation channel.

        Args:
            **kwargs (Any): Additional keyword arguments to be used in the prompt header.

        Returns:
            str: The prompt instruction header.

        Raises:
            NotImplementedError: If method is not implemented in subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def get_prompt_body(self, supervisor: DigitalEmployeeSupervisor, **kwargs: Any) -> str:
        """Returns the prompt instruction body for this escalation channel.

        Args:
            supervisor (DigitalEmployeeSupervisor): The supervisor to escalate to.
            **kwargs (Any): Additional keyword arguments to be used in the prompt body.

        Returns:
            str: The prompt instruction body.

        Raises:
            NotImplementedError: If method is not implemented in subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def get_required_tools(self) -> list[Tool]:
        """Returns any Tools required by this channel.

        Returns:
            list[Tool]: List of Tool instances required for this channel.

        Raises:
            NotImplementedError: If method is not implemented in subclasses.
        """
        raise NotImplementedError

    def get_prompt_instruction(self, supervisor: DigitalEmployeeSupervisor, **kwargs: Any) -> str:
        """Returns prompt instruction string consisting of the instruction header and body text.

        Args:
            supervisor (DigitalEmployeeSupervisor): The supervisor to escalate to.
            **kwargs (Any): The additional keyword arguments to be used in the prompt instruction.

        Returns:
            str: The prompt instruction string.
        """
        return f"#### {self.get_prompt_header(**kwargs)}\n\n{self.get_prompt_body(supervisor, **kwargs)}"

    def __eq__(self, other: object) -> bool:
        """Compare escalation channels by type.

        Two escalation channel instances are considered equal if they are of the same class type,
        regardless of their instance attributes.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if other is an EscalationChannel of the same type, False otherwise.
        """
        if not isinstance(other, EscalationChannel):
            return NotImplemented
        return isinstance(other, type(self))

    def __hash__(self) -> int:
        """Return hash based on the channel type.

        Returns:
            int: Hash value based on the channel's class type.
        """
        return hash(type(self))
