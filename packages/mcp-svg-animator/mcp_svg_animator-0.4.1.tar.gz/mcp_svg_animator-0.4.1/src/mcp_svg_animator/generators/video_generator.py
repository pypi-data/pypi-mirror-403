"""Generate video files from SVG animations using Playwright."""

from playwright.sync_api import sync_playwright


def create_video_from_svg(
    svg_content: str,
    output_path: str,
    duration_ms: int = 3000,
    width: int | None = None,
    height: int | None = None,
) -> None:
    """Create a video file from an SVG animation.

    Uses Playwright to render the SVG in a headless browser and record it.

    Args:
        svg_content: The SVG content as a string.
        output_path: Path where the video file will be saved (.webm format).
        duration_ms: Duration of the video in milliseconds.
        width: Video width (defaults to SVG width or 800).
        height: Video height (defaults to SVG height or 600).
    """
    # Parse SVG dimensions if not provided
    if width is None:
        width = _extract_dimension(svg_content, "width") or 800
    if height is None:
        height = _extract_dimension(svg_content, "height") or 600

    # Create HTML page with the SVG
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
        context = browser.new_context(
            viewport={"width": width, "height": height},
            record_video_dir=".",
            record_video_size={"width": width, "height": height},
        )

        page = context.new_page()
        page.set_content(html_content)

        # Wait for the animation duration
        page.wait_for_timeout(duration_ms)

        # Close context to finalize video
        context.close()
        browser.close()

        # Move video to output path
        video = page.video
        if video:
            video_path = video.path()
            if video_path:
                import shutil
                shutil.move(video_path, output_path)


def _extract_dimension(svg_content: str, attr: str) -> int | None:
    """Extract a dimension attribute from SVG content."""
    import re

    pattern = rf'{attr}=["\'](\d+)'
    match = re.search(pattern, svg_content)
    if match:
        return int(match.group(1))
    return None
