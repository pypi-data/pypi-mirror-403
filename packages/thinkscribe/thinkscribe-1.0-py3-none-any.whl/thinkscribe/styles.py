"""CSS styles loading."""

from pathlib import Path

# Path to styles
_STYLES_PATH = Path(__file__).parent / "styles" / "styles.css"


def load_styles() -> str:
    """Load CSS styles from file."""
    if _STYLES_PATH.exists():
        return _STYLES_PATH.read_text()
    return ""
