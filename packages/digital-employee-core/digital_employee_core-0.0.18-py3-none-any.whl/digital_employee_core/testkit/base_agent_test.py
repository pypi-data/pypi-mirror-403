"""Base classes for agent integration tests.

Provides common functionality for testing agents:
    ToolCapturingRenderer: Captures tools/delegations and their success status
    BaseAgentTest: Base test class with common setup and assertion methods

Prerequisites:
    - Agents must be deployed and accessible via the GLAIP SDK before running tests
    - Test classes must override the AGENT class attribute with the deployed agent instance

Authors:
    Vio Albert Ferdinand (vio.a.ferdinand@gdplabs.id)
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
    Saul Sayers (saul.sayers@gdplabs.id)
    Richard Gunawan (richard.gunawan@gdplabs.id)

References:
    https://github.com/GDP-ADMIN/glaip-sdk/blob/bbfeb3ea5a0c095c843c34a77e753f6832bd86c7/python/glaip-sdk/examples/auto_check_tool/test_agent_simple.py
"""

import logging
import time
from enum import StrEnum, auto
from io import StringIO
from typing import Any, TypedDict

from glaip_sdk import Agent
from glaip_sdk.exceptions import AgentTimeoutError
from glaip_sdk.utils.rendering.models import Step
from glaip_sdk.utils.run_renderer import RichStreamRenderer, RunStats
from rich.console import Console

from digital_employee_core.testkit.constants import SEPARATOR_THICK, SEPARATOR_THIN


class ToolStatus(StrEnum):
    """Enumeration of tool status values."""

    SUCCESS = auto()
    FAILED = auto()
    UNKNOWN = auto()


class ToolCall(TypedDict):
    """Tool/delegation call data."""

    status: ToolStatus
    data: Step


class ToolCapturingRenderer(RichStreamRenderer):
    """Captures tools/delegations and their success status during agent execution."""

    def __init__(self, verbose: bool = False):
        """Initialize the tool capturing renderer with silent console."""
        if not verbose:
            silent_console = Console(file=StringIO(), quiet=True, force_terminal=False)
            super().__init__(console=silent_console, verbose=verbose)
        else:
            super().__init__(verbose=verbose)
        self.tool_calls: list[ToolCall] = []
        self.response_text = ""

    def on_complete(self, stats: RunStats) -> None:
        """Extract tools/delegations and their success status from steps.

        Args:
            stats (RunStats): The run stats object containing the step information.
        """
        try:
            for step in self.steps.by_id.values():
                if step.kind not in ["tool", "delegate"]:
                    continue

                has_error = hasattr(step, "status") and step.status == "failed"
                is_complete = hasattr(step, "status") and step.status == "complete"
                has_output = hasattr(step, "output") and step.output is not None

                if has_error:
                    status = ToolStatus.FAILED
                elif is_complete or has_output:
                    status = ToolStatus.SUCCESS
                else:
                    status = ToolStatus.UNKNOWN

                self.tool_calls.append(
                    {
                        "status": status,
                        "data": step,
                    }
                )

            if hasattr(self.state, "buffer"):
                self.response_text = "".join(self.state.buffer).strip()

            super().on_complete(stats)

        except Exception as e:
            logging.error("Exception in on_complete: %s", e)
            raise


class AssertionType(StrEnum):
    """Enumeration of assertion types."""

    EXACT = auto()
    KEYWORDS = auto()


class Assertion(TypedDict):
    """Assertion for agent integration tests."""

    type: AssertionType
    values: list[Any]


class ToolCallAssertion(TypedDict):
    """Tool call assertion for agent integration tests."""

    name: str
    params: dict[str, Assertion]


ToolCallResults = tuple[list[ToolCallAssertion], list[ToolCallAssertion], list[ToolCallAssertion], list[ToolCall]]


