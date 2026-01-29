"""Regular expressions for code block detection."""

import re

# Regex for converting code blocks
MERMAID_CODE_BLOCK_RE = re.compile(
    r'<pre><code class="language-mermaid">(.*?)</code></pre>',
    re.DOTALL,
)
CHARTJS_CODE_BLOCK_RE = re.compile(
    r'<pre><code class="language-chartjs">(.*?)</code></pre>',
    re.DOTALL,
)
