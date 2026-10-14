#!/usr/bin/env python3
"""Generate the site-wide default OG share image for Fulltrust Lab.

Output: public/og.png (1200x630)

The horizontal brand logo (public/brand/fulltrust-lab-logo.svg) is inlined
into the layout, so replacing that file is enough to swap the logo.
Rasterization uses headless Chrome (macOS system Chrome required; no Python
package dependencies). Japanese text uses system fonts (Hiragino Sans on
macOS); no CDN/web fonts are used.

Usage: python3 tools/gen_site_og_image.py
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "public/brand/fulltrust-lab-logo.svg"
OUT = ROOT / "public/og.png"
W, H = 1200, 630

INK = "#22293a"      # site ink / favicon
ACCENT = "#2337ff"   # site accent
GRAY = "#60739f"     # rgb(var(--gray))

FONT = "'Hiragino Sans','Hiragino Kaku Gothic ProN',sans-serif"


def logo_inner() -> str:
    """Return the inner elements of the brand logo SVG (for inlining)."""
    text = LOGO.read_text(encoding="utf-8")
    m = re.search(r"<svg[^>]*>(.*)</svg>", text, re.S)
    if not m:
        sys.exit(f"could not parse {LOGO}")
    return m.group(1)


def build_svg() -> str:
    inner = logo_inner()
    # logo viewBox is 720x160; scale to 660px wide -> scale = 660/720
    logo_w = 660
    logo_h = logo_w * 160 / 720
    lx = (W - logo_w) / 2
    ly = 190
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="#ffffff"/>
  <rect x="0" y="0" width="{W}" height="8" fill="{ACCENT}"/>

  <g transform="translate({lx} {ly}) scale({logo_w / 720})">{inner}</g>

  <text x="{W / 2}" y="480" text-anchor="middle" font-family="{FONT}"
        font-size="36" font-weight="600" fill="{INK}">技術を実際に試して検証するラボ</text>

  <text x="{W / 2}" y="556" text-anchor="middle"
        font-family="system-ui,sans-serif" font-size="22" font-weight="600"
        fill="{GRAY}" letter-spacing="2">lab.fulltrust.co.jp</text>
</svg>
"""


def rasterize(svg: str, out: Path) -> None:
    chrome = shutil.which("Google Chrome") or next(
        (
            p
            for p in (
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium",
            )
            if Path(p).exists()
        ),
        None,
    )
    if not chrome:
        sys.exit("headless Chrome not found; required to rasterize the SVG")
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "og.svg"
        src.write_text(svg, encoding="utf-8")
        subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                f"--window-size={W},{H}",
                f"--screenshot={out}",
                f"file://{src}",
            ],
            check=True,
            capture_output=True,
        )


def main() -> None:
    rasterize(build_svg(), OUT)
    size_kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT.relative_to(ROOT)} ({W}x{H}, {size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
