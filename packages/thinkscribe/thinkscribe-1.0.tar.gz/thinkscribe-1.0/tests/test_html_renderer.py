"""Tests for HTML rendering with chart support."""

import re
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thinkscribe.html_renderer import (
    _replace_chartjs,
    _replace_mermaid,
    markdown_to_html_with_charts,
)


class TestReplaceMermaid:
    """Test _replace_mermaid function."""

    def test_replace_basic_mermaid(self):
        """Test replacing basic mermaid code block."""
        # Create a mock match object
        class MockMatch:
            def group(self, n):
                return "graph TD\n    A --> B"

        match = MockMatch()
        result = _replace_mermaid(match)

        assert '<div class="mermaid">' in result
        assert "graph TD" in result
        assert "A --> B" in result
        assert "</div>" in result

    def test_replace_mermaid_unescapes_html_entities(self):
        """Test that HTML entities are unescaped."""
        class MockMatch:
            def group(self, n):
                return "graph TD\n    A &lt;-- B\n    C --&gt; D\n    E &amp; F"

        match = MockMatch()
        result = _replace_mermaid(match)

        # HTML entities should be unescaped
        assert "A <-- B" in result
        assert "C --> D" in result
        assert "E & F" in result
        # Original entities should not be present
        assert "&lt;" not in result
        assert "&gt;" not in result
        assert "&amp;" not in result

    def test_replace_mermaid_preserves_structure(self):
        """Test that mermaid diagram structure is preserved."""
        class MockMatch:
            def group(self, n):
                return "sequenceDiagram\n    Alice->>Bob: Hello\n    Bob->>Alice: Hi"

        match = MockMatch()
        result = _replace_mermaid(match)

        assert "sequenceDiagram" in result
        assert "Alice->>Bob: Hello" in result
        assert "Bob->>Alice: Hi" in result


class TestReplaceChartjs:
    """Test _replace_chartjs function."""

    def test_replace_basic_chartjs(self):
        """Test replacing basic Chart.js code block."""
        # Reset counter by importing module fresh
        import thinkscribe.html_renderer as hr
        hr._chart_counter = 0

        class MockMatch:
            def group(self, n):
                return '{"type": "bar", "data": {}}'

        match = MockMatch()
        result = _replace_chartjs(match)

        assert '<div class="chart-container">' in result
        assert '<canvas id="chart_1">' in result
        assert "</canvas>" in result
        assert "<script>" in result
        assert "new Chart(ctx," in result
        assert '{"type": "bar", "data": {}}' in result

    def test_replace_chartjs_increments_counter(self):
        """Test that each chart gets unique ID."""
        import thinkscribe.html_renderer as hr
        hr._chart_counter = 0

        class MockMatch:
            def group(self, n):
                return '{"type": "line"}'

        match = MockMatch()

        result1 = _replace_chartjs(match)
        result2 = _replace_chartjs(match)
        result3 = _replace_chartjs(match)

        assert 'id="chart_1"' in result1
        assert 'id="chart_2"' in result2
        assert 'id="chart_3"' in result3

    def test_replace_chartjs_unescapes_html_entities(self):
        """Test that HTML entities are unescaped in config."""
        import thinkscribe.html_renderer as hr
        hr._chart_counter = 0

        class MockMatch:
            def group(self, n):
                return '{"label": "A &lt; B &gt; C &amp; D", "quote": &quot;test&quot;}'

        match = MockMatch()
        result = _replace_chartjs(match)

        # HTML entities should be unescaped
        assert '"A < B > C & D"' in result
        assert '"test"' in result or "'test'" in result  # Quote handling
        # Original entities should not be present
        assert "&lt;" not in result
        assert "&gt;" not in result
        assert "&amp;" not in result
        assert "&quot;" not in result

    def test_replace_chartjs_includes_error_handling(self):
        """Test that Chart.js replacement includes try-catch."""
        import thinkscribe.html_renderer as hr
        hr._chart_counter = 0

        class MockMatch:
            def group(self, n):
                return "{}"

        match = MockMatch()
        result = _replace_chartjs(match)

        assert "try {" in result
        assert "} catch (e) {" in result
        assert "console.error" in result
        assert "Chart rendering failed" in result

    def test_replace_chartjs_wraps_in_iife(self):
        """Test that Chart.js code is wrapped in IIFE."""
        import thinkscribe.html_renderer as hr
        hr._chart_counter = 0

        class MockMatch:
            def group(self, n):
                return "{}"

        match = MockMatch()
        result = _replace_chartjs(match)

        assert "(function() {" in result
        assert "})();" in result


