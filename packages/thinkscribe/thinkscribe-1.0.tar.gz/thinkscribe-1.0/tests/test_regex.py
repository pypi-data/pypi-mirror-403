"""Tests for regex patterns used in code block detection."""

import re
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thinkscribe.regex import CHARTJS_CODE_BLOCK_RE, MERMAID_CODE_BLOCK_RE


class TestMermaidRegex:
    """Test Mermaid code block regex pattern."""

    def test_matches_basic_mermaid_block(self):
        """Test matching basic Mermaid code block."""
        html = '<pre><code class="language-mermaid">graph TD</code></pre>'
        match = MERMAID_CODE_BLOCK_RE.search(html)

        assert match is not None
        assert match.group(1) == "graph TD"

    def test_matches_multiline_mermaid(self):
        """Test matching multiline Mermaid diagram."""
        html = '''<pre><code class="language-mermaid">graph TD
    A --> B
    B --> C</code></pre>'''
        match = MERMAID_CODE_BLOCK_RE.search(html)

        assert match is not None
        content = match.group(1)
        assert "graph TD" in content
        assert "A --> B" in content
        assert "B --> C" in content

    def test_matches_flowchart(self):
        """Test matching Mermaid flowchart."""
        html = '''<pre><code class="language-mermaid">flowchart LR
    Start --> Stop</code></pre>'''
        match = MERMAID_CODE_BLOCK_RE.search(html)

        assert match is not None
        assert "flowchart LR" in match.group(1)

    def test_matches_with_newlines(self):
        """Test matching diagram with multiple newlines."""
        html = '<pre><code class="language-mermaid">\n\ngraph TD\n\n</code></pre>'
        match = MERMAID_CODE_BLOCK_RE.search(html)

        assert match is not None

    def test_does_not_match_wrong_language(self):
        """Test that non-mermaid code blocks don't match."""
        html = '<pre><code class="language-python">print("hello")</code></pre>'
        match = MERMAID_CODE_BLOCK_RE.search(html)

        assert match is None

    def test_does_not_match_plain_code(self):
        """Test that plain code blocks without language don't match."""
        html = '<pre><code>graph TD</code></pre>'
        match = MERMAID_CODE_BLOCK_RE.search(html)

        assert match is None

    def test_matches_pie_chart(self):
        """Test matching Mermaid pie chart."""
        html = '''<pre><code class="language-mermaid">pie
    "Dogs" : 42
    "Cats" : 35</code></pre>'''
        match = MERMAID_CODE_BLOCK_RE.search(html)

        assert match is not None
        assert "pie" in match.group(1)

    def test_captures_content_only(self):
        """Test that only inner content is captured, not tags."""
        html = '<pre><code class="language-mermaid">graph TD</code></pre>'
        match = MERMAID_CODE_BLOCK_RE.search(html)

        captured = match.group(1)
        assert "<pre>" not in captured
        assert "<code>" not in captured
        assert captured == "graph TD"

    def test_findall_multiple_diagrams(self):
        """Test finding multiple Mermaid diagrams."""
        html = '''
        <pre><code class="language-mermaid">graph TD</code></pre>
        <p>Some text</p>
        <pre><code class="language-mermaid">flowchart LR</code></pre>
        '''
        matches = MERMAID_CODE_BLOCK_RE.findall(html)

        assert len(matches) == 2
        assert "graph TD" in matches[0]
        assert "flowchart LR" in matches[1]


