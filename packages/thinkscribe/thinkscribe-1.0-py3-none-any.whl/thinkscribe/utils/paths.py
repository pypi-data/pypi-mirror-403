"""Path and directory management utilities."""

from pathlib import Path

from ..config.settings import settings


def ensure_output_dir() -> Path:
    """Ensure the output directory exists."""
    output_dir = Path(settings.pdf_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
