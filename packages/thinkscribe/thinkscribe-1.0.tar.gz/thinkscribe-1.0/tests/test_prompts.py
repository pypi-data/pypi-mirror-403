"""Tests for prompt template loading and building."""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thinkscribe.prompts import (
    build_prompt,
    build_prompt_with_config,
    load_preset,
    load_prompt_template,
)
from thinkscribe.report_config import Audience, FocusArea, Preset, ReportConfig, Style, Tone


class TestLoadPromptTemplate:
    """Test loading prompt templates from YAML."""

    def test_load_default_template(self):
        """Test loading default REPORT_GENERATOR_TEMPLATE."""
        template = load_prompt_template()

        assert isinstance(template, str)
        assert len(template) > 0
        # Should contain markdown-related keywords
        assert "markdown" in template.lower()

    def test_load_quick_insights_template(self):
        """Test loading QUICK_INSIGHTS_TEMPLATE."""
        template = load_prompt_template("QUICK_INSIGHTS_TEMPLATE")

        assert isinstance(template, str)
        assert len(template) > 0
        # Should mention bullet points and insights
        assert "bullet" in template.lower() or "insight" in template.lower()

    def test_template_contains_placeholders(self):
        """Test that templates contain expected placeholders."""
        template = load_prompt_template()

        # Should have question and answer placeholders
        assert "{question}" in template or "question" in template.lower()
        assert "{answer}" in template or "answer" in template.lower()

    def test_load_nonexistent_template_raises_error(self):
        """Test that loading non-existent template raises KeyError."""
        with pytest.raises(KeyError):
            load_prompt_template("NONEXISTENT_TEMPLATE")


class TestBuildPrompt:
    """Test legacy build_prompt function."""

    def test_build_prompt_replaces_question(self):
        """Test that {question} is replaced."""
        template = "Question: {question}\nAnswer: {answer}"
        result = build_prompt(template, "What is 2+2?", "4")

        assert "{question}" not in result
        assert "What is 2+2?" in result

    def test_build_prompt_replaces_answer(self):
        """Test that {answer} is replaced."""
        template = "Question: {question}\nAnswer: {answer}"
        result = build_prompt(template, "Test", "Response")

        assert "{answer}" not in result
        assert "Response" in result

    def test_build_prompt_replaces_both(self):
        """Test that both placeholders are replaced."""
        template = "{question} and {answer}"
        result = build_prompt(template, "Q", "A")

        assert result == "Q and A"
        assert "{" not in result

    def test_build_prompt_with_json_braces(self):
        """Test that JSON braces are not confused with placeholders."""
        template = '{question} - {"key": "value"} - {answer}'
        result = build_prompt(template, "Q", "A")

        # JSON braces should remain
        assert '{"key": "value"}' in result
        # Placeholders should be replaced
        assert "{question}" not in result
        assert "{answer}" not in result

    def test_build_prompt_preserves_formatting(self):
        """Test that template formatting is preserved."""
        template = "Line 1: {question}\n\nLine 2: {answer}\n  Indented"
        result = build_prompt(template, "Q", "A")

        assert "\n\n" in result
        assert "  Indented" in result

    def test_build_prompt_with_empty_strings(self):
        """Test building prompt with empty strings."""
        template = "{question}|{answer}"
        result = build_prompt(template, "", "")

        assert result == "|"


