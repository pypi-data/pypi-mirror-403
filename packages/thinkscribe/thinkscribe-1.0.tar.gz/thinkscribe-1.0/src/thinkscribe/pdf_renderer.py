"""HTML to PDF conversion using Playwright."""

import logging
import subprocess
import sys
from pathlib import Path

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

_browser_installed: bool | None = None


def _ensure_chromium_installed() -> None:
    """Check if Chromium is installed, and install it if missing."""
    global _browser_installed

    if _browser_installed:
        return

    # Check if chromium is already installed by looking for the browser
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        _browser_installed = True
        return
    except Exception:
        pass

    # Chromium not found, install it
    logger.info("Chromium not found. Installing automatically (this may take a moment)...")
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
        )
        _browser_installed = True
        logger.info("Chromium installed successfully.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to install Chromium. Please run manually: playwright install chromium\n"
            f"Error: {e.stderr.decode() if e.stderr else str(e)}"
        ) from e


async def html_to_pdf_with_playwright(html_path: Path, pdf_path: Path) -> None:
    """Use Playwright (Chromium) to convert an HTML file to PDF."""
    _ensure_chromium_installed()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Load local HTML file
        await page.goto(f"file://{html_path.resolve()}", wait_until="networkidle")

        # Wait for charts to render (Mermaid and Chart.js)
        await page.wait_for_timeout(1000)

        # Generate PDF
        await page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            margin={"top": "15mm", "bottom": "15mm", "left": "12mm", "right": "12mm"},
        )

        await browser.close()
