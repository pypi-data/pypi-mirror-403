"""Agents package for digital employee core.

This package provides pre-configured Agent instances for various specialized tasks.
"""

from digital_employee_core.agents.mom_agent import mom_agent
from digital_employee_core.agents.mom_docs_agent import mom_docs_agent
from digital_employee_core.agents.mom_mail_agent import mom_mail_agent

__all__ = [
    "mom_agent",
    "mom_mail_agent",
    "mom_docs_agent",
]
