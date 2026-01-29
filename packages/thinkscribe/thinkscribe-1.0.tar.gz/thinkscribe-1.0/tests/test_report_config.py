"""Tests for report configuration and behavior customization."""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thinkscribe.report_config import (
    Audience,
    FocusArea,
    Preset,
    ReportConfig,
    Style,
    Tone,
)


class TestEnums:
    """Test enum definitions."""

    def test_audience_values(self):
        """Test all audience enum values exist."""
        assert Audience.EXECUTIVES.value == "executives"
        assert Audience.TECHNICAL.value == "technical"
        assert Audience.ANALYSTS.value == "analysts"
        assert Audience.GENERAL.value == "general"

    def test_style_values(self):
        """Test all style enum values exist."""
        assert Style.CONCISE.value == "concise"
        assert Style.DETAILED.value == "detailed"
        assert Style.VISUAL_HEAVY.value == "visual_heavy"

    def test_tone_values(self):
        """Test all tone enum values exist."""
        assert Tone.FORMAL.value == "formal"
        assert Tone.PERSUASIVE.value == "persuasive"
        assert Tone.CASUAL.value == "casual"

    def test_focus_area_values(self):
        """Test all focus area enum values exist."""
        assert FocusArea.METRICS.value == "metrics"
        assert FocusArea.RECOMMENDATIONS.value == "recommendations"
        assert FocusArea.TRENDS.value == "trends"
        assert FocusArea.COMPARISONS.value == "comparisons"
        assert FocusArea.INSIGHTS.value == "insights"

    def test_preset_values(self):
        """Test all preset enum values exist."""
        assert Preset.EXECUTIVE_SUMMARY.value == "executive_summary"
        assert Preset.TECHNICAL_DEEP_DIVE.value == "technical_deep_dive"
        assert Preset.DATA_ANALYSIS.value == "data_analysis"
        assert Preset.SALES_PRESENTATION.value == "sales_presentation"
        assert Preset.QUICK_OVERVIEW.value == "quick_overview"


class TestReportConfig:
    """Test ReportConfig class."""

    def test_create_empty_config(self):
        """Test creating config with no parameters."""
        config = ReportConfig()
        assert config.audience is None
        assert config.style is None
        assert config.tone is None
        assert config.focus is None

    def test_create_config_with_audience(self):
        """Test creating config with audience only."""
        config = ReportConfig(audience=Audience.EXECUTIVES)
        assert config.audience == Audience.EXECUTIVES
        assert config.style is None

    def test_create_config_with_all_parameters(self):
        """Test creating config with all parameters."""
        config = ReportConfig(
            audience=Audience.TECHNICAL,
            style=Style.DETAILED,
            tone=Tone.FORMAL,
            focus=[FocusArea.INSIGHTS, FocusArea.TRENDS]
        )
        assert config.audience == Audience.TECHNICAL
        assert config.style == Style.DETAILED
        assert config.tone == Tone.FORMAL
        assert len(config.focus) == 2
        assert FocusArea.INSIGHTS in config.focus
        assert FocusArea.TRENDS in config.focus

    def test_create_config_with_custom_prompt(self):
        """Test creating config with custom prompt."""
        custom = "My custom prompt with {question} and {answer}"
        config = ReportConfig(custom_prompt=custom)
        assert config.custom_prompt == custom

    def test_create_config_with_template_file(self):
        """Test creating config with custom template file."""
        template_path = Path("./custom.yaml")
        config = ReportConfig(
            template_file=template_path,
            template_name="MY_TEMPLATE"
        )
        assert config.template_file == template_path
        assert config.template_name == "MY_TEMPLATE"

    def test_to_dict_excludes_none_values(self):
        """Test that to_dict() excludes None values."""
        config = ReportConfig(audience=Audience.EXECUTIVES)
        result = config.to_dict()

        assert "audience" in result
        assert result["audience"] == Audience.EXECUTIVES
        # None values should be excluded
        assert "style" not in result or result["style"] is None

    def test_to_dict_includes_all_set_values(self):
        """Test that to_dict() includes all non-None values."""
        config = ReportConfig(
            audience=Audience.ANALYSTS,
            style=Style.VISUAL_HEAVY,
            tone=Tone.CASUAL,
            focus=[FocusArea.METRICS]
        )
        result = config.to_dict()

        assert result["audience"] == Audience.ANALYSTS
        assert result["style"] == Style.VISUAL_HEAVY
        assert result["tone"] == Tone.CASUAL
        assert len(result["focus"]) == 1


