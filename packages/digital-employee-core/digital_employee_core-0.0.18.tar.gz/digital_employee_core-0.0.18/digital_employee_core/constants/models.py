"""Model name constants for AI models.

This module defines constant values for various AI model names
used throughout the digital employee core package.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)

References:
    NONE
"""

# Model names constants
GPT_4_1_MODEL_NAME = "gpt-4.1"
GPT_5_MODEL_NAME = "gpt-5"
GPT_5_MINIMAL_MODEL_NAME = "gpt-5-minimal"
GPT_5_MINI_MODEL_NAME = "gpt-5-mini"
GPT_5_LOW_MODEL_NAME = "gpt-5-low"
GPT_5_1_MODEL_NAME = "gpt-5.1"
GPT_5_1_LOW_MODEL_NAME = "gpt-5.1-low"
GPT_5_1_MEDIUM_MODEL_NAME = "gpt-5.1-medium"
GPT_5_1_HIGH_MODEL_NAME = "gpt-5.1-high"
GPT_5_2_MODEL_NAME = "gpt-5.2"
GPT_5_2_LOW_MODEL_NAME = "gpt-5.2-low"
GPT_5_2_MEDIUM_MODEL_NAME = "gpt-5.2-medium"
GPT_5_2_HIGH_MODEL_NAME = "gpt-5.2-high"
GPT_5_2_XHIGH_MODEL_NAME = "gpt-5.2-xhigh"

# Default model for digital employees
DEFAULT_MODEL_NAME = GPT_5_MINI_MODEL_NAME

# Provider constants
OPENAI_PROVIDER = "openai"

# Model provider mappings
MODEL_PROVIDERS = {
    GPT_4_1_MODEL_NAME: OPENAI_PROVIDER,
    GPT_5_MODEL_NAME: OPENAI_PROVIDER,
    GPT_5_MINIMAL_MODEL_NAME: OPENAI_PROVIDER,
    GPT_5_MINI_MODEL_NAME: OPENAI_PROVIDER,
    GPT_5_LOW_MODEL_NAME: OPENAI_PROVIDER,
    GPT_5_1_MODEL_NAME: OPENAI_PROVIDER,
    GPT_5_1_LOW_MODEL_NAME: OPENAI_PROVIDER,
    GPT_5_1_MEDIUM_MODEL_NAME: OPENAI_PROVIDER,
    GPT_5_1_HIGH_MODEL_NAME: OPENAI_PROVIDER,
    GPT_5_2_MODEL_NAME: OPENAI_PROVIDER,
    GPT_5_2_LOW_MODEL_NAME: OPENAI_PROVIDER,
    GPT_5_2_MEDIUM_MODEL_NAME: OPENAI_PROVIDER,
    GPT_5_2_HIGH_MODEL_NAME: OPENAI_PROVIDER,
    GPT_5_2_XHIGH_MODEL_NAME: OPENAI_PROVIDER,
}


def get_model_provider(model_name: str) -> str:
    """Get the provider for a given model name.

    Args:
        model_name (str): The name of the model.

    Returns:
        str: The provider name.

    Raises:
        ValueError: If the model name is not found in MODEL_PROVIDERS.
    """
    if model_name not in MODEL_PROVIDERS:
        raise ValueError(f"Unknown model name: {model_name}")
    return MODEL_PROVIDERS[model_name]


def get_model_full_name(model_name: str) -> str:
    """Get the full model name with provider prefix.

    If the model name already contains a provider prefix (indicated by '/'),
    it is returned as-is. Otherwise, the provider is looked up and prepended.

    Args:
        model_name (str): The name of the model.

    Returns:
        str: The full model name in format "provider/model_name".

    Raises:
        ValueError: If the model name does not contain a provider prefix
            and is not found in MODEL_PROVIDERS.
    """
    return model_name if "/" in model_name else f"{get_model_provider(model_name)}/{model_name}"
