# thinkscribe

Transform your thoughts into beautiful visual reports — give us abstract text, we create meaning with charts and diagrams.

## 📚 Documentation

- **[Complete Guide](docs/COMPLETE_GUIDE.md)** - Comprehensive documentation with all functions, use cases, and examples
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - One-page cheat sheet for common tasks
- **[Custom Prompts Guide](docs/CUSTOM_PROMPTS_GUIDE.md)** - Create custom prompt templates for reports and insights
- **[Anti-Hallucination Guide](docs/PREVENTING_HALLUCINATION.md)** - Ensure data fidelity in reports
- **[Packaging Guide](PACKAGING_GUIDE.md)** - Build and distribute the package

## Features

- 📊 **Automatic Visualizations**: Generates Chart.js charts and Mermaid diagrams from your data
- 🤖 **Multi-LLM Support**: Works with Ollama (local/free), OpenAI, and Azure OpenAI
- 🎯 **Behavior Customization**: Tailor reports for different audiences (executives, technical, analysts)
- 📄 **PDF Generation**: High-quality PDF output via Playwright (auto-installs Chromium on first use)
- ⚡ **Quick Insights**: Fast summary generation for immediate feedback
- 🎨 **Professional Styling**: Clean, modern report layouts
- 🔧 **Flexible Configuration**: Presets, custom templates, or full programmatic control

## Installation

### 1. Install the package

```bash
pip install thinkscribe
```

For development installation:

```bash
git clone https://github.com/yourusername/thinkscribe.git
cd thinkscribe
pip install -e .
```

### 2. Set up an LLM Provider

> **Note:** Playwright's Chromium browser is automatically installed on first PDF generation. No manual setup required!

Choose one of the following:

**Option A: Ollama (Free, runs locally)**

```bash
# Install from https://ollama.ai
ollama pull gpt-oss:20b  # or your preferred model
ollama serve
```

**Option B: OpenAI**

```bash
# Get API key from https://platform.openai.com
export REPORT_LLM_PROVIDER=openai
export REPORT_LLM_API_KEY=sk-proj-your-key-here
export REPORT_LLM_MODEL=gpt-4-turbo-preview
```

**Option C: Azure OpenAI**

```bash
# Get credentials from Azure portal
export REPORT_LLM_PROVIDER=azure
export REPORT_LLM_BASE_URL=https://your-resource.openai.azure.com
export REPORT_LLM_MODEL=your-deployment-name
export REPORT_LLM_API_KEY=your-azure-key
```

**Option D: OpenAI-Compatible Providers (Groq, Together AI, Mistral, etc.)**

Any provider with an OpenAI-compatible API works out of the box. Just set `openai` as the provider and point to your provider's base URL:

```bash
# Groq Cloud
export REPORT_LLM_PROVIDER=openai
export REPORT_LLM_BASE_URL=https://api.groq.com/openai/v1
export REPORT_LLM_MODEL=llama-3.3-70b-versatile
export REPORT_LLM_API_KEY=gsk_your-groq-key

# Together AI
export REPORT_LLM_PROVIDER=openai
export REPORT_LLM_BASE_URL=https://api.together.xyz/v1
export REPORT_LLM_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo
export REPORT_LLM_API_KEY=your-together-key

# Mistral AI
export REPORT_LLM_PROVIDER=openai
export REPORT_LLM_BASE_URL=https://api.mistral.ai/v1
export REPORT_LLM_MODEL=mistral-large-latest
export REPORT_LLM_API_KEY=your-mistral-key

# OpenRouter
export REPORT_LLM_PROVIDER=openai
export REPORT_LLM_BASE_URL=https://openrouter.ai/api/v1
export REPORT_LLM_MODEL=anthropic/claude-3.5-sonnet
export REPORT_LLM_API_KEY=your-openrouter-key
```

## Quick Start

```python
from thinkscribe import generate_report, generate_quick_insights

# Your data (can be dict, list, string, or any JSON-serializable object)
data = {
    "sales": [
        {"name": "Alice", "revenue": 50000},
        {"name": "Bob", "revenue": 75000},
        {"name": "Charlie", "revenue": 62000}
    ]
}

# Generate quick insights (fast, 3-5 bullet points)
insights = generate_quick_insights(
    data=data,
    question="Who are the top performers?"
)
print(insights)

# Generate full PDF report
pdf_path = generate_report(
    data=data,
    question="Analyze sales performance and provide recommendations",
    output_path="sales_report.pdf"  # Optional, auto-generates if not provided
)

print(f"Report generated: {pdf_path}")
```

## Behavior Customization 🎯

**NEW**: Customize report output for different audiences, styles, and purposes without writing prompts!

### Quick Start with Presets

