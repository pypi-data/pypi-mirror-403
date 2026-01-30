"""Generate PNG files from SVG content using Playwright."""

from playwright.sync_api import sync_playwright


def create_png_from_svg(
    svg_content: str,
    output_path: str,
    width: int | None = None,
    height: int | None = None,
) -> None:
    """Create a PNG file from SVG content.

    Uses Playwright to render the SVG in a headless browser and take a screenshot.

    Args:
        svg_content: The SVG content as a string.
        output_path: Path where the PNG file will be saved.
        width: Image width (defaults to SVG width or 800).
        height: Image height (defaults to SVG height or 600).
    """
    if width is None:
        width = _extract_dimension(svg_content, "width") or 800
    if height is None:
        height = _extract_dimension(svg_content, "height") or 600

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            width: {width}px;
            height: {height}px;
            background: white;
        }}
        svg {{
            max-width: 100%;
            max-height: 100%;
        }}
    </style>
</head>
<body>
{svg_content}
</body>
</html>"""

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_content(html_content)
        page.screenshot(path=output_path, type="png")
        browser.close()


def _extract_dimension(svg_content: str, attr: str) -> int | None:
    """Extract a dimension attribute from SVG content."""
    import re

    pattern = rf'{attr}=["\'](\d+)'
    match = re.search(pattern, svg_content)
    if match:
        return int(match.group(1))
    return None
