"""Model name constants for AI models.

This module defines constant values for various AI model names
used throughout the digital employee core package.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)
    Vio Albert Ferdinand (vio.a.ferdinand@gdplabs.id)

References:
    NONE
"""

# Model names constants
GPT_4_1_MODEL_NAME = "openai/gpt-4.1"
GPT_5_MODEL_NAME = "openai/gpt-5"
GPT_5_MINIMAL_MODEL_NAME = "openai/gpt-5-minimal"
GPT_5_MINI_MODEL_NAME = "openai/gpt-5-mini"
GPT_5_LOW_MODEL_NAME = "openai/gpt-5-low"
GPT_5_1_MODEL_NAME = "openai/gpt-5.1"
GPT_5_1_LOW_MODEL_NAME = "openai/gpt-5.1-low"
GPT_5_1_MEDIUM_MODEL_NAME = "openai/gpt-5.1-medium"
GPT_5_1_HIGH_MODEL_NAME = "openai/gpt-5.1-high"
GPT_5_2_MODEL_NAME = "openai/gpt-5.2"
GPT_5_2_LOW_MODEL_NAME = "openai/gpt-5.2-low"
GPT_5_2_MEDIUM_MODEL_NAME = "openai/gpt-5.2-medium"
GPT_5_2_HIGH_MODEL_NAME = "openai/gpt-5.2-high"
GPT_5_2_XHIGH_MODEL_NAME = "openai/gpt-5.2-xhigh"

# Default model for digital employees
DEFAULT_MODEL_NAME = GPT_5_MINI_MODEL_NAME


def ensure_valid_model_name(model_name: str) -> str:
    """Ensure the model name is valid.

    Args:
        model_name (str): The model name to validate.

    Returns:
        str: The validated model name.

    Raises:
        ValueError: If the model name is invalid.
    """
    try:
        provider, name = model_name.split("/")
    except ValueError:
        raise ValueError(f"Model name must in the format 'provider/model_name', got: {model_name}") from None
    if not provider or not name:
        raise ValueError(f"Model name must include both provider and model parts, got: {model_name}")
    return model_name