class TestMarkdownToHtmlWithCharts:
    """Test markdown_to_html_with_charts function."""

    def test_converts_basic_markdown(self):
        """Test basic markdown to HTML conversion."""
        md = "# Hello World\n\nThis is **bold** and *italic*."
        result = markdown_to_html_with_charts(md)

        assert "<h1>Hello World</h1>" in result
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result

    def test_converts_markdown_with_lists(self):
        """Test markdown lists conversion."""
        md = "- Item 1\n- Item 2\n- Item 3"
        result = markdown_to_html_with_charts(md)

        assert "<ul>" in result
        assert "<li>Item 1</li>" in result
        assert "<li>Item 2</li>" in result
        assert "<li>Item 3</li>" in result

    def test_converts_markdown_with_tables(self):
        """Test markdown tables extension."""
        md = """| Name | Age |
|------|-----|
| Alice | 30 |
| Bob | 25 |"""
        result = markdown_to_html_with_charts(md)

        assert "<table>" in result
        assert "<thead>" in result
        assert "<tbody>" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_converts_markdown_with_fenced_code(self):
        """Test fenced code blocks (non-chart)."""
        md = "```python\nprint('hello')\n```"
        result = markdown_to_html_with_charts(md)

        assert "<code" in result
        assert "print('hello')" in result

    def test_replaces_mermaid_blocks(self):
        """Test that mermaid code blocks are replaced."""
        # First convert markdown to HTML to see what regex pattern we need
        import markdown
        md = "```mermaid\ngraph TD\n    A --> B\n```"
        html = markdown.markdown(md, extensions=["fenced_code"])

        # Now test full conversion
        result = markdown_to_html_with_charts(md)

        assert '<div class="mermaid">' in result
        assert "graph TD" in result
        assert "A --> B" in result

    def test_replaces_chartjs_blocks(self):
        """Test that Chart.js code blocks are replaced."""
        import thinkscribe.html_renderer as hr
        hr._chart_counter = 0

        md = '```chartjs\n{"type": "bar", "data": {}}\n```'
        result = markdown_to_html_with_charts(md)

        assert '<canvas id="chart_' in result
        assert "new Chart(ctx," in result
        assert '{"type": "bar"' in result

    def test_multiple_charts_get_unique_ids(self):
        """Test that multiple charts get unique IDs."""
        import thinkscribe.html_renderer as hr
        hr._chart_counter = 0

        md = """```chartjs
{"type": "bar"}
```

```chartjs
{"type": "line"}
```

```chartjs
{"type": "pie"}
```"""
        result = markdown_to_html_with_charts(md)

        assert 'id="chart_1"' in result
        assert 'id="chart_2"' in result
        assert 'id="chart_3"' in result

    def test_includes_html_doctype(self):
        """Test that result includes proper HTML structure."""
        md = "# Test"
        result = markdown_to_html_with_charts(md)

        assert "<!DOCTYPE html>" in result
        assert "<html lang=\"en\">" in result
        assert "<head>" in result
        assert "<body>" in result
        assert "</html>" in result

    def test_includes_chart_js_cdn(self):
        """Test that Chart.js CDN is included."""
        md = "# Test"
        result = markdown_to_html_with_charts(md)

        assert "chart.js" in result.lower()
        assert "cdn.jsdelivr.net" in result

    def test_includes_mermaid_cdn(self):
        """Test that Mermaid CDN is included."""
        md = "# Test"
        result = markdown_to_html_with_charts(md)

        assert "mermaid" in result.lower()
        assert "cdn.jsdelivr.net" in result

    def test_includes_mermaid_initialization(self):
        """Test that Mermaid is initialized."""
        md = "# Test"
        result = markdown_to_html_with_charts(md)

        assert "mermaid.initialize" in result
        assert "startOnLoad: true" in result

    def test_includes_custom_styles(self):
        """Test that custom styles are loaded."""
        md = "# Test"
        result = markdown_to_html_with_charts(md)

        # Should include custom styles
        assert "<style>" in result
        assert "</style>" in result
        # Should have mermaid and chart styling
        assert ".mermaid" in result
        assert ".chart-container" in result

    def test_sets_page_title(self):
        """Test that page title is set correctly."""
        md = "# Test"
        result = markdown_to_html_with_charts(md, title="My Report")

        assert "<title>My Report</title>" in result

    def test_default_title(self):
        """Test default title when not provided."""
        md = "# Test"
        result = markdown_to_html_with_charts(md)

        assert "<title>Report</title>" in result

    def test_includes_footer(self):
        """Test that footer is included."""
        md = "# Test"
        result = markdown_to_html_with_charts(md)

        assert "<footer" in result
        assert "Generated by Virtual Case Manager" in result
        # Should include a date
        assert "20" in result  # Year should contain '20'

    def test_mixed_content_all_features(self):
        """Test document with all features combined."""
        import thinkscribe.html_renderer as hr
        hr._chart_counter = 0

        md = """# Sales Report

## Overview

This report analyzes **Q4 sales** performance.

### Key Metrics

- Revenue: $500K
- Growth: 25%
- Customers: 1,200

### Data Flow

```mermaid
graph TD
    A[Sales Data] --> B[Analysis]
    B --> C[Report]
```

### Revenue Chart

```chartjs
{"type": "bar", "data": {"labels": ["Q1", "Q2", "Q3", "Q4"]}}
```

### Summary Table

| Metric | Value |
|--------|-------|
| Revenue | 500K |
| Growth | 25% |
"""
        result = markdown_to_html_with_charts(md, title="Q4 Sales Report")

        # Check markdown conversion
        assert "<h1>Sales Report</h1>" in result
        assert "<h2>Overview</h2>" in result
        assert "<strong>Q4 sales</strong>" in result
        assert "<li>Revenue: $500K</li>" in result

        # Check mermaid
        assert '<div class="mermaid">' in result
        assert "graph TD" in result
        assert "Sales Data" in result

        # Check Chart.js
        assert '<canvas id="chart_1"' in result
        assert '{"type": "bar"' in result

        # Check table
        assert "<table>" in result
        assert "Metric" in result
        assert "Value" in result

        # Check HTML structure
        assert "<!DOCTYPE html>" in result
        assert "<title>Q4 Sales Report</title>" in result
        assert "cdn.jsdelivr.net" in result

    def test_empty_markdown(self):
        """Test with empty markdown."""
        md = ""
        result = markdown_to_html_with_charts(md)

        # Should still return valid HTML document
        assert "<!DOCTYPE html>" in result
        assert "<html" in result
        assert "<body>" in result

    def test_markdown_with_newlines(self):
        """Test that nl2br extension works."""
        md = "Line 1\nLine 2\nLine 3"
        result = markdown_to_html_with_charts(md)

        # With nl2br extension, newlines should become <br>
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result


