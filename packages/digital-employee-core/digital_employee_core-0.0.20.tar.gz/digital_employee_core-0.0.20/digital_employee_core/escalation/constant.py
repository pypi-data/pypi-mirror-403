"""Constants for escalation functionality.

This module contains constant strings used for escalation-related warnings
and messages throughout the digital employee core.

Authors:
    Vio Albert Ferdinand (vio.a.ferdinand@gdplabs.id)

References:
    NONE
"""

ESCALATION_NO_CHANNELS_PROMPT_WARNING = (
    "Escalation is enabled but no escalation channels are configured; skipping escalation prompt. "
    "Set channels via escalation_config.channels or DigitalEmployee.add_escalation_channel()."
)

ESCALATION_NO_CHANNELS_DEPENDENCIES_WARNING = (
    "Escalation is enabled but no escalation channels are configured; skipping MCP/Tool building. "
    "Set channels via escalation_config.channels or DigitalEmployee.add_escalation_channel()."
)

ESCALATION_PROMPT = """### [CRITICAL] ESCALATION PROTOCOL

You MUST immediately escalate to human supervision when ANY of the following situations occur:
1. **Tool/Technical Failures**
   - Any tool returns an error or exception that cannot be automatically retried
   - A tool times out after the maximum retry attempts
   - Required tools are unavailable, misconfigured, or returning invalid responses
   - Integration with external services fails (API errors, authentication failures, etc.)

2. **Specific situations defined in your instructions**
   - ANY situation explicitly marked as requiring escalation in your instructions

**IMPORTANT:**
- Do NOT ask for confirmation or permission before escalating - proceed directly
- NEVER attempt to bypass, ignore, or work around a critical escalation trigger

Escalation Channels:
"""