Use pre-configured templates for common scenarios:

```python
from thinkscribe import generate_report

# Executive summary - concise, high-level, business-focused
pdf_path = generate_report(
    data=sales_data,
    question="Q4 performance analysis",
    preset="executive_summary"
)

# Technical deep dive - detailed, implementation-focused
pdf_path = generate_report(
    data=system_metrics,
    question="System performance analysis",
    preset="technical_deep_dive"
)

# Data analysis - statistical, methodology-focused
pdf_path = generate_report(
    data=experiment_results,
    question="A/B test results",
    preset="data_analysis"
)
```

**Available Presets:**

- `executive_summary` - High-level business summary for C-suite
- `technical_deep_dive` - Detailed technical analysis for engineers
- `data_analysis` - Statistical analysis for data scientists
- `sales_presentation` - Persuasive report for sales/marketing
- `quick_overview` - Fast, scannable summary for general audience

### Fine-Grained Control

Customize individual aspects:

```python
# Customize audience, style, and tone
pdf_path = generate_report(
    data=data,
    question="Analyze user engagement",
    audience="executives",      # executives|technical|analysts|general
    style="concise",            # concise|detailed|visual_heavy
    tone="formal",              # formal|persuasive|casual
    focus=["metrics", "recommendations"]  # What to emphasize
)
```

### Using ReportConfig (Advanced)

For maximum control and type safety:

```python
from thinkscribe import (
    generate_report,
    ReportConfig,
    Audience,
    Style,
    Tone,
    FocusArea
)

# Build custom configuration
config = ReportConfig(
    audience=Audience.TECHNICAL,
    style=Style.DETAILED,
    tone=Tone.FORMAL,
    focus=[FocusArea.INSIGHTS, FocusArea.TRENDS]
)

pdf_path = generate_report(
    data=data,
    question="System performance trends",
    config=config
)

# Or use a preset and override specific values
config = ReportConfig.from_preset(
    Preset.EXECUTIVE_SUMMARY,
    tone=Tone.PERSUASIVE  # Override the preset's tone
)
```

### Behavior Options Reference

#### Audiences

- **`executives`** - C-level focus: ROI, strategic implications, high-level recommendations
- **`technical`** - Engineering focus: implementation details, architecture, methodologies
- **`analysts`** - Data focus: statistical significance, methodology, data quality
- **`general`** - Accessible language, balanced depth, clear explanations

#### Styles

- **`concise`** - 1-2 pages, bullet points, key highlights only
- **`detailed`** - 3-5 pages, comprehensive analysis with context
- **`visual_heavy`** - Chart-first approach, minimal text, infographic style

#### Tones

- **`formal`** - Professional, objective, academic language
- **`persuasive`** - Action-oriented, compelling, results-focused
- **`casual`** - Friendly, conversational, accessible

#### Focus Areas

- **`metrics`** - Prioritize quantitative data and KPIs
- **`recommendations`** - Emphasize actionable next steps
- **`trends`** - Focus on patterns and future projections
- **`comparisons`** - Highlight comparative analysis
- **`insights`** - Uncover hidden patterns and surprises

### Custom Templates (Expert)

Create your own prompt templates for complete control over report generation.

**See the [Custom Prompts Guide](docs/CUSTOM_PROMPTS_GUIDE.md) for complete documentation.**

```python
from pathlib import Path

# Option 1: Custom YAML template file (recommended)
config = ReportConfig(
    template_file=Path("./my_templates.yaml"),
    template_name="MY_CUSTOM_TEMPLATE"
)

pdf_path = generate_report(data, question="...", config=config)

# Option 2: Inline custom prompt (quick experiments)
custom_prompt = """
Create a report focusing on {question}.
Data: {answer}
Make it extremely concise with only bullet points.
"""

config = ReportConfig(custom_prompt=custom_prompt)
pdf_path = generate_report(data, question="...", config=config)
```

**Examples:**

- See `examples/07_custom_prompts.py` for working examples
- See `examples/custom_templates.yaml` for template file structure

## Configuration

### LLM Provider Setup

thinkscribe supports multiple LLM providers: **Ollama** (local), **OpenAI**, and **Azure OpenAI**.

#### Option 1: Ollama (Default - Free & Local)

```bash
# Using Ollama (default configuration)
REPORT_LLM_PROVIDER=ollama
REPORT_LLM_BASE_URL=http://localhost:11434
REPORT_LLM_MODEL=gpt-oss:20b
REPORT_LLM_TEMPERATURE=0.3
REPORT_LLM_MAX_TOKENS=4096

# PDF Configuration
REPORT_PDF_OUTPUT_DIR=reports
```

**Setup Ollama:**

