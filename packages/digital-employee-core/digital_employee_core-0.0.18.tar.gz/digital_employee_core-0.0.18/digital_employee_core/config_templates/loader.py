"""Configuration template loader and processor.

This module provides utilities for loading and processing configuration templates
from YAML files, replacing placeholders with values from DigitalEmployeeConfiguration objects.
Uses OmegaConf for powerful configuration management with variable interpolation and merging.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    [1] OmegaConf Documentation: https://omegaconf.readthedocs.io/
"""

from pathlib import Path
from typing import Any

from glaip_sdk import MCP, Tool
from omegaconf import DictConfig, OmegaConf
from omegaconf.errors import OmegaConfBaseException

from digital_employee_core.configuration.configuration import DigitalEmployeeConfiguration

# Configuration template filenames
MCP_CONFIGS_TEMPLATE = "mcp_configs.yaml"
TOOL_CONFIGS_TEMPLATE = "tool_configs.yaml"
DEFAULTS_TEMPLATE = "defaults.yaml"


class ConfigurationValidationError(Exception):
    """Raised when configuration validation fails due to missing required values."""

    pass


class ConfigTemplateLoader:
    """Loads and processes configuration templates from YAML files.

    This class handles loading YAML configuration templates and replacing
    placeholders with actual values from DigitalEmployeeConfiguration objects.

    Attributes:
        template_dir (Path): Path to the directory containing template files.
    """

    def __init__(self, template_dir: str | Path | None = None):
        """Initialize the ConfigTemplateLoader.

        Args:
            template_dir (str | Path | None, optional): Path to template directory. Defaults to config_templates
                in the package directory.
        """
        if template_dir is None:
            # Default to config_templates directory in the package
            package_dir = Path(__file__).parent.parent
            template_dir = package_dir / "config_templates"

        self.template_dir = Path(template_dir)

    def load_template(self, filename: str) -> dict[str, Any]:
        """Load a YAML template file using OmegaConf.

        Args:
            filename (str): Name of the template file (e.g., 'mcp_configs.yaml').

        Returns:
            dict[str, Any]: Dictionary containing the template configuration.

        Raises:
            FileNotFoundError: If the template file does not exist.
        """
        template_path = self.template_dir / filename
        return self.load_template_from_path(template_path)

    def load_template_from_path(self, filepath: str | Path) -> dict[str, Any]:
        """Load a YAML template file from an absolute path using OmegaConf.

        Args:
            filepath (str | Path): Absolute path to the template file.

        Returns:
            dict[str, Any]: Dictionary containing the template configuration.

        Raises:
            FileNotFoundError: If the template file does not exist.
        """
        template_path = Path(filepath)
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        config = OmegaConf.load(template_path)
        # Convert to dict for backward compatibility, but don't resolve yet
        return OmegaConf.to_container(config, resolve=False)

    @staticmethod
    def merge_configs(
        base_config: dict[str, dict[str, Any]] | DictConfig,
        additional_config: dict[str, dict[str, Any]] | DictConfig,
    ) -> dict[str, dict[str, Any]]:
        """Merge two configuration dictionaries using OmegaConf.

        The additional_config will override values in base_config for matching keys.
        New keys in additional_config will be added to the result.
        Performs recursive deep merge for nested dictionaries.

        Args:
            base_config (dict[str, dict[str, Any]] | DictConfig): Base configuration dictionary.
            additional_config (dict[str, dict[str, Any]] | DictConfig): Additional configuration to merge.

        Returns:
            dict[str, dict[str, Any]]: Merged configuration dictionary.
        """
        base_omega = OmegaConf.create(base_config) if not isinstance(base_config, DictConfig) else base_config
        additional_omega = (
            OmegaConf.create(additional_config) if not isinstance(additional_config, DictConfig) else additional_config
        )
        merged = OmegaConf.merge(base_omega, additional_omega)
        return OmegaConf.to_container(merged, resolve=False)

    @staticmethod
    def _process_comma_separated_values(value: Any) -> Any:
        """Convert comma-separated strings to lists.

        This is applied to configuration values from DigitalEmployeeConfiguration objects
        to support comma-separated list inputs (e.g., "tool1,tool2,tool3").

        Args:
            value (Any): Value to process.

        Returns:
            Any: List if value is a comma-separated string, otherwise the original value.
        """
        match value:
            case str() if "," in value and not value.startswith(("[", "{")):
                return [item.strip() for item in value.split(",") if item.strip()]
            case dict():
                return {k: ConfigTemplateLoader._process_comma_separated_values(v) for k, v in value.items()}
            case list():
                return [ConfigTemplateLoader._process_comma_separated_values(item) for item in value]
            case _:
                return value

    def _build_config_dict(self, configurations: list[DigitalEmployeeConfiguration]) -> dict[str, Any]:
        """Build configuration dictionary from DigitalEmployeeConfiguration objects.

        Processes comma-separated values to convert them to lists automatically.

        Args:
            configurations (list[DigitalEmployeeConfiguration]): List of configuration objects.

        Returns:
            dict[str, Any]: Dictionary mapping configuration keys to their processed values.
        """
        return {config.key: self._process_comma_separated_values(config.value) for config in configurations}

    def _merge_configurations(
        self,
        template: dict[str, Any] | DictConfig,
        configurations: list[DigitalEmployeeConfiguration],
    ) -> dict[str, Any]:
        """Merge template, defaults, and user configurations using OmegaConf.

        Merge order:
        1. defaults.yaml (base defaults)
        2. User configurations from DigitalEmployeeConfiguration objects
        3. Template file with ${KEY} placeholders

        This ensures defaults are used when keys are not provided, user configs override defaults,
        and OmegaConf resolves all interpolations.

        Args:
            template (dict[str, Any] | DictConfig): Template configuration with placeholders.
            configurations (list[DigitalEmployeeConfiguration]): List of user configuration objects.

        Returns:
            dict[str, Any]: Resolved configuration dictionary with all placeholders replaced,
                containing only keys that exist in the template.

        Raises:
            ConfigurationValidationError: If required placeholders cannot be resolved.
        """
        # Load defaults
        defaults_path = self.template_dir / DEFAULTS_TEMPLATE
        defaults = OmegaConf.load(defaults_path) if defaults_path.exists() else OmegaConf.create({})

        # Build user configuration from DigitalEmployeeConfiguration objects
        user_config = OmegaConf.create(self._build_config_dict(configurations))

        # Convert template to OmegaConf if needed
        template_config = OmegaConf.create(template) if not isinstance(template, DictConfig) else template

        # Store template keys before merging
        template_keys = set(template.keys()) if isinstance(template, dict) else set(template_config.keys())

        # Merge: defaults <- user_config <- template
        # This allows user_config to override defaults, and template structure to use both
        merged = OmegaConf.merge(defaults, user_config, template_config)

        # Resolve all interpolations and convert to plain dict
        try:
            resolved = OmegaConf.to_container(merged, resolve=True)
            # Filter to only return keys that exist in the template
            # This excludes the user config and defaults keys that were used for interpolation
            filtered_result = {k: v for k, v in resolved.items() if k in template_keys}
            return filtered_result
        except OmegaConfBaseException as e:
            # Extract missing keys from error message
            error_msg = (
                f"Missing required configuration values. "
                f"Some configuration placeholders could not be resolved: {str(e)}. "
                f"Please provide DigitalEmployeeConfiguration objects for the missing keys."
            )
            raise ConfigurationValidationError(error_msg) from e

    def load_mcp_configs(
        self,
        configurations: list[DigitalEmployeeConfiguration],
        filter_mcps: list[MCP] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Load MCP configuration template and resolve placeholders with OmegaConf.

        Merges defaults.yaml, user configurations, and mcp_configs.yaml template,
        then resolves all ${KEY} placeholders using OmegaConf interpolation.
        If the template file doesn't exist, returns an empty dictionary.

        Args:
            configurations (list[DigitalEmployeeConfiguration]): List of DigitalEmployeeConfiguration objects.
            filter_mcps (list[MCP] | None, optional): List of MCP objects to filter. If provided,
                only configs for these MCPs will be included. Defaults to None (includes all configs).

        Returns:
            dict[str, dict[str, Any]]: Dictionary mapping MCP names to their configurations.
                Returns empty dict if template file doesn't exist.

        Raises:
            ConfigurationValidationError: If required placeholders cannot be resolved.
        """
        template_path = self.template_dir / MCP_CONFIGS_TEMPLATE
        if not template_path.exists():
            return {}

        template = self.load_template(MCP_CONFIGS_TEMPLATE)

        # Filter template before merging for better performance
        if filter_mcps is not None:
            filter_names = {mcp.name for mcp in filter_mcps}
            template = {name: config for name, config in template.items() if name in filter_names}

        result = self._merge_configurations(template, configurations)
        return result

    def load_tool_configs(
        self,
        configurations: list[DigitalEmployeeConfiguration],
        filter_tools: list[Tool] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Load tool configuration template and resolve placeholders with OmegaConf.

        Merges defaults.yaml, user configurations, and tool_configs.yaml template,
        then resolves all ${KEY} placeholders using OmegaConf interpolation.
        If the template file doesn't exist, returns an empty dictionary.

        Args:
            configurations (list[DigitalEmployeeConfiguration]): List of DigitalEmployeeConfiguration objects.
            filter_tools (list[Tool] | None, optional): List of Tool objects to filter. If provided,
                only configs for these tools will be included. Defaults to None (includes all configs).

        Returns:
            dict[str, dict[str, Any]]: Dictionary mapping tool names to their configurations.
                Returns empty dict if template file doesn't exist.

        Raises:
            ConfigurationValidationError: If required placeholders cannot be resolved.
        """
        template_path = self.template_dir / TOOL_CONFIGS_TEMPLATE
        if not template_path.exists():
            return {}

        template = self.load_template(TOOL_CONFIGS_TEMPLATE)

        # Filter template before merging for better performance
        if filter_tools is not None:
            filter_names = {tool.name for tool in filter_tools}
            template = {name: config for name, config in template.items() if name in filter_names}

        result = self._merge_configurations(template, configurations)
        return result

    def resolve_placeholders(
        self,
        text: str,
        configurations: list[DigitalEmployeeConfiguration] | None = None,
        additional_loaders: list["ConfigTemplateLoader"] | None = None,
    ) -> str:
        """Resolve placeholders in a given text using OmegaConf interpolation.

        This method merges defaults from multiple config loaders (in order),
        then merges with user configurations, and resolves placeholders.

        Args:
            text (str): String containing placeholders in ${...} format.
            configurations (list[DigitalEmployeeConfiguration] | None, optional): List of configuration objects.
                Defaults to None.
            additional_loaders (list[ConfigTemplateLoader] | None, optional): Additional config loaders to merge
                defaults from (in order: self -> additional_loaders[0] -> additional_loaders[1] -> ...).
                Defaults to None.

        Returns:
            str: Resolved string with all placeholders replaced.

        Raises:
            ConfigurationValidationError: If placeholders cannot be resolved.
        """
        try:
            # Start with current loader's defaults
            defaults_path = self.template_dir / DEFAULTS_TEMPLATE
            merged_defaults = OmegaConf.load(defaults_path) if defaults_path.exists() else OmegaConf.create({})

            # Merge additional loaders' defaults (in order)
            if additional_loaders:
                for loader in additional_loaders:
                    loader_defaults_path = loader.template_dir / DEFAULTS_TEMPLATE
                    if loader_defaults_path.exists():
                        loader_defaults = OmegaConf.load(loader_defaults_path)
                        merged_defaults = OmegaConf.merge(merged_defaults, loader_defaults)

            # Build user configuration
            user_config = OmegaConf.create({})
            if configurations:
                user_config = OmegaConf.create(self._build_config_dict(configurations))

            # Merge defaults with user config (user config takes precedence)
            merged = OmegaConf.merge(merged_defaults, user_config)

            # Add the text as a temporary value for interpolation (faster than merge)
            OmegaConf.update(merged, "_temp_text", text, merge=False)

            # Resolve and return
            resolved = OmegaConf.to_container(merged, resolve=True)
            return resolved["_temp_text"]

        except OmegaConfBaseException as e:
            error_msg = (
                f"Failed to resolve placeholders in text. "
                f"Some placeholders could not be resolved: {str(e)}. "
                f"Please provide DigitalEmployeeConfiguration objects for the missing keys."
            )
            raise ConfigurationValidationError(error_msg) from e