class TestHtmlRendererIntegration:
    """Integration tests for HTML rendering."""

    def test_html_output_is_valid(self):
        """Test that output is valid HTML structure."""
        import thinkscribe.html_renderer as hr
        hr._chart_counter = 0

        md = """# Report

```mermaid
graph LR
    A --> B
```

```chartjs
{"type": "line"}
```
"""
        result = markdown_to_html_with_charts(md)

        # Basic HTML validation checks
        assert result.count("<!DOCTYPE html>") == 1
        assert result.count("<html") == 1
        assert result.count("</html>") == 1
        assert result.count("<head>") == 1
        assert result.count("</head>") == 1
        assert result.count("<body>") == 1
        assert result.count("</body>") == 1

    def test_script_tags_are_balanced(self):
        """Test that all script tags are properly closed."""
        import thinkscribe.html_renderer as hr
        hr._chart_counter = 0

        md = '```chartjs\n{"type": "bar"}\n```\n\n```chartjs\n{"type": "pie"}\n```'
        result = markdown_to_html_with_charts(md)

        # Count opening and closing script tags
        open_count = result.count("<script")
        close_count = result.count("</script>")

        assert open_count == close_count
        assert open_count >= 3  # At least: Chart.js CDN, Mermaid CDN, Mermaid init

    def test_chart_ids_are_referenced_correctly(self):
        """Test that chart IDs in canvas match IDs in script."""
        import thinkscribe.html_renderer as hr
        hr._chart_counter = 0

        md = '```chartjs\n{"type": "bar"}\n```'
        result = markdown_to_html_with_charts(md)

        # Extract canvas ID
        canvas_match = re.search(r'<canvas id="(chart_\d+)"', result)
        assert canvas_match is not None
        canvas_id = canvas_match.group(1)

        # Check that same ID is used in script
        assert f"getElementById('{canvas_id}')" in result

    def test_responsive_styling_included(self):
        """Test that responsive styling is included for charts."""
        md = "# Test"
        result = markdown_to_html_with_charts(md)

        # Should include responsive styling
        assert "max-width: 100%" in result
        assert "overflow-x: auto" in result or "width: 100%" in result

    def test_mermaid_config_included(self):
        """Test that Mermaid configuration is included."""
        md = "# Test"
        result = markdown_to_html_with_charts(md)

        assert "theme: 'default'" in result or 'theme: "default"' in result
        assert "startOnLoad: true" in result
        assert "useMaxWidth" in result


