"""Report configuration classes for behavior customization."""

from enum import Enum
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Audience(str, Enum):
    """Target audience for the report."""

    EXECUTIVES = "executives"
    TECHNICAL = "technical"
    ANALYSTS = "analysts"
    GENERAL = "general"


class Style(str, Enum):
    """Report style/length."""

    CONCISE = "concise"
    DETAILED = "detailed"
    VISUAL_HEAVY = "visual_heavy"


class Tone(str, Enum):
    """Report tone/voice."""

    FORMAL = "formal"
    PERSUASIVE = "persuasive"
    CASUAL = "casual"


class FocusArea(str, Enum):
    """Areas to emphasize in the report."""

    METRICS = "metrics"
    RECOMMENDATIONS = "recommendations"
    TRENDS = "trends"
    COMPARISONS = "comparisons"
    INSIGHTS = "insights"


class Preset(str, Enum):
    """Pre-configured report templates."""

    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
    DATA_ANALYSIS = "data_analysis"
    SALES_PRESENTATION = "sales_presentation"
    QUICK_OVERVIEW = "quick_overview"


class ReportConfig(BaseModel):
    """
    Configuration for report generation behavior.

    This allows fine-tuning the report output for different audiences,
    styles, and purposes without writing custom prompts.

    Examples:
        # Using individual parameters
        config = ReportConfig(
            audience=Audience.EXECUTIVES,
            style=Style.CONCISE,
            tone=Tone.FORMAL
        )

        # Using a preset
        config = ReportConfig.from_preset(Preset.EXECUTIVE_SUMMARY)

        # Override preset with custom values
        config = ReportConfig.from_preset(
            Preset.TECHNICAL_DEEP_DIVE,
            tone=Tone.CASUAL
        )
    """

    audience: Optional[Audience] = Field(
        default=None,
        description="Target audience for the report",
    )
    style: Optional[Style] = Field(
        default=None,
        description="Report style/length preference",
    )
    tone: Optional[Tone] = Field(
        default=None,
        description="Report tone/voice",
    )
    focus: Optional[list[FocusArea]] = Field(
        default=None,
        description="Areas to emphasize in the report",
    )
    template_file: Optional[Path] = Field(
        default=None,
        description="Path to custom template YAML file",
    )
    template_name: Optional[str] = Field(
        default=None,
        description="Name of template to use from template_file",
    )
    custom_prompt: Optional[str] = Field(
        default=None,
        description="Complete custom prompt (overrides all other settings)",
    )

    @classmethod
    def from_preset(
        cls,
        preset: Preset,
        audience: Optional[Audience] = None,
        style: Optional[Style] = None,
        tone: Optional[Tone] = None,
        focus: Optional[list[FocusArea]] = None,
    ) -> "ReportConfig":
        """
        Create a ReportConfig from a preset.

        Args:
            preset: The preset configuration to use
            audience: Override preset's audience
            style: Override preset's style
            tone: Override preset's tone
            focus: Override preset's focus areas

        Returns:
            ReportConfig with preset values and any overrides applied
        """
        # Define preset configurations
        preset_configs = {
            Preset.EXECUTIVE_SUMMARY: {
                "audience": Audience.EXECUTIVES,
                "style": Style.CONCISE,
                "tone": Tone.FORMAL,
                "focus": [FocusArea.RECOMMENDATIONS, FocusArea.METRICS],
            },
            Preset.TECHNICAL_DEEP_DIVE: {
                "audience": Audience.TECHNICAL,
                "style": Style.DETAILED,
                "tone": Tone.FORMAL,
                "focus": [FocusArea.INSIGHTS, FocusArea.TRENDS],
            },
            Preset.DATA_ANALYSIS: {
                "audience": Audience.ANALYSTS,
                "style": Style.DETAILED,
                "tone": Tone.FORMAL,
                "focus": [FocusArea.METRICS, FocusArea.INSIGHTS],
            },
            Preset.SALES_PRESENTATION: {
                "audience": Audience.GENERAL,
                "style": Style.VISUAL_HEAVY,
                "tone": Tone.PERSUASIVE,
                "focus": [FocusArea.METRICS, FocusArea.RECOMMENDATIONS],
            },
            Preset.QUICK_OVERVIEW: {
                "audience": Audience.GENERAL,
                "style": Style.CONCISE,
                "tone": Tone.CASUAL,
                "focus": [FocusArea.INSIGHTS, FocusArea.METRICS],
            },
        }

        config = preset_configs[preset].copy()

        # Apply overrides
        if audience is not None:
            config["audience"] = audience
        if style is not None:
            config["style"] = style
        if tone is not None:
            config["tone"] = tone
        if focus is not None:
            config["focus"] = focus

        return cls(**config)

    def to_dict(self) -> dict:
        """Convert config to dictionary, excluding None values."""
        return {
            k: v
            for k, v in self.model_dump().items()
            if v is not None
        }