class BaseAgentTest:
    """Base class for agent integration tests."""

    # Subclasses should override these
    AGENT: Agent | None = None  # Agent instance to test
    TIMEOUT = 600  # Default 10 minutes

    QUESTION_PRINT_LENGTH = 80
    ERROR_MESSAGE_PRINT_LENGTH = 100

    @classmethod
    def setup_class(cls):
        """Set up agent.

        Raises:
            ValueError: If TIMEOUT is not greater than 0,
            RuntimeError: If AGENT is not set in test class.
        """
        if cls.TIMEOUT <= 0:
            raise ValueError(f"TIMEOUT must be greater than 0, got {cls.TIMEOUT}")

        if cls.AGENT is None:
            raise RuntimeError("AGENT must be set in test class")

        logging.info("Connected to agent: %s (ID: %s)", cls.AGENT.name, cls.AGENT.id)

    def run_agent_test(
        self,
        question: str,
        expected_tool_calls: list[ToolCallAssertion],
        expected_response: Assertion,
        chat_history: list[str] | None = None,
        configurations: list | None = None,
    ) -> str:
        """Test agent execution.

        Args:
            question (str): The question to send to the agent (can contain placeholders).
            expected_tool_calls (list[ToolCallAssertion]): The expected tool calls for the agent.
            expected_response (Assertion): The expected response for the agent.
            chat_history (list[str] | None): The chat history to send to the agent.
            configurations (list | None): Optional list of configurations to pass to the agent.

        Returns:
            str: The response text from the agent.
        """
        self._print_phase_header("SETUP")
        self._setup_test_data()

        # Get replacements after setup (so setup data is available)
        replacements = self._get_replacements()

        # Format question and expected_tool_calls with replacements
        if replacements:
            question = question.format(**replacements)
            self._replace_expected_tool_calls(expected_tool_calls, **replacements)
            self._replace_assertion(expected_response, **replacements)

        try:
            # Test execution phase
            self._print_phase_header("TEST EXECUTION")
            self._print_test_inputs(question, expected_tool_calls, expected_response)

            logging.info("Starting agent execution...")

            renderer = ToolCapturingRenderer(verbose=True)
            response_text, error_occurred, error_message = self._run_agent_with_error_handling(
                question, renderer, chat_history, configurations
            )

            # Use response from return value or renderer
            if not response_text and renderer.response_text:
                response_text = renderer.response_text

            actual_tool_calls = renderer.tool_calls
            logging.info("Actual tool calls: %d", len(actual_tool_calls))

            self._print_agent_response(response_text)

            tool_results = self._categorize_tool_calls(actual_tool_calls, expected_tool_calls)
            self._print_tool_results(actual_tool_calls, expected_tool_calls, tool_results)

            self._assert_tool_calls(tool_results, error_occurred, error_message)
            self._assert_response(response_text, expected_response)

            return response_text

        finally:
            # Cleanup: Remove test data
            self._print_phase_header("CLEANUP")
            self._cleanup_test_data()
            logging.info(SEPARATOR_THICK)

    def _setup_test_data(self, **kwargs) -> None:
        """Set up test data. Override in subclass if needed."""
        pass

    def _cleanup_test_data(self) -> None:
        """Clean up test data. Override in subclass if needed."""
        pass

    def _get_replacements(self) -> dict[str, Any] | None:
        """Get replacement values for formatting test case.

        This method is called after _setup_test_data(), so setup data is available.
        Override in subclass to provide replacement values.

        Returns:
            dict[str, Any] | None: Replacement values or None if no replacements needed.
        """
        return None

    def _replace_expected_tool_calls(self, expected_tool_calls: list[ToolCallAssertion], **kwargs: Any) -> None:
        """Replace expected tool calls with actual values.

        Args:
            expected_tool_calls (list[ToolCallAssertion]): The expected tool calls.
            **kwargs (Any): The keyword arguments to replace the expected tool calls.
        """
        for tool_call in expected_tool_calls:
            # Replace Name
            tool_call["name"] = tool_call["name"].format(**kwargs)

            # Replace Params
            params = tool_call["params"]
            for param in params.values():
                self._replace_assertion(param, **kwargs)

    def _replace_assertion(self, assertion: Assertion, **kwargs: Any) -> None:
        """Replace placeholders in assertion values with actual values.

        Args:
            assertion (Assertion): The assertion specification.
            **kwargs (Any): The keyword arguments to replace within the assertion values.
        """
        if not assertion or "values" not in assertion:
            return

        assertion["values"] = [
            value.format(**kwargs) if isinstance(value, str) else value for value in assertion["values"]
        ]

    def _print_phase_header(self, phase: str) -> None:
        """Print phase header in uppercase.

        Args:
            phase (str): The phase name.
        """
        logging.info("\n" + SEPARATOR_THICK)
        logging.info("%s PHASE", phase.upper())
        logging.info(SEPARATOR_THICK)

    def _print_test_inputs(
        self, question: str, expected_tool_calls: list[ToolCallAssertion], expected_response: Assertion
    ) -> None:
        """Print agent requirements.

        Args:
            question (str): The question to send to the agent.
            expected_tool_calls (list[ToolCallAssertion]): The expected tool calls for the agent.
            expected_response (Assertion): The expected response for the agent.
        """
        logging.info("\n" + SEPARATOR_THIN)
        logging.info("Question: %s...", question[: self.QUESTION_PRINT_LENGTH])
        logging.info("Expected tool calls: %d", len(expected_tool_calls))
        logging.info("Expected response: %s", expected_response)

    def _run_agent_with_error_handling(
        self,
        question: str,
        renderer: ToolCapturingRenderer,
        chat_history: list[str] | None = None,
        configurations: list | None = None,
    ) -> tuple[str, bool, str]:
        """Run agent and handle errors.

        Args:
            question (str): The question to send to the agent.
            renderer (ToolCapturingRenderer): The renderer to capture tools.
            chat_history (list[str] | None): The chat history to send to the agent.
            configurations (list | None): Optional list of configurations to pass to the agent.

        Returns:
            tuple[str, bool, str]: Response text, error occurred flag, and error message.
        """
        error_occurred = False
        error_message = ""
        response_text = ""

        try:
            start_time = time.time()
            logging.info("   Sending request to agent...")
            response_text = self.AGENT.run(
                message=question, renderer=renderer, chat_history=chat_history, runtime_config=configurations
            )
            elapsed = time.time() - start_time
            logging.info("Agent execution completed in %.1fs", elapsed)
        except AgentTimeoutError as e:
            error_occurred = True
            error_message = f"Timeout after {e.timeout_seconds}s"
            logging.warning("Agent timeout: %s", error_message)
            logging.warning("Tool calls captured before timeout: %d", len(renderer.tool_calls))
        except Exception as e:
            error_occurred = True
            error_message = f"{type(e).__name__}: {str(e)[: self.ERROR_MESSAGE_PRINT_LENGTH]}"
            logging.warning("Error: %s", error_message)
            logging.warning("Tool calls captured before error: %d", len(renderer.tool_calls))

        return response_text, error_occurred, error_message

    def _print_agent_response(self, response_text: str) -> None:
        """Print agent response.

        Args:
            response_text (str): The response text from the agent.
        """
        if response_text and response_text.strip():
            logging.info("\n" + SEPARATOR_THIN)
            logging.info("Agent Response (%d chars)", len(response_text))
            logging.info(SEPARATOR_THIN)
            logging.info("%s\n", response_text)
            logging.info(SEPARATOR_THIN)
        else:
            logging.warning("No response captured")

    def _categorize_tool_calls(
        self,
        actual_tool_calls: list[ToolCall],
        expected_tool_calls: list[ToolCallAssertion],
    ) -> ToolCallResults:
        """Categorize tool calls into passing, failed, missing, and extra.

        Args:
            actual_tool_calls (list[ToolCall]): List of actual tool calls.
            expected_tool_calls (list[ToolCallAssertion]): List of expected tool call assertions.

        Returns:
            ToolCallResults:
                passing: Tool calls that were used and succeeded.
                failed: Tool calls that were used and failed.
                missing: Tool calls that were expected but not used.
                extra: Tool calls that were used but not expected.
        """
        passing_tool_calls: list[ToolCallAssertion] = []
        failed_tool_calls: list[ToolCallAssertion] = []
        missing_tool_calls: list[ToolCallAssertion] = []

        actual_tool_names = {tool_call["data"].name for tool_call in actual_tool_calls}
        expected_tool_names = {tool_call["name"] for tool_call in expected_tool_calls}

        # Categorize tools
        for expected_tool_call in expected_tool_calls:
            expected_tool_name = expected_tool_call["name"]
            if expected_tool_name not in actual_tool_names:
                missing_tool_calls.append(expected_tool_call)
                continue

            is_passing_tool_call = False
            for actual_tool_call in actual_tool_calls:
                if (
                    actual_tool_call["data"].name == expected_tool_name
                    and actual_tool_call["status"] == ToolStatus.SUCCESS
                    and self._assert_tool_call_params(actual_tool_call, expected_tool_call)
                ):
                    is_passing_tool_call = True
                    break

            if is_passing_tool_call:
                passing_tool_calls.append(expected_tool_call)
            else:
                failed_tool_calls.append(expected_tool_call)

        extra_tool_calls = [
            tool_call for tool_call in actual_tool_calls if tool_call["data"].name not in expected_tool_names
        ]

        return passing_tool_calls, failed_tool_calls, missing_tool_calls, extra_tool_calls

    def _assert_tool_call_params(self, actual_tool_call: ToolCall, expected_tool_call: ToolCallAssertion) -> bool:  # noqa: PLR0911
        """Assert that tool was called with expected parameters.

        Args:
            actual_tool_call (ToolCall): The actual tool call object.
            expected_tool_call (ToolCallAssertion): The expected tool call assertion.

        Returns:
            bool: True if the tool parameters match the expected values, False otherwise.
        """
        for expected_name, expected_spec in expected_tool_call["params"].items():
            expected_type = expected_spec["type"]
            expected_values = expected_spec["values"]

            actual_value = self._get_actual_value(actual_tool_call["data"].args, expected_name)
            if actual_value is None:
                return False

            if expected_type == AssertionType.EXACT.value:
                if not self.assert_value_exact(actual_value, expected_values):
                    return False
            elif expected_type == AssertionType.KEYWORDS.value:
                if not self.assert_value_keywords(actual_value, expected_values):
                    return False
            else:
                return False

        return True

    def _get_actual_value(self, actual_params: dict[str, Any], expected_name: str) -> Any | None:
        """Get an actual value from a dictionary using the expected name.

        Args:
            actual_params (dict[str, Any]): The actual parameters.
            expected_name (str): The expected name.

        Returns:
            Any | None: The actual value, or None if the expected name is not found.
        """
        keys = expected_name.split(".")
        current = actual_params

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def _print_tool_results(
        self,
        actual_tool_calls: list[ToolCall],
        expected_tool_calls: list[ToolCallAssertion],
        tool_results: ToolCallResults,
    ) -> None:
        """Print tool validation results.

        Args:
            actual_tool_calls (list[ToolCall]): List of actual tool calls.
            expected_tool_calls (list[ToolCallAssertion]): List of expected tool call assertions.
            tool_results (ToolCallResults): Tool call results.
        """
        passing_tool_calls, failed_tool_calls, missing_tool_calls, extra_tool_calls = tool_results

        # Print summary
        total_issues = len(failed_tool_calls) + len(missing_tool_calls)
        total_expected_tool_calls = len(expected_tool_calls)
        if total_issues > 0:
            logging.error("FAIL - %d/%d expected tool calls have issues", total_issues, total_expected_tool_calls)
        else:
            logging.info(
                "PASS - All %d/%d expected tool calls succeeded",
                total_expected_tool_calls,
                total_expected_tool_calls,
            )

        # Show passing tools
        if passing_tool_calls:
            logging.info("Expected tool calls that PASSED (%d):", len(passing_tool_calls))
            for tool_call in passing_tool_calls:
                logging.info("   ✓ %s", tool_call["name"])

        # Show failed tools
        if failed_tool_calls:
            logging.error("Expected tool calls that FAILED (%d):", len(failed_tool_calls))
            for tool_call in failed_tool_calls:
                logging.error("   ✗ %s", tool_call["name"])

        # Show missing tools
        if missing_tool_calls:
            logging.warning("Expected tool calls NOT USED (%d):", len(missing_tool_calls))
            for tool_call in missing_tool_calls:
                logging.warning("   ✗ %s (not captured)", tool_call["name"])

        # Show extra tools
        if extra_tool_calls:
            logging.warning("Extra tool calls used (not in expected list) (%d):", len(extra_tool_calls))
            for tool_call in extra_tool_calls:
                logging.warning("   • %s [status: %s]", tool_call["data"].name, tool_call["status"])

        # Warn if no tools captured
        if not actual_tool_calls:
            logging.warning("WARNING: No tool calls were captured at all!")

    def _assert_tool_calls(
        self,
        tool_results: ToolCallResults,
        error_occurred: bool = False,
        error_message: str = "",
    ) -> None:
        """Assert that all expected tools were used and succeeded.

        Args:
            tool_results (ToolCallResults): Tool call results.
            error_occurred (bool): Whether an error occurred during execution.
            error_message (str): Error message if any.

        Raises:
            AssertionError: If any expected tools are missing or failed.
        """
        _, failed_tool_calls, missing_tool_calls, _ = tool_results

        # Build error message
        error_detail = f" (Error: {error_message})" if error_occurred else ""

        # Separate missing from failed
        all_issues = []
        if missing_tool_calls:
            all_issues.append(f"Missing (not used): {missing_tool_calls}")
        if failed_tool_calls:
            all_issues.append(f"Failed (used but errored): {failed_tool_calls}")

        assert not all_issues, f"{'; '.join(all_issues)}{error_detail}"

    def _assert_response(self, response_text: str, expected_response: Assertion) -> None:
        """Assert that the response matches the expected response.

        Args:
            response_text (str): The response text from the agent.
            expected_response (Assertion): The expected response.

        Raises:
            AssertionError: If the response does not match the expected response.
            ValueError: If the response type is invalid.
        """
        if expected_response["type"] == AssertionType.EXACT.value:
            assert self.assert_value_exact(response_text, expected_response["values"]), (
                f"Response text does not match expected value: {expected_response['values']}"
            )
        elif expected_response["type"] == AssertionType.KEYWORDS.value:
            assert self.assert_value_keywords(response_text, expected_response["values"]), (
                f"Response text does not contain all expected keywords: {expected_response['values']}"
            )
        else:
            raise ValueError(f"Invalid response type: {expected_response['type']}")

    def assert_value_exact(self, actual_value: Any, expected_values: list[Any]) -> bool:
        """Assert that a value has an exact value match.

        Args:
            actual_value (Any): The actual value.
            expected_values (list[Any]): The expected values.

        Returns:
            bool: True if the values match exactly, False otherwise.
        """
        return actual_value in expected_values

    def assert_value_keywords(self, actual_value: str, expected_keywords: list[str]) -> bool:
        """Assert that a value contains all expected keywords.

        Args:
            actual_value (str): The actual value (typically a string/message).
            expected_keywords (list[str]): List of keywords that must be present.

        Returns:
            bool: True if the value contains all expected keywords, False otherwise.
        """
        return all(keyword.lower() in str(actual_value).lower() for keyword in expected_keywords if keyword)
