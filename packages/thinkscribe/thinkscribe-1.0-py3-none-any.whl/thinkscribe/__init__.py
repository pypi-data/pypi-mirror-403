"""Report generation module with behavior customization."""

from .generator import generate_report
from .markdown_llm import generate_quick_insights
from .report_config import (
    Audience,
    FocusArea,
    Preset,
    ReportConfig,
    Style,
    Tone,
)

__all__ = [
    # Main functions
    "generate_report",
    "generate_quick_insights",
    # Configuration classes
    "ReportConfig",
    # Enums for type-safe configuration
    "Audience",
    "Style",
    "Tone",
    "FocusArea",
    "Preset",
]
