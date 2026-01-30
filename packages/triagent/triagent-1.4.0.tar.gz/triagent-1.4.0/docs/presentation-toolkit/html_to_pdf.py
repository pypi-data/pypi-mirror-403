#!/usr/bin/env python3
"""
Capture screenshots of HTML presentation slides and generate PDF.

Usage:
    python docs/presentation-toolkit/html_to_pdf.py [--input FILE] [--output FILE]

Dependencies:
    pip install playwright Pillow
    playwright install chromium
"""

import argparse
import os
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright


def capture_slides_to_pdf(
    input_html: str, output_pdf: str, width: int = 1920, height: int = 1080
):
    """Capture all slides and save as PDF."""

    # Resolve absolute path for file:// URL
    input_path = Path(input_html).resolve()
    file_url = f"file://{input_path}"

    screenshots = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": height})

        # Navigate to presentation
        page.goto(file_url)
        page.wait_for_load_state("networkidle")

        # Get total slides from JavaScript
        total_slides = page.evaluate("() => totalSlides")
        print(f"Capturing {total_slides} slides...")

        # Slides with animations that need extra time to load
        animated_slides = {11: 5000}  # slide_number: extra_wait_ms

        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(1, total_slides + 1):
                # Extra wait for slides with animations
                if i in animated_slides:
                    extra_wait = animated_slides[i]
                    print(f"  Waiting {extra_wait/1000}s for slide {i} animations...")
                    page.wait_for_timeout(extra_wait)

                # Take screenshot
                screenshot_path = os.path.join(tmpdir, f"slide_{i:02d}.png")
                page.screenshot(path=screenshot_path, full_page=False)
                screenshots.append(screenshot_path)
                print(f"  Captured slide {i}/{total_slides}")

                # Advance to next slide
                if i < total_slides:
                    page.keyboard.press("ArrowRight")
                    page.wait_for_timeout(600)  # Wait for transition

            browser.close()

            # Convert PNGs to PDF
            images = [Image.open(s).convert("RGB") for s in screenshots]
            images[0].save(output_pdf, save_all=True, append_images=images[1:])
            print(f"\nPDF saved: {output_pdf}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert HTML presentation to PDF")
    parser.add_argument(
        "--input",
        "-i",
        default="triagent-executive-demo.html",
        help="Input HTML file (default: triagent-executive-demo.html)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="triagent-executive-demo.pdf",
        help="Output PDF file (default: triagent-executive-demo.pdf)",
    )
    parser.add_argument(
        "--width", "-w", type=int, default=1920, help="Viewport width"
    )
    parser.add_argument(
        "--height", "-H", type=int, default=1080, help="Viewport height"
    )

    args = parser.parse_args()
    capture_slides_to_pdf(args.input, args.output, args.width, args.height)