```bash
# Install Ollama from https://ollama.ai
ollama pull gpt-oss:20b  # or any other model
ollama serve
```

#### Option 2: OpenAI

```bash
# Using OpenAI
REPORT_LLM_PROVIDER=openai
REPORT_LLM_BASE_URL=https://api.openai.com  # Optional, this is the default
REPORT_LLM_MODEL=gpt-4-turbo-preview
REPORT_LLM_API_KEY=sk-proj-your-api-key-here
REPORT_LLM_TEMPERATURE=0.3
REPORT_LLM_MAX_TOKENS=4096

# PDF Configuration
REPORT_PDF_OUTPUT_DIR=reports
```

#### Option 3: Azure OpenAI

```bash
# Using Azure OpenAI
REPORT_LLM_PROVIDER=azure
REPORT_LLM_BASE_URL=https://your-resource.openai.azure.com
REPORT_LLM_MODEL=your-deployment-name
REPORT_LLM_API_KEY=your-azure-api-key
REPORT_LLM_TEMPERATURE=0.3
REPORT_LLM_MAX_TOKENS=4096

# PDF Configuration
REPORT_PDF_OUTPUT_DIR=reports
```

#### Option 4: OpenAI-Compatible Providers

Any provider with an OpenAI-compatible API (Groq, Together AI, Mistral, OpenRouter, etc.) works by setting `openai` as the provider with a custom base URL:

```bash
# Example: Groq Cloud
REPORT_LLM_PROVIDER=openai
REPORT_LLM_BASE_URL=https://api.groq.com/openai/v1
REPORT_LLM_MODEL=llama-3.3-70b-versatile
REPORT_LLM_API_KEY=gsk_your-groq-key
REPORT_LLM_TEMPERATURE=0.3
REPORT_LLM_MAX_TOKENS=4096
```

### Programmatic Configuration

You can also configure settings in code:

```python
from thinkscribe.config import settings

# Configure for OpenAI
settings.llm_provider = "openai"
settings.llm_model = "gpt-4-turbo-preview"
settings.llm_api_key = "sk-proj-..."

# Or for Ollama
settings.llm_provider = "ollama"
settings.llm_model = "llama2:13b"
settings.llm_temperature = 0.5
```

### Legacy Configuration (Deprecated)

Old `REPORT_OLLAMA_*` settings still work but will show deprecation warnings:

```bash
# DEPRECATED - still works but use REPORT_LLM_* instead
REPORT_OLLAMA_HOST=http://localhost:11434
REPORT_OLLAMA_MODEL=gpt-oss:20b
```

The system will automatically migrate these to the new settings.

## API Reference

### `generate_report()`

Generate a complete PDF report with visualizations and behavior customization.

```python
def generate_report(
    data: Any,
    output_path: str | Path | None = None,
    question: str | None = None,
    charts: list | None = None,
    # Behavior customization (NEW)
    config: ReportConfig | None = None,
    audience: str | None = None,
    style: str | None = None,
    tone: str | None = None,
    focus: list[str] | None = None,
    preset: str | None = None,
) -> str:
    """
    Args:
        data: Input data (text, dict, list, JSON, etc.)
        output_path: Output PDF path (auto-generated if None)
        question: User's question to guide report generation
        charts: Deprecated (LLM generates visualizations automatically)

        # Behavior Customization
        config: ReportConfig object for complete control
        audience: Target audience (executives|technical|analysts|general)
        style: Report style (concise|detailed|visual_heavy)
        tone: Report tone (formal|persuasive|casual)
        focus: List of focus areas (metrics, recommendations, trends, etc.)
        preset: Use preset config (executive_summary, technical_deep_dive, etc.)

    Returns:
        Path to generated PDF file
    """
```

**Examples:**

```python
# Basic usage
pdf_path = generate_report(
    data={"temperature": [20, 22, 25, 23, 21]},
    question="Analyze temperature trends this week"
)

# With behavior customization
pdf_path = generate_report(
    data=sales_data,
    question="Q4 analysis",
    audience="executives",
    style="concise",
    tone="formal"
)

# Using a preset
pdf_path = generate_report(
    data=data,
    question="System performance",
    preset="technical_deep_dive"
)
```

### `generate_quick_insights()`

Generate quick bullet-point insights (fast, 3-5 seconds).

```python
def generate_quick_insights(
    data: Any,
    question: str | None = None,
) -> str:
    """
    Args:
        data: Input data (text, dict, list, JSON, etc.)
        question: User's question

    Returns:
        String with 3-5 bullet point insights
    """
```

**Example:**

```python
insights = generate_quick_insights(
    data=user_feedback_data,
    question="What are the main themes in user feedback?"
)
```

## Report Features

The generated reports automatically include:

