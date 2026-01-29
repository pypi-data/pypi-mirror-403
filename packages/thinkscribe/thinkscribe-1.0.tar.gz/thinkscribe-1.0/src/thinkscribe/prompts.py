"""Prompt template management with behavior customization."""

from pathlib import Path
from typing import Optional

import yaml

from .report_config import ReportConfig

# Path to prompt templates
_TEMPLATE_PATH = Path(__file__).parent / "prompts" / "prompt_templates.yaml"


def _load_yaml_data(template_path: Path | None = None) -> dict:
    """Load YAML template data."""
    path = template_path or _TEMPLATE_PATH
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_prompt_template(template_name: str = "REPORT_GENERATOR_TEMPLATE") -> str:
    """
    Load a prompt template from YAML by name.

    This is the legacy function for backward compatibility.
    For new code, use build_prompt_with_config() instead.
    """
    data = _load_yaml_data()
    # Return the old-style PROMPT if it exists, otherwise build from BASE_INSTRUCTION
    if "PROMPT" in data[template_name]:
        return data[template_name]["PROMPT"]
    return data[template_name]["BASE_INSTRUCTION"]


def build_prompt_with_config(
    question: str,
    answer: str,
    config: Optional[ReportConfig] = None,
    template_name: str = "REPORT_GENERATOR_TEMPLATE",
) -> str:
    """
    Build a complete prompt with behavior customizations.

    Args:
        question: The user's question
        answer: The data/answer to analyze
        config: Optional ReportConfig for behavior customization
        template_name: Name of the base template to use

    Returns:
        Complete prompt string with all modifiers applied
    """
    # Handle custom prompt override
    if config and config.custom_prompt:
        return config.custom_prompt.replace("{question}", question).replace(
            "{answer}", answer
        )

    # Load from custom template file if specified
    yaml_data = (
        _load_yaml_data(config.template_file) if config and config.template_file else _load_yaml_data()
    )

    # Use custom template name if specified
    if config and config.template_name:
        template_name = config.template_name

    # Build the prompt parts
    parts = []

    # 1. Base instruction
    template_data = yaml_data.get(template_name, {})
    base_instruction = template_data.get("BASE_INSTRUCTION", "")
    parts.append(base_instruction)

    # 2. Apply behavior modifiers if config is provided
    if config:
        # Audience modifier
        if config.audience:
            audience_data = yaml_data.get("AUDIENCES", {}).get(config.audience.value, {})
            if audience_data:
                parts.append(f"\n{audience_data.get('context', '')}")
                parts.append(audience_data.get("guidelines", ""))

        # Style modifier
        if config.style:
            style_data = yaml_data.get("STYLES", {}).get(config.style.value, {})
            if style_data:
                parts.append(f"\n{style_data.get('characteristics', '')}")

        # Tone modifier
        if config.tone:
            tone_data = yaml_data.get("TONES", {}).get(config.tone.value, {})
            if tone_data:
                parts.append(f"\n{tone_data.get('voice', '')}")

        # Focus areas
        if config.focus:
            focus_data = yaml_data.get("FOCUS_AREAS", {})
            parts.append("\n## Focus Areas")
            for focus_area in config.focus:
                focus_info = focus_data.get(focus_area.value, {})
                if focus_info:
                    parts.append(f"- **{focus_area.value.title()}:** {focus_info.get('emphasis', '')}")

    # 3. Default structure
    default_structure = template_data.get("DEFAULT_STRUCTURE", "")
    parts.append(f"\n{default_structure}")

    # 4. Add input section with clear boundaries
    parts.append("\n" + "=" * 80)
    parts.append("## INPUT DATA (Use ONLY this data - do not add anything else!)")
    parts.append("=" * 80)
    parts.append(f"\n**QUESTION:** {question}\n")
    parts.append(f"**DATA/ANSWER:**\n{answer}\n")
    parts.append("=" * 80)

    # 5. Final instruction with anti-hallucination reminder
    parts.append("""
## Task

Generate a markdown report based **strictly and exclusively** on the INPUT DATA above.

**REMEMBER:**
- Use only the data provided above - no external knowledge
- If a metric isn't in the input, don't include it
- Never invent numbers, names, or facts
- Label any analysis/interpretation clearly as such

Now generate the report:
""")

    return "\n".join(parts)


def load_preset(preset_name: str) -> dict:
    """
    Load a preset configuration from the YAML file.

    Args:
        preset_name: Name of the preset to load

    Returns:
        Dictionary with preset configuration
    """
    yaml_data = _load_yaml_data()
    presets = yaml_data.get("PRESETS", {})
    return presets.get(preset_name, {})


def build_prompt(template: str, question: str, answer: str) -> str:
    """
    Fill placeholders in the prompt template.

    This is the legacy function for backward compatibility.
    For new code, use build_prompt_with_config() instead.
    """
    # Use simple replacement instead of .format() to avoid conflicts
    # with JSON curly braces in Chart.js examples
    return template.replace("{question}", question).replace("{answer}", answer)