class TestChartJSRegex:
    """Test Chart.js code block regex pattern."""

    def test_matches_basic_chartjs_block(self):
        """Test matching basic Chart.js code block."""
        html = '<pre><code class="language-chartjs">{"type": "bar"}</code></pre>'
        match = CHARTJS_CODE_BLOCK_RE.search(html)

        assert match is not None
        assert '{"type": "bar"}' in match.group(1)

    def test_matches_complete_chart_config(self):
        """Test matching complete Chart.js configuration."""
        config = '''{
  "type": "bar",
  "data": {
    "labels": ["A", "B"],
    "datasets": [{
      "data": [1, 2]
    }]
  }
}'''
        html = f'<pre><code class="language-chartjs">{config}</code></pre>'
        match = CHARTJS_CODE_BLOCK_RE.search(html)

        assert match is not None
        content = match.group(1)
        assert '"type": "bar"' in content
        assert '"labels"' in content
        assert '"datasets"' in content

    def test_matches_with_escaped_quotes(self):
        """Test matching config with quotes in strings."""
        html = '<pre><code class="language-chartjs">{"title": "Bob\'s Chart"}</code></pre>'
        match = CHARTJS_CODE_BLOCK_RE.search(html)

        assert match is not None

    def test_matches_line_chart(self):
        """Test matching line chart configuration."""
        html = '<pre><code class="language-chartjs">{"type": "line", "data": {}}</code></pre>'
        match = CHARTJS_CODE_BLOCK_RE.search(html)

        assert match is not None
        assert '"type": "line"' in match.group(1)

    def test_matches_pie_chart(self):
        """Test matching pie chart configuration."""
        html = '<pre><code class="language-chartjs">{"type": "pie", "data": {}}</code></pre>'
        match = CHARTJS_CODE_BLOCK_RE.search(html)

        assert match is not None
        assert '"type": "pie"' in match.group(1)

    def test_does_not_match_wrong_language(self):
        """Test that non-chartjs code blocks don't match."""
        html = '<pre><code class="language-json">{"type": "bar"}</code></pre>'
        match = CHARTJS_CODE_BLOCK_RE.search(html)

        assert match is None

    def test_captures_content_only(self):
        """Test that only JSON content is captured."""
        html = '<pre><code class="language-chartjs">{"test": true}</code></pre>'
        match = CHARTJS_CODE_BLOCK_RE.search(html)

        captured = match.group(1)
        assert "<pre>" not in captured
        assert "<code>" not in captured
        assert captured == '{"test": true}'

    def test_findall_multiple_charts(self):
        """Test finding multiple Chart.js blocks."""
        html = '''
        <pre><code class="language-chartjs">{"type": "bar"}</code></pre>
        <p>Text</p>
        <pre><code class="language-chartjs">{"type": "line"}</code></pre>
        '''
        matches = CHARTJS_CODE_BLOCK_RE.findall(html)

        assert len(matches) == 2
        assert '"type": "bar"' in matches[0]
        assert '"type": "line"' in matches[1]

    def test_matches_with_newlines_in_json(self):
        """Test matching JSON with newlines."""
        html = '''<pre><code class="language-chartjs">{
  "type": "bar"
}</code></pre>'''
        match = CHARTJS_CODE_BLOCK_RE.search(html)

        assert match is not None
        content = match.group(1)
        assert "\n" in content
        assert '"type": "bar"' in content


class TestRegexFlags:
    """Test regex flags and behavior."""

    def test_mermaid_dotall_flag(self):
        """Test that Mermaid regex has DOTALL flag (matches newlines)."""
        assert MERMAID_CODE_BLOCK_RE.flags & re.DOTALL

    def test_chartjs_dotall_flag(self):
        """Test that Chart.js regex has DOTALL flag."""
        assert CHARTJS_CODE_BLOCK_RE.flags & re.DOTALL

    def test_mermaid_matches_across_newlines(self):
        """Test that Mermaid regex matches content spanning multiple lines."""
        html = '''<pre><code class="language-mermaid">line1
line2
line3</code></pre>'''
        match = MERMAID_CODE_BLOCK_RE.search(html)

        assert match is not None
        content = match.group(1)
        assert "line1" in content
        assert "line2" in content
        assert "line3" in content

    def test_chartjs_matches_across_newlines(self):
        """Test that Chart.js regex matches content spanning multiple lines."""
        html = '''<pre><code class="language-chartjs">{
"key1": "value1",
"key2": "value2"
}</code></pre>'''
        match = CHARTJS_CODE_BLOCK_RE.search(html)

        assert match is not None
        content = match.group(1)
        assert "key1" in content
        assert "key2" in content


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_mermaid_empty_block(self):
        """Test matching empty Mermaid block."""
        html = '<pre><code class="language-mermaid"></code></pre>'
        match = MERMAID_CODE_BLOCK_RE.search(html)

        assert match is not None
        assert match.group(1) == ""

    def test_chartjs_empty_block(self):
        """Test matching empty Chart.js block."""
        html = '<pre><code class="language-chartjs"></code></pre>'
        match = CHARTJS_CODE_BLOCK_RE.search(html)

        assert match is not None
        assert match.group(1) == ""

    def test_mixed_code_blocks(self):
        """Test HTML with both Mermaid and Chart.js blocks."""
        html = '''
        <pre><code class="language-mermaid">graph TD</code></pre>
        <pre><code class="language-chartjs">{"type": "bar"}</code></pre>
        '''

        mermaid_matches = MERMAID_CODE_BLOCK_RE.findall(html)
        chartjs_matches = CHARTJS_CODE_BLOCK_RE.findall(html)

        assert len(mermaid_matches) == 1
        assert len(chartjs_matches) == 1
        assert "graph TD" in mermaid_matches[0]
        assert "bar" in chartjs_matches[0]

    def test_nested_braces_in_chartjs(self):
        """Test Chart.js config with nested braces."""
        html = '''<pre><code class="language-chartjs">{
  "options": {
    "plugins": {
      "legend": {"display": true}
    }
  }
}</code></pre>'''
        match = CHARTJS_CODE_BLOCK_RE.search(html)

        assert match is not None
        content = match.group(1)
        assert '"plugins"' in content
        assert '"legend"' in content

    def test_special_characters_in_mermaid(self):
        """Test Mermaid with special characters."""
        html = '<pre><code class="language-mermaid">A["Node with [brackets]"]</code></pre>'
        match = MERMAID_CODE_BLOCK_RE.search(html)

        assert match is not None
        assert "brackets" in match.group(1)
