#!/usr/bin/env python3
"""Generate the OG share image for the git-100k-merges article.

Output: public/article/git-100k-merges/og.png (1200x630)

How it works: this script renders an SVG layout and rasterizes it with
headless Chrome (macOS system Chrome is required as an external tool;
no Python package dependencies). Japanese text uses system fonts
(Hiragino Sans on macOS); no CDN/web fonts are used.

Usage: python3 tools/gen_og_image.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public/article/git-100k-merges/og.png"
W, H = 1200, 630

INK = "#22293a"      # same ink as favicon.svg / body text
ACCENT = "#2337ff"   # site accent
GRAY = "#60739f"     # rgb(var(--gray))
FAINT = "#e5e9f0"    # rgb(var(--gray-light))

FONT = "'Hiragino Sans','Hiragino Kaku Gothic ProN',sans-serif"

SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="#ffffff"/>
  <rect x="0" y="0" width="{W}" height="8" fill="{ACCENT}"/>

  <!-- brand row -->
  <rect x="72" y="54" width="40" height="40" rx="8" fill="{INK}"/>
  <text x="92" y="82" text-anchor="middle" font-family="system-ui,sans-serif"
        font-size="17" font-weight="700" fill="#ffffff">FL</text>
  <text x="126" y="82" font-family="{FONT}" font-size="30" font-weight="700"
        fill="{INK}" letter-spacing="0.5">Fulltrust Lab</text>

  <rect x="948" y="60" width="180" height="34" rx="17" fill="none"
        stroke="{GRAY}" stroke-width="1.5"/>
  <text x="1038" y="82" text-anchor="middle" font-family="system-ui,sans-serif"
        font-size="17" font-weight="600" fill="{GRAY}"
        letter-spacing="2">EXPERIMENT 001</text>

  <!-- main copy -->
  <text x="72" y="296" font-family="{FONT}" font-size="76" font-weight="800"
        fill="{INK}">Gitは1日3万mergeに</text>
  <text x="72" y="400" font-family="{FONT}" font-size="76" font-weight="800"
        fill="{INK}">耐えられるのか？</text>

  <!-- divider -->
  <rect x="72" y="452" width="640" height="2" fill="{FAINT}"/>

  <!-- stats -->
  <text x="72" y="540" font-family="system-ui,sans-serif" font-size="46"
        font-weight="800" fill="{ACCENT}">100,000</text>
  <text x="72" y="572" font-family="system-ui,sans-serif" font-size="17"
        font-weight="600" fill="{GRAY}" letter-spacing="3">MERGES TESTED</text>

  <text x="352" y="540" font-family="system-ui,sans-serif" font-size="46"
        font-weight="800" fill="{INK}">59.3<tspan font-size="26"
        fill="{GRAY}"> ms</tspan></text>
  <text x="352" y="572" font-family="system-ui,sans-serif" font-size="17"
        font-weight="600" fill="{GRAY}" letter-spacing="3">MERGE MEDIAN</text>

  <!-- note -->
  <text x="1128" y="596" text-anchor="end" font-family="{FONT}" font-size="22"
        fill="{GRAY}">小規模・逐次実行で検証</text>
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
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rasterize(SVG, OUT)
    size_kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT.relative_to(ROOT)} ({W}x{H}, {size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
