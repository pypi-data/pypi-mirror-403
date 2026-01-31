"""Escalation configuration model.

Authors:
    Vio Albert Ferdinand (vio.a.ferdinand@gdplabs.id)

References:
    NONE
"""

from pydantic import BaseModel, ConfigDict, Field

from digital_employee_core.escalation.base_escalation_channel import EscalationChannel


class EscalationConfig(BaseModel):
    """Configuration for escalation behavior.

    Controls whether escalation is enabled and which channels are active.

    Attributes:
        enabled: Whether escalation is enabled. Defaults to True.
        channels: List of escalation channel instances. Defaults to empty list.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    enabled: bool = Field(default=True, description="Enable/disable escalation")
    channels: list[EscalationChannel] = Field(
        default_factory=list,
        description="List of escalation channel instances",
    )
