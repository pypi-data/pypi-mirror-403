"""Configuration propagation logic for sub-agents.

This module provides utilities for propagating configurations from parent
DigitalEmployee to sub-agents. Configurations flow down the agent hierarchy,
with selective filtering based on each sub-agent's tools and MCPs.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    NONE
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from glaip_sdk import Agent
from gllm_core.utils import LoggerManager

logger = LoggerManager().get_logger(__name__)

# Type alias for sub-agents (can be Agent or other types)
SubAgentType = Agent | Any


class ItemType(StrEnum):
    """Enum for configuration item types."""

    TOOL = "tool"
    MCP = "MCP"


@dataclass
class DependencyCollectionContext:
    """Context for collecting dependencies from agent hierarchies.

    Attributes:
        dependency_type: Type of dependency to collect (TOOL or MCP).
        name_extractor: Function to extract names from dependencies.
        dependencies: List to collect dependencies into.
        seen: Set of already seen dependency names.
        visited_agents: Set of already visited agent names (for cycle detection).
    """

    dependency_type: ItemType
    name_extractor: Callable[[Any], str | None]
    dependencies: list[Any] = field(default_factory=list)
    seen: set[str] = field(default_factory=set)
    visited_agents: set[str] = field(default_factory=set)


class ConfigPropagationManager:
    """Manages configuration propagation for sub-agents.

    This class handles the propagation of tool and MCP configurations from
    parent DigitalEmployee to sub-agents. All configuration keys must be strings.

    The propagation process:
    1. Checks which tools/MCPs need configs (don't already have one)
    2. Propagates from parent configs using strict name matching
    3. Merges existing and propagated configs with precedence
    """

    def process_sub_agents_with_propagation(
        self,
        sub_agents: list[SubAgentType],
        parent_tool_configs: dict[str, dict[str, Any]],
        parent_mcp_configs: dict[str, dict[str, Any]],
    ) -> list[SubAgentType]:
        """Process sub-agents to propagate configurations from parent.

        For each Agent sub-agent:
        - Check if it has configs for all tools/MCPs it uses
        - For tools/MCPs without configs, propagate from parent if available
        - Merge existing configs with propagated configs (existing takes precedence)
        - Recursively process nested sub-agents if they exist

        Args:
            sub_agents (list[SubAgentType]): List of sub-agent instances (can be Agent or other types).
            parent_tool_configs (dict[str, dict[str, Any]]): Parent's tool configurations with string keys.
            parent_mcp_configs (dict[str, dict[str, Any]]): Parent's MCP configurations with string keys.

        Returns:
            list[SubAgentType]: Processed sub-agents with propagated configurations.
                Non-Agent sub-agents are included unchanged in the result.
        """
        if not sub_agents:
            return []

        processed_agents = []

        for sub_agent in sub_agents:
            # Skip non-Agent sub-agents
            if self._is_non_agent_sub_agent(sub_agent):
                processed_agents.append(sub_agent)
                continue

            # Process the agent with config propagation
            processed_agent = self._process_single_agent(sub_agent, parent_tool_configs, parent_mcp_configs)
            processed_agents.append(processed_agent)

        return processed_agents

    def collect_all_sub_agent_dependencies(
        self, sub_agents: list[SubAgentType], dependency_type: ItemType
    ) -> list[Any]:
        """Collect all dependencies (tools or MCPs) from all sub-agents recursively.

        Args:
            sub_agents (list[SubAgentType]): List of sub-agent instances.
            dependency_type (ItemType): Type of dependency to collect - TOOL or MCP.

        Returns:
            list[Any]: List of unique dependencies from all sub-agents.
        """
        # Get the appropriate name extractor
        name_extractor = self._get_name_extractor(dependency_type)
        if not name_extractor:
            return []

        # Create collection context
        context = DependencyCollectionContext(
            dependency_type=dependency_type,
            name_extractor=name_extractor,
        )

        # Collect dependencies from all sub-agents
        for sub_agent in sub_agents or []:
            self._collect_dependencies_from_agent(sub_agent, context)

        return context.dependencies

    @staticmethod
    def _get_agent_dependencies(agent: Agent, dependency_type: ItemType) -> list[Any]:
        """Get dependencies (tools or MCPs) from an agent based on type.

        Args:
            agent (Agent): The agent to get dependencies from.
            dependency_type (ItemType): Type of dependency - TOOL or MCP.

        Returns:
            list[Any]: List of dependencies from the agent.
        """
        if dependency_type == ItemType.TOOL:
            return agent.tools or []
        elif dependency_type == ItemType.MCP:
            return agent.mcps or []
        return []

    @staticmethod
    def _add_unique_dependencies(
        dependencies: list[Any],
        seen: set[str],
        agent_deps: list[Any],
        name_extractor: Callable[[Any], str | None],
    ) -> None:
        """Add unique dependencies to the list, avoiding duplicates.

        Args:
            dependencies (list[Any]): List to add dependencies to.
            seen (set[str]): Set of already seen dependency names.
            agent_deps (list[Any]): Dependencies to add.
            name_extractor (Callable): Function to extract name from dependency.
        """
        for dep in agent_deps:
            dep_name = name_extractor(dep)
            if dep_name and dep_name not in seen:
                seen.add(dep_name)
                dependencies.append(dep)

    @staticmethod
    def _get_config_names(configs: dict | None) -> set[str]:
        """Extract string names from configuration keys.

        Args:
            configs (dict | None): Configuration dictionary with string keys.

        Returns:
            set[str]: Set of configuration names (keys).
        """
        if not configs:
            return set()
        return set(configs.keys())

    @staticmethod
    def _extract_tool_name(tool: Any) -> str | None:
        """Extract tool name from tool object.

        Args:
            tool (Any): Tool object with 'name' or '__name__' attribute.

        Returns:
            str | None: Tool name if found, None otherwise.
        """
        return getattr(tool, "name", None) or getattr(tool, "__name__", None)

    @staticmethod
    def _extract_mcp_name(mcp: Any) -> str | None:
        """Extract MCP name from MCP object.

        Args:
            mcp (Any): MCP object with 'name' attribute.

        Returns:
            str | None: MCP name if found, None otherwise.
        """
        return getattr(mcp, "name", None)

    @staticmethod
    def _propagate_configs(
        items: list[Any],
        parent_configs: dict[str, dict[str, Any]],
        existing_config_names: set[str],
        name_extractor: Callable[[Any], str | None],
        item_type: ItemType,
    ) -> dict[str, dict[str, Any]]:
        """Generic config propagation logic.

        Args:
            items (list[Any]): List of tools or MCPs.
            parent_configs (dict[str, dict[str, Any]]): Parent configurations.
            existing_config_names (set[str]): Names of existing configs in sub-agent.
            name_extractor (callable): Function to extract name from item.
            item_type (ItemType): Type of item (TOOL or MCP) for logging.

        Returns:
            dict[str, dict[str, Any]]: Propagated configurations.
        """
        propagated = {}

        for item in items:
            if not (item_name := name_extractor(item)):
                logger.warning(
                    f"Cannot propagate config for {item_type.value} {item}: "
                    f"no identifiable name found. "
                    f"Ensure {item_type.value}s have proper naming."
                )
                continue

            if item_name not in existing_config_names and item_name in parent_configs:
                propagated[item_name] = parent_configs[item_name]

        return propagated

    @staticmethod
    def _merge_configs(
        existing_configs: dict | None, propagated_configs: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Merge existing configs with propagated configs.

        Existing configs take precedence over propagated configs.
        All config keys must be strings.

        Args:
            existing_configs (dict | None): The sub-agent's existing configs with string keys.
            propagated_configs (dict[str, dict[str, Any]]): The configs propagated from parent with string keys.

        Returns:
            dict[str, dict[str, Any]]: Merged configurations with string keys, or empty dict if neither exists.
        """
        if not existing_configs:
            return propagated_configs or {}

        if not propagated_configs:
            return existing_configs

        # Merge: propagated configs form base, existing configs take precedence
        return {**propagated_configs, **existing_configs}

    @staticmethod
    def _is_non_agent_sub_agent(sub_agent: SubAgentType) -> bool:
        """Check if sub-agent should be skipped (not an Agent instance).

        Args:
            sub_agent (SubAgentType): Sub-agent to check.

        Returns:
            bool: True if sub-agent should be skipped, False otherwise.
        """
        if not isinstance(sub_agent, Agent):
            logger.warning(
                f"Skipping unsupported sub-agent type: {type(sub_agent)}. Sub-agents must be Agent instances."
            )
            return True
        return False

    @staticmethod
    def _update_agent_with_nested_agents(agent: Agent, nested_agents: list[SubAgentType]) -> Agent:
        """Update an agent with processed nested agents.

        Args:
            agent (Agent): The agent to update.
            nested_agents (list): Processed nested agents.

        Returns:
            Agent: New agent instance with updated nested agents.
        """
        if nested_agents == agent.agents:
            return agent

        agent_dict = agent.model_dump(exclude_none=False)
        agent_dict["agents"] = nested_agents
        return Agent(**agent_dict)

    def _get_name_extractor(self, dependency_type: ItemType) -> Callable[[Any], str | None] | None:
        """Get the appropriate name extractor for the dependency type.

        Args:
            dependency_type (ItemType): Type of dependency - TOOL or MCP.

        Returns:
            Callable | None: Name extractor function, or None if type is invalid.
        """
        if dependency_type == ItemType.TOOL:
            return self._extract_tool_name
        elif dependency_type == ItemType.MCP:
            return self._extract_mcp_name
        return None

    def _propagate_tool_configs(
        self, sub_agent: Agent, parent_tool_configs: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Propagate tool configurations from parent for tools used by sub-agent.

        Only propagates configs for tools that don't already have a config in sub_agent.tool_configs.
        Uses strict name-based matching. All config keys must be strings.

        Args:
            sub_agent (Agent): The Agent sub-agent.
            parent_tool_configs (dict[str, dict[str, Any]]): Parent's tool configurations with string keys.

        Returns:
            dict[str, dict[str, Any]]: Filtered tool configs for sub-agent, or empty dict if no matches.
        """
        if not parent_tool_configs or not sub_agent.tools:
            return {}

        # Get existing config names from sub-agent
        existing_config_names = self._get_config_names(sub_agent.tool_configs)

        propagated = self._propagate_configs(
            items=sub_agent.tools,
            parent_configs=parent_tool_configs,
            existing_config_names=existing_config_names,
            name_extractor=self._extract_tool_name,
            item_type=ItemType.TOOL,
        )

        return propagated

    def _propagate_mcp_configs(
        self, sub_agent: Agent, parent_mcp_configs: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Propagate MCP configurations from parent for MCPs used by sub-agent.

        Only propagates configs for MCPs that don't already have a config in sub_agent.mcp_configs.
        Uses strict name-based matching. All config keys must be strings.

        Args:
            sub_agent (Agent): The Agent sub-agent.
            parent_mcp_configs (dict[str, dict[str, Any]]): Parent's MCP configurations with string keys.

        Returns:
            dict[str, dict[str, Any]]: Filtered MCP configs for sub-agent, or empty dict if no matches.
        """
        if not parent_mcp_configs or not sub_agent.mcps:
            return {}

        # Get existing config names from sub-agent
        existing_config_names = self._get_config_names(sub_agent.mcp_configs)

        propagated = self._propagate_configs(
            items=sub_agent.mcps,
            parent_configs=parent_mcp_configs,
            existing_config_names=existing_config_names,
            name_extractor=self._extract_mcp_name,
            item_type=ItemType.MCP,
        )

        return propagated

    def _apply_propagated_configs_to_agent(
        self,
        agent: Agent,
        propagated_tool_configs: dict[str, dict[str, Any]],
        propagated_mcp_configs: dict[str, dict[str, Any]],
    ) -> Agent:
        """Apply propagated configs to an agent by creating a new instance.

        Args:
            agent (Agent): The agent to apply configs to.
            propagated_tool_configs (dict[str, dict[str, Any]]): Propagated tool configs.
            propagated_mcp_configs (dict[str, dict[str, Any]]): Propagated MCP configs.

        Returns:
            Agent: New agent instance with merged configs.
        """
        merged_tool_configs = self._merge_configs(agent.tool_configs, propagated_tool_configs)
        merged_mcp_configs = self._merge_configs(agent.mcp_configs, propagated_mcp_configs)

        agent_dict = agent.model_dump(exclude_none=False)
        agent_dict["tool_configs"] = merged_tool_configs
        agent_dict["mcp_configs"] = merged_mcp_configs

        return Agent(**agent_dict)

    def _prepare_configs_for_nested_agents(
        self,
        agent: Agent,
        parent_tool_configs: dict[str, dict[str, Any]],
        parent_mcp_configs: dict[str, dict[str, Any]],
    ) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
        """Prepare merged configs for nested agents.

        Nested agents should have access to both:
        1. Their direct parent's (agent's) merged configs
        2. The grandparent's original configs

        Args:
            agent (Agent): The parent agent.
            parent_tool_configs (dict[str, dict[str, Any]]): Grandparent's tool configs.
            parent_mcp_configs (dict[str, dict[str, Any]]): Grandparent's MCP configs.

        Returns:
            tuple: (merged_tool_configs, merged_mcp_configs) for nested agents.
        """
        merged_tool_configs = self._merge_configs(agent.tool_configs, parent_tool_configs)
        merged_mcp_configs = self._merge_configs(agent.mcp_configs, parent_mcp_configs)
        return merged_tool_configs, merged_mcp_configs

    def _process_single_agent(
        self,
        agent: Agent,
        parent_tool_configs: dict[str, dict[str, Any]],
        parent_mcp_configs: dict[str, dict[str, Any]],
    ) -> Agent:
        """Process a single agent with config propagation and nested agent handling.

        Args:
            agent (Agent): The agent to process.
            parent_tool_configs (dict[str, dict[str, Any]]): Parent's tool configurations.
            parent_mcp_configs (dict[str, dict[str, Any]]): Parent's MCP configurations.

        Returns:
            Agent: Processed agent with propagated configs and processed nested agents.
        """
        # Propagate configs from parent
        propagated_tool_configs = self._propagate_tool_configs(agent, parent_tool_configs)
        propagated_mcp_configs = self._propagate_mcp_configs(agent, parent_mcp_configs)

        # Apply propagated configs if any
        has_propagation = propagated_tool_configs or propagated_mcp_configs
        if has_propagation:
            agent = self._apply_propagated_configs_to_agent(agent, propagated_tool_configs, propagated_mcp_configs)

        # Process nested agents if they exist
        if hasattr(agent, "agents") and agent.agents:
            nested_tool_configs, nested_mcp_configs = self._prepare_configs_for_nested_agents(
                agent, parent_tool_configs, parent_mcp_configs
            )

            processed_nested_agents = self.process_sub_agents_with_propagation(
                sub_agents=agent.agents,
                parent_tool_configs=nested_tool_configs,
                parent_mcp_configs=nested_mcp_configs,
            )

            agent = self._update_agent_with_nested_agents(agent, processed_nested_agents)

        return agent

    def _collect_dependencies_from_agent(self, agent: Agent, context: DependencyCollectionContext) -> None:
        """Recursively collect dependencies from an agent and its nested agents.

        Args:
            agent (Agent): The agent to collect from.
            context (DependencyCollectionContext): Collection context with state tracking.
        """
        if not isinstance(agent, Agent):
            return

        # Check for cycles - if we've seen this agent before, skip it
        if agent.name in context.visited_agents:
            return
        context.visited_agents.add(agent.name)

        # Get dependencies from this agent
        agent_deps = self._get_agent_dependencies(agent, context.dependency_type)
        self._add_unique_dependencies(context.dependencies, context.seen, agent_deps, context.name_extractor)

        # Recursively process nested agents
        for nested_agent in agent.agents or []:
            self._collect_dependencies_from_agent(nested_agent, context)
