"""Agent configuration models for digital employee.

This module provides classes for managing agent-specific configurations
such as step limits and delegation depth.

Authors:
    Vio Albert Ferdinand (vio.a.ferdinand@gdplabs.id)

References:
    NONE
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AgentConfigKeys(StrEnum):
    """Configuration key constants for agent configuration.

    Attributes:
        STEP_LIMIT_CONFIG (str): The step limit configuration key.
        MEMORY (str): The memory provider configuration key.
    """

    STEP_LIMIT_CONFIG = "step_limit_config"
    MEMORY = "memory"


class StepLimitConfig(BaseModel):
    """Represents the step limit configuration for the digital employee.

    This configuration is used to limit the number of steps the digital
    employee can take and the maximum delegation depth.

    Attributes:
        max_steps (int | None): The maximum number of steps the digital employee can take.
        max_delegation_depth (int | None): The maximum delegation depth the digital employee can use.
    """

    model_config = ConfigDict(extra="forbid")

    max_steps: int | None = Field(default=None, ge=1, le=1000)
    max_delegation_depth: int | None = Field(default=None, ge=0, le=10)

    def to_dict(self) -> dict[str, int | float]:
        """Serialize the step limit configuration for the SDK.

        Returns:
            dict[str, int | float]: Configuration dictionary with only provided values.
        """
        return self.model_dump(exclude_none=True)


class MemoryProvider(StrEnum):
    """Supported memory providers for agent_config["memory"]."""

    MEM0 = "mem0"