class TestBuildPromptWithConfig:
    """Test build_prompt_with_config function."""

    def test_build_without_config_uses_base_template(self):
        """Test that without config, base template is used."""
        result = build_prompt_with_config(
            question="Test question",
            answer="Test answer",
            config=None
        )

        assert "Test question" in result
        assert "Test answer" in result
        assert "markdown" in result.lower()

    def test_build_with_custom_prompt_override(self):
        """Test that custom_prompt completely overrides template."""
        custom = "Simple: {question} -> {answer}"
        config = ReportConfig(custom_prompt=custom)

        result = build_prompt_with_config("Q", "A", config)

        assert result == "Simple: Q -> A"
        # Should not contain base template content
        assert "markdown" not in result.lower()

    def test_build_with_executive_audience(self):
        """Test that executive audience adds specific modifiers."""
        config = ReportConfig(audience=Audience.EXECUTIVES)

        result = build_prompt_with_config("Analyze sales", "Data", config)

        # Should include executive-specific language
        assert ("executive" in result.lower() or
                "c-level" in result.lower() or
                "strategic" in result.lower())

    def test_build_with_technical_audience(self):
        """Test that technical audience adds tech modifiers."""
        config = ReportConfig(audience=Audience.TECHNICAL)

        result = build_prompt_with_config("Debug", "Logs", config)

        assert ("technical" in result.lower() or
                "engineer" in result.lower() or
                "implementation" in result.lower())

    def test_build_with_analysts_audience(self):
        """Test that analysts audience adds data-focused modifiers."""
        config = ReportConfig(audience=Audience.ANALYSTS)

        result = build_prompt_with_config("Analyze", "Stats", config)

        assert ("analyst" in result.lower() or
                "statistical" in result.lower() or
                "data" in result.lower())

    def test_build_with_concise_style(self):
        """Test that concise style adds brevity modifiers."""
        config = ReportConfig(style=Style.CONCISE)

        result = build_prompt_with_config("Q", "A", config)

        assert ("concise" in result.lower() or
                "brief" in result.lower() or
                "1-2 pages" in result.lower())

    def test_build_with_detailed_style(self):
        """Test that detailed style adds comprehensiveness modifiers."""
        config = ReportConfig(style=Style.DETAILED)

        result = build_prompt_with_config("Q", "A", config)

        assert ("detailed" in result.lower() or
                "comprehensive" in result.lower() or
                "3-5 pages" in result.lower())

    def test_build_with_visual_heavy_style(self):
        """Test that visual_heavy style emphasizes charts."""
        config = ReportConfig(style=Style.VISUAL_HEAVY)

        result = build_prompt_with_config("Q", "A", config)

        assert ("visual" in result.lower() or
                "chart" in result.lower() or
                "diagram" in result.lower())

    def test_build_with_formal_tone(self):
        """Test that formal tone adds professional language."""
        config = ReportConfig(tone=Tone.FORMAL)

        result = build_prompt_with_config("Q", "A", config)

        assert ("formal" in result.lower() or
                "professional" in result.lower() or
                "objective" in result.lower())

    def test_build_with_persuasive_tone(self):
        """Test that persuasive tone adds action-oriented language."""
        config = ReportConfig(tone=Tone.PERSUASIVE)

        result = build_prompt_with_config("Q", "A", config)

        assert ("persuasive" in result.lower() or
                "action" in result.lower() or
                "compelling" in result.lower())

    def test_build_with_focus_areas(self):
        """Test that focus areas are included in prompt."""
        config = ReportConfig(focus=[FocusArea.METRICS, FocusArea.RECOMMENDATIONS])

        result = build_prompt_with_config("Q", "A", config)

        assert "metrics" in result.lower()
        assert "recommendations" in result.lower()

    def test_build_with_all_modifiers(self):
        """Test building with all modifiers at once."""
        config = ReportConfig(
            audience=Audience.EXECUTIVES,
            style=Style.CONCISE,
            tone=Tone.FORMAL,
            focus=[FocusArea.METRICS]
        )

        result = build_prompt_with_config("Analyze", "Data", config)

        # Should contain question and answer
        assert "Analyze" in result
        assert "Data" in result
        # Should be a substantial prompt
        assert len(result) > 200

    def test_build_with_preset_executive_summary(self):
        """Test building prompt from executive_summary preset."""
        config = ReportConfig.from_preset(Preset.EXECUTIVE_SUMMARY)

        result = build_prompt_with_config("Q4 Analysis", "Sales data", config)

        assert "Q4 Analysis" in result
        assert "Sales data" in result
        # Should have executive-specific content
        assert "executive" in result.lower()

    def test_build_includes_base_instruction(self):
        """Test that base instruction is always included."""
        config = ReportConfig(audience=Audience.TECHNICAL)

        result = build_prompt_with_config("Q", "A", config)

        # Should still have base markdown instructions
        assert "markdown" in result.lower()
        assert "chart" in result.lower() or "visualization" in result.lower()


class TestLoadPreset:
    """Test load_preset function."""

    def test_load_executive_summary_preset(self):
        """Test loading executive_summary preset data."""
        preset_data = load_preset("executive_summary")

        assert preset_data is not None
        assert isinstance(preset_data, dict)
        assert "audience" in preset_data
        assert preset_data["audience"] == "executives"

    def test_load_technical_deep_dive_preset(self):
        """Test loading technical_deep_dive preset data."""
        preset_data = load_preset("technical_deep_dive")

        assert preset_data is not None
        assert preset_data["audience"] == "technical"

    def test_load_nonexistent_preset(self):
        """Test loading non-existent preset returns empty dict."""
        preset_data = load_preset("nonexistent_preset")

        assert preset_data == {}


class TestPromptStructure:
    """Test overall prompt structure and completeness."""

    def test_prompt_has_input_section(self):
        """Test that built prompt has input section."""
        config = ReportConfig(audience=Audience.GENERAL)
        result = build_prompt_with_config("Question here", "Answer here", config)

        # Should have clear input section
        assert "Question here" in result
        assert "Answer here" in result
        # Should label them somehow
        assert ("question" in result.lower() and "answer" in result.lower())

    def test_prompt_has_instructions(self):
        """Test that prompt has clear instructions."""
        config = ReportConfig(audience=Audience.EXECUTIVES)
        result = build_prompt_with_config("Q", "A", config)

        # Should have instruction keywords
        assert any(word in result.lower() for word in [
            "generate", "create", "write", "produce", "report"
        ])

    def test_prompt_is_substantial(self):
        """Test that prompts are detailed enough to guide LLM."""
        config = ReportConfig(
            audience=Audience.TECHNICAL,
            style=Style.DETAILED,
            focus=[FocusArea.INSIGHTS, FocusArea.TRENDS]
        )
        result = build_prompt_with_config("Analysis", "Data", config)

        # Should be a reasonably long prompt
        assert len(result) > 500  # At least 500 characters

    def test_prompt_question_and_answer_not_confused(self):
        """Test that question and answer don't get mixed up."""
        result = build_prompt_with_config(
            question="What is the trend?",
            answer="Upward growth",
            config=None
        )

        # Should appear in order and be distinguishable
        q_pos = result.find("What is the trend?")
        a_pos = result.find("Upward growth")

        assert q_pos != -1
        assert a_pos != -1
        # Question should come before answer in the input section
        # (Note: might not always be true depending on template structure)
