"""LLM integration and markdown generation with multi-provider support."""

import logging
import warnings
from typing import Any, Optional

import requests

from .config.settings import settings
from .prompts import build_prompt, build_prompt_with_config, load_prompt_template
from .report_config import ReportConfig
from .serializers import serialize_data

logger = logging.getLogger(__name__)


def call_llm(prompt: str, max_tokens: int | None = None) -> str:
    """
    Send a prompt to LLM provider (Ollama, OpenAI, Azure, etc.).

    Automatically handles provider-specific authentication and URL construction
    based on settings.llm_provider.

    Args:
        prompt: The prompt to send
        max_tokens: Optional override for max tokens (uses settings default if None)

    Returns:
        The assistant's response text.

    Raises:
        RuntimeError: If LLM generation fails
        ValueError: If provider configuration is invalid
    """
    provider = settings.llm_provider
    base_url = settings.llm_base_url
    model = settings.llm_model
    api_key = settings.llm_api_key

    # Build provider-specific URL and headers
    if provider == "openai":
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set REPORT_LLM_API_KEY environment variable."
            )
        url = f"{base_url.rstrip('/')}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    elif provider == "ollama":
        url = f"{base_url.rstrip('/')}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}

    elif provider == "azure":
        if not api_key:
            raise ValueError(
                "Azure API key is required. Set REPORT_LLM_API_KEY environment variable."
            )
        if not base_url or not model:
            raise ValueError(
                "Azure requires llm_base_url and llm_model to be set. "
                "Format: https://<resource>.openai.azure.com"
            )
        # Azure uses deployment name in URL
        url = f"{base_url.rstrip('/')}/openai/deployments/{model}/chat/completions?api-version=2024-02-15-preview"
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
        }

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    # Build request payload (OpenAI-compatible format)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "stream": False,
        "temperature": settings.llm_temperature,
        "max_tokens": max_tokens or settings.llm_max_tokens,
    }

    logger.info(f"Calling {provider} at {url} with model {model}")

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=300)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = e.response.json()
        except Exception:
            error_detail = e.response.text

        logger.error(f"HTTP error from {provider}: {e} - {error_detail}")
        raise RuntimeError(
            f"{provider.title()} API request failed: {e}\nDetails: {error_detail}"
        ) from e
    except Exception as e:
        logger.error(f"Failed to call {provider}: {e}")
        raise RuntimeError(f"{provider.title()} generation failed: {e}") from e


def call_ollama(prompt: str, max_tokens: int | None = None) -> str:
    """
    [DEPRECATED] Legacy function for Ollama calls.

    Use call_llm() instead, which supports multiple providers.
    This function is kept for backward compatibility.

    Args:
        prompt: The prompt to send
        max_tokens: Optional override for max tokens

    Returns:
        The assistant's response text.
    """
    warnings.warn(
        "call_ollama() is deprecated. Use call_llm() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return call_llm(prompt, max_tokens)


def generate_markdown(
    data: Any,
    question: str | None = None,
    config: Optional[ReportConfig] = None,
) -> str:
    """
    Use LLM to generate markdown report from question and data.

    Supports multiple LLM providers (Ollama, OpenAI, Azure) based on settings.

    Args:
        data: Any input data (text, dict, list, etc.)
        question: The user's original question
        config: Optional ReportConfig for behavior customization

    Returns:
        Markdown formatted response string

    Examples:
        # Default generation
        md = generate_markdown(data, "Analyze sales")

        # With behavior customization
        config = ReportConfig(
            audience=Audience.EXECUTIVES,
            style=Style.CONCISE,
            tone=Tone.FORMAL
        )
        md = generate_markdown(data, "Analyze sales", config=config)

        # Using a preset
        config = ReportConfig.from_preset(Preset.EXECUTIVE_SUMMARY)
        md = generate_markdown(data, "Analyze sales", config=config)
    """
    data_str = serialize_data(data)
    question_str = question or "Generate a report for this data"

    # Always use build_prompt_with_config for proper data insertion and anti-hallucination
    # Even when config is None, this ensures data is properly formatted in the prompt
    prompt = build_prompt_with_config(question_str, data_str, config)

    return call_llm(prompt)


def generate_quick_insights(data: Any, question: str | None = None) -> str:
    """
    Generate quick insights from data - fast, lightweight summary.

    This is meant to be called first to give users immediate value
    while the full PDF report generates in the background.

    Supports multiple LLM providers (Ollama, OpenAI, Azure) based on settings.

    Args:
        data: Input data (text, dict, list, etc.)
        question: The user's original question

    Returns:
        String with 3-5 bullet point insights
    """
    data_str = serialize_data(data)
    question_str = question or "Summarize this data"

    # Load quick insights template
    template = load_prompt_template("QUICK_INSIGHTS_TEMPLATE")
    prompt = build_prompt(template, question_str, data_str)

    # Use lower max_tokens for faster response
    return call_llm(prompt, max_tokens=512)
