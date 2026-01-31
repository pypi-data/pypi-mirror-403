"""Schedule configuration model.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    NONE
"""

from glaip_sdk.models.schedule import ScheduleConfig
from pydantic import BaseModel, ConfigDict, Field


class ScheduleItemConfig(BaseModel):
    """Configuration for a single scheduled task.

    Wraps a schedule configuration with its associated input/description.

    Attributes:
        schedule_config (ScheduleConfig): The schedule configuration (cron or ScheduleConfig object).
        input (str): Description of the scheduled task to be executed.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    schedule_config: ScheduleConfig = Field(description="The schedule configuration")
    input: str = Field(description="Description of the scheduled task to be executed")