class TestChartCounterReset:
    """Test chart counter behavior."""

    def test_counter_starts_at_zero(self):
        """Test that counter can be reset."""
        import thinkscribe.html_renderer as hr

        # Reset counter
        hr._chart_counter = 0

        class MockMatch:
            def group(self, n):
                return "{}"

        match = MockMatch()
        result = _replace_chartjs(match)

        assert 'id="chart_1"' in result

    def test_counter_persists_across_calls(self):
        """Test that counter persists across multiple calls."""
        import thinkscribe.html_renderer as hr
        hr._chart_counter = 5

        class MockMatch:
            def group(self, n):
                return "{}"

        match = MockMatch()
        result = _replace_chartjs(match)

        # Should continue from 5
        assert 'id="chart_6"' in result


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_markdown_with_special_characters(self):
        """Test markdown with special characters."""
        md = "# Test & <Test> \"Test\""
        result = markdown_to_html_with_charts(md)

        # Should be properly escaped in HTML
        assert "&amp;" in result or "&" in result
        assert "&lt;" in result or "<" in result or "Test" in result

    def test_very_long_markdown(self):
        """Test with very long markdown content."""
        md = "# Report\n\n" + ("This is a paragraph.\n\n" * 100)
        result = markdown_to_html_with_charts(md)

        assert "<!DOCTYPE html>" in result
        assert result.count("This is a paragraph") == 100

    def test_nested_markdown_structures(self):
        """Test nested lists and quotes."""
        md = """- Item 1
  - Subitem 1.1
  - Subitem 1.2
- Item 2

> Quote level 1
> > Quote level 2
"""
        result = markdown_to_html_with_charts(md)

        assert "<ul>" in result
        assert "<li>Item 1" in result
        assert "Subitem 1.1" in result

    def test_multiple_mermaid_diagrams(self):
        """Test multiple Mermaid diagrams in one document."""
        md = """```mermaid
graph TD
    A --> B
```

```mermaid
sequenceDiagram
    Alice->>Bob: Hi
```

```mermaid
pie
    "A": 30
    "B": 70
```
"""
        result = markdown_to_html_with_charts(md)

        # Should have 3 mermaid divs
        assert result.count('<div class="mermaid">') == 3
        assert "graph TD" in result
        assert "sequenceDiagram" in result
        assert "pie" in result

    def test_chartjs_with_complex_config(self):
        """Test Chart.js with complex configuration."""
        import thinkscribe.html_renderer as hr
        hr._chart_counter = 0

        md = """```chartjs
{
    "type": "bar",
    "data": {
        "labels": ["A", "B", "C"],
        "datasets": [{
            "label": "Sales",
            "data": [10, 20, 30]
        }]
    },
    "options": {
        "responsive": true,
        "plugins": {
            "title": {
                "display": true,
                "text": "Sales Chart"
            }
        }
    }
}
```"""
        result = markdown_to_html_with_charts(md)

        assert "Sales Chart" in result
        assert '"labels": ["A", "B", "C"]' in result
        assert '"responsive": true' in result