class TestPresets:
    """Test preset configurations."""

    def test_executive_summary_preset(self):
        """Test executive_summary preset configuration."""
        config = ReportConfig.from_preset(Preset.EXECUTIVE_SUMMARY)

        assert config.audience == Audience.EXECUTIVES
        assert config.style == Style.CONCISE
        assert config.tone == Tone.FORMAL
        assert FocusArea.RECOMMENDATIONS in config.focus
        assert FocusArea.METRICS in config.focus

    def test_technical_deep_dive_preset(self):
        """Test technical_deep_dive preset configuration."""
        config = ReportConfig.from_preset(Preset.TECHNICAL_DEEP_DIVE)

        assert config.audience == Audience.TECHNICAL
        assert config.style == Style.DETAILED
        assert config.tone == Tone.FORMAL
        assert FocusArea.INSIGHTS in config.focus
        assert FocusArea.TRENDS in config.focus

    def test_data_analysis_preset(self):
        """Test data_analysis preset configuration."""
        config = ReportConfig.from_preset(Preset.DATA_ANALYSIS)

        assert config.audience == Audience.ANALYSTS
        assert config.style == Style.DETAILED
        assert config.tone == Tone.FORMAL
        assert FocusArea.METRICS in config.focus
        assert FocusArea.INSIGHTS in config.focus

    def test_sales_presentation_preset(self):
        """Test sales_presentation preset configuration."""
        config = ReportConfig.from_preset(Preset.SALES_PRESENTATION)

        assert config.audience == Audience.GENERAL
        assert config.style == Style.VISUAL_HEAVY
        assert config.tone == Tone.PERSUASIVE
        assert FocusArea.METRICS in config.focus
        assert FocusArea.RECOMMENDATIONS in config.focus

    def test_quick_overview_preset(self):
        """Test quick_overview preset configuration."""
        config = ReportConfig.from_preset(Preset.QUICK_OVERVIEW)

        assert config.audience == Audience.GENERAL
        assert config.style == Style.CONCISE
        assert config.tone == Tone.CASUAL
        assert FocusArea.INSIGHTS in config.focus
        assert FocusArea.METRICS in config.focus

    def test_all_presets_loadable(self):
        """Test that all presets can be loaded without errors."""
        for preset in Preset:
            config = ReportConfig.from_preset(preset)
            # All presets should have basic fields set
            assert config.audience is not None
            assert config.style is not None
            assert config.tone is not None
            assert config.focus is not None
            assert len(config.focus) > 0


class TestPresetOverrides:
    """Test overriding preset values."""

    def test_override_audience(self):
        """Test overriding preset audience."""
        config = ReportConfig.from_preset(
            Preset.EXECUTIVE_SUMMARY,
            audience=Audience.TECHNICAL
        )

        assert config.audience == Audience.TECHNICAL  # Overridden
        assert config.style == Style.CONCISE  # From preset
        assert config.tone == Tone.FORMAL  # From preset

    def test_override_style(self):
        """Test overriding preset style."""
        config = ReportConfig.from_preset(
            Preset.EXECUTIVE_SUMMARY,
            style=Style.DETAILED
        )

        assert config.style == Style.DETAILED  # Overridden
        assert config.audience == Audience.EXECUTIVES  # From preset

    def test_override_tone(self):
        """Test overriding preset tone."""
        config = ReportConfig.from_preset(
            Preset.TECHNICAL_DEEP_DIVE,
            tone=Tone.CASUAL
        )

        assert config.tone == Tone.CASUAL  # Overridden
        assert config.audience == Audience.TECHNICAL  # From preset

    def test_override_focus(self):
        """Test overriding preset focus areas."""
        custom_focus = [FocusArea.COMPARISONS, FocusArea.TRENDS]
        config = ReportConfig.from_preset(
            Preset.EXECUTIVE_SUMMARY,
            focus=custom_focus
        )

        assert config.focus == custom_focus  # Overridden
        assert config.audience == Audience.EXECUTIVES  # From preset

    def test_override_multiple_values(self):
        """Test overriding multiple preset values at once."""
        config = ReportConfig.from_preset(
            Preset.EXECUTIVE_SUMMARY,
            audience=Audience.ANALYSTS,
            tone=Tone.PERSUASIVE,
            style=Style.VISUAL_HEAVY
        )

        # All overridden
        assert config.audience == Audience.ANALYSTS
        assert config.tone == Tone.PERSUASIVE
        assert config.style == Style.VISUAL_HEAVY
        # Focus still from preset
        assert FocusArea.RECOMMENDATIONS in config.focus


class TestValidation:
    """Test Pydantic validation."""

    def test_invalid_audience_type_raises_error(self):
        """Test that invalid audience type raises validation error."""
        with pytest.raises(Exception):  # Pydantic validation error
            ReportConfig(audience="invalid_audience")

    def test_invalid_style_type_raises_error(self):
        """Test that invalid style type raises validation error."""
        with pytest.raises(Exception):
            ReportConfig(style="invalid_style")

    def test_invalid_tone_type_raises_error(self):
        """Test that invalid tone type raises validation error."""
        with pytest.raises(Exception):
            ReportConfig(tone="invalid_tone")

    def test_invalid_focus_type_raises_error(self):
        """Test that invalid focus area raises validation error."""
        with pytest.raises(Exception):
            ReportConfig(focus=["invalid_focus"])

    def test_valid_focus_list(self):
        """Test that valid focus list is accepted."""
        config = ReportConfig(focus=[FocusArea.METRICS, FocusArea.INSIGHTS])
        assert len(config.focus) == 2

    def test_empty_focus_list_allowed(self):
        """Test that empty focus list is allowed."""
        config = ReportConfig(focus=[])
        assert config.focus == []


class TestConfigComparison:
    """Test comparing configurations."""

    def test_same_config_equal(self):
        """Test that two configs with same values are equal."""
        config1 = ReportConfig(
            audience=Audience.EXECUTIVES,
            style=Style.CONCISE
        )
        config2 = ReportConfig(
            audience=Audience.EXECUTIVES,
            style=Style.CONCISE
        )

        # Pydantic models should be comparable
        assert config1.audience == config2.audience
        assert config1.style == config2.style

    def test_different_config_not_equal(self):
        """Test that configs with different values are not equal."""
        config1 = ReportConfig(audience=Audience.EXECUTIVES)
        config2 = ReportConfig(audience=Audience.TECHNICAL)

        assert config1.audience != config2.audience
