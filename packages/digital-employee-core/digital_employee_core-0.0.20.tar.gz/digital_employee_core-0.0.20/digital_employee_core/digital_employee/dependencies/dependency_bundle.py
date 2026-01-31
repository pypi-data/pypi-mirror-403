"""Dependency bundle for digital employee.

Authors:
    Vio Albert Ferdinand (vio.a.ferdinand@gdplabs.id)

References:
    NONE
"""

from dataclasses import dataclass
from typing import Any

from glaip_sdk import MCP, Tool

from digital_employee_core.config_templates.loader import ConfigTemplateLoader


@dataclass(slots=True)
class DependencyBundle:
    """Bundle of dependencies (tools, MCPs) and their configurations.

    This class manages collections of tools and MCPs along with their
    optional configuration dictionaries. It provides utilities for
    deduplication, merging, and combining multiple bundles.

    Attributes:
        tools (list[Tool]): List of Tool instances.
        mcps (list[MCP]): List of MCP instances.
        tool_configs (dict[str, dict[str, Any]] | None): Optional mapping of tool names to their configurations.
        mcp_configs (dict[str, dict[str, Any]] | None): Optional mapping of MCP names to their configurations.
    """

    tools: list[Tool]
    mcps: list[MCP]
    tool_configs: dict[str, dict[str, Any]] | None
    mcp_configs: dict[str, dict[str, Any]] | None

    @staticmethod
    def dedupe_preserve_order(items: list[Any]) -> list[Any]:
        """Remove duplicates from a list while preserving the original order.

        Args:
            items (list[Any]): The list of items to deduplicate.

        Returns:
            list[Any]: A new list with duplicates removed, preserving the order of first occurrences.
        """
        deduped: list[Any] = []
        seen = set()
        for item in items:
            if item not in seen:
                deduped.append(item)
                seen.add(item)
        return deduped

    @staticmethod
    def merge_config_maps(
        base: dict[str, dict[str, Any]] | None,
        extra: dict[str, dict[str, Any]] | None,
    ) -> dict[str, dict[str, Any]] | None:
        """Merge two configuration maps, handling None values gracefully.

        Args:
            base (dict[str, dict[str, Any]] | None): The base configuration map.
            extra (dict[str, dict[str, Any]] | None): The extra configuration map to merge.

        Returns:
            dict[str, dict[str, Any]] | None: The merged configuration map, or None if both inputs are None.
        """
        if base is None and extra is None:
            return None

        base_dict: dict[str, dict[str, Any]] = base if isinstance(base, dict) else {}
        extra_dict: dict[str, dict[str, Any]] = extra if isinstance(extra, dict) else {}

        return ConfigTemplateLoader.merge_configs(base_dict, extra_dict)

    def merged_with(
        self,
        extra: "DependencyBundle",
        *,
        merge_configs: bool,
    ) -> "DependencyBundle":
        """Create a new dependency bundle by merging this bundle with another.

        Args:
            extra (DependencyBundle): The other dependency bundle to merge with.
            merge_configs (bool): Whether to merge configuration maps.

        Returns:
            DependencyBundle: A new dependency bundle with merged dependencies and configurations.
        """
        merged_tools = DependencyBundle.dedupe_preserve_order(self.tools + extra.tools)
        merged_mcps = DependencyBundle.dedupe_preserve_order(self.mcps + extra.mcps)

        if merge_configs:
            tool_configs = DependencyBundle.merge_config_maps(self.tool_configs, extra.tool_configs)
            mcp_configs = DependencyBundle.merge_config_maps(self.mcp_configs, extra.mcp_configs)
        else:
            tool_configs = self.tool_configs.copy() if self.tool_configs is not None else None
            mcp_configs = self.mcp_configs.copy() if self.mcp_configs is not None else None

        return DependencyBundle(
            tools=merged_tools,
            mcps=merged_mcps,
            tool_configs=tool_configs,
            mcp_configs=mcp_configs,
        )