### 📊 Visualizations

The LLM intelligently chooses appropriate visualizations:

- **Chart.js Charts**: Bar charts, line charts, pie charts, radar charts
- **Mermaid Diagrams**: Flowcharts, process diagrams, relationships

### 📝 Report Structure

1. **Title & Summary**: Clear overview with key findings
2. **Visualizations**: Automatically generated charts and diagrams
3. **Detailed Analysis**: In-depth breakdown of the data
4. **Tables**: Raw data presented in clean tables
5. **Recommendations**: Actionable insights

### 🎨 Styling

- Professional typography and spacing
- Color-coded sections and headers
- Responsive chart sizing
- Page break optimization

## Advanced Usage

### Custom Output Directory

```python
from pathlib import Path

output_dir = Path("./monthly_reports")
output_dir.mkdir(exist_ok=True)

pdf_path = generate_report(
    data=monthly_data,
    output_path=output_dir / "january_2024.pdf",
    question="Monthly performance summary"
)
```

### Batch Report Generation

```python
datasets = {
    "Q1": q1_data,
    "Q2": q2_data,
    "Q3": q3_data,
    "Q4": q4_data,
}

for quarter, data in datasets.items():
    pdf_path = generate_report(
        data=data,
        question=f"Analyze {quarter} performance",
        output_path=f"reports/{quarter}_report.pdf"
    )
    print(f"Generated {quarter}: {pdf_path}")
```

## Real-World Use Cases

### Board Meeting Executive Summary

```python
# Generate high-level summary for board presentation
pdf_path = generate_report(
    data=company_metrics,
    question="Q4 2024 company performance and 2025 outlook",
    preset="executive_summary"
)
```

### Engineering Incident Report

```python
# Detailed technical postmortem
pdf_path = generate_report(
    data=incident_logs,
    question="Database outage root cause analysis",
    audience="technical",
    style="detailed",
    focus=["insights", "recommendations"]
)
```

### A/B Test Results for Data Team

```python
# Statistical analysis with methodology
pdf_path = generate_report(
    data=ab_test_results,
    question="Checkout flow A/B test analysis",
    preset="data_analysis"
)
```

### Sales Proposal

```python
# Persuasive presentation with visuals
pdf_path = generate_report(
    data=roi_analysis,
    question="ROI projection for enterprise plan",
    audience="general",
    style="visual_heavy",
    tone="persuasive",
    focus=["metrics", "recommendations"]
)
```

## Requirements

- Python >= 3.10
- **LLM Provider** (choose one):
  - Ollama (free, local) - [Download](https://ollama.ai)
  - OpenAI API key - [Get Key](https://platform.openai.com)
  - Azure OpenAI credentials
- Dependencies (auto-installed):
  - markdown
  - requests
  - pyyaml
  - playwright
  - pydantic >= 2.0
  - pydantic-settings

## Project Structure

```
thinkscribe/
├── generator.py          # Main orchestration
├── config/               # Configuration management
├── markdown_llm.py       # LLM integration
├── html_renderer.py      # Markdown → HTML conversion
├── pdf_renderer.py       # HTML → PDF conversion
├── prompts.py            # Prompt template management
├── styles.py             # CSS styling
├── serializers.py        # Data serialization
├── regex.py              # Pattern matching
└── utils/                # Utility functions
```

## Troubleshooting

### LLM Provider Issues

**Ollama Connection Errors**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama (if not running)
ollama serve

# Check environment
echo $REPORT_LLM_PROVIDER  # should be "ollama" or empty
```

**OpenAI API Errors**

```bash
# Verify API key is set
echo $REPORT_LLM_API_KEY

# Test API connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $REPORT_LLM_API_KEY"
```

**Azure OpenAI Errors**

```bash
# Verify all Azure settings
echo $REPORT_LLM_PROVIDER  # should be "azure"
echo $REPORT_LLM_BASE_URL
echo $REPORT_LLM_MODEL
echo $REPORT_LLM_API_KEY
```

**Provider Configuration**

```python
# Check current provider in Python
from thinkscribe.config import settings
print(f"Provider: {settings.llm_provider}")
print(f"Model: {settings.llm_model}")
print(f"Base URL: {settings.llm_base_url}")
```

### Playwright Errors

Chromium is automatically installed on first PDF generation. If auto-installation fails:

```bash
# Manually install Chromium
playwright install chromium

# Or force reinstall
playwright install --force chromium

# Check Playwright installation
playwright --version
```

### Import Errors

```bash
# Reinstall package
pip install --force-reinstall thinkscribe

# Or for development mode
pip install -e .
```

## License

MIT

## Contributing

Contributions welcome! Please feel free to submit issues and pull requests.
