"""Escalation package for Digital Employee Core.

This package provides extensible escalation channels for handling
critical roadblocks that require human intervention.
"""

from digital_employee_core.escalation.base_escalation_channel import EscalationChannel
from digital_employee_core.escalation.escalation_config import EscalationConfig

__all__ = [
    "EscalationChannel",
    "EscalationConfig",
]
