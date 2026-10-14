#!/usr/bin/env python3
"""Generate static SVG charts for the git-100k-merges article.

Reads raw experiment data only (never re-runs anything):
  tmp/git-merge-lab/results/benchmark.csv
  tmp/git-merge-lab/results/merge_times.csv
  tmp/git-merge-lab/results/post_gc_bench.json

Writes SVGs to public/article/git-100k-merges/.
Pure stdlib; deterministic output.
"""
import csv
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "tmp/git-merge-lab/results")
OUT = os.path.join(ROOT, "public/article/git-100k-merges")

W, H = 720, 400
ML, MR, MT, MB = 70, 16, 34, 48
PW, PH = W - ML - MR, H - MT - MB

COLORS = {
    "log": "#c0392b",
    "log_oneline": "#e67e22",
    "revlist_all": "#8e44ad",
    "fsck": "#2980b9",
    "status": "#27ae60",
    "branch": "#16a085",
    "merge_base": "#7f8c8d",
}

LABELS = {
    "log": "git log",
    "log_oneline": "git log --oneline",
    "revlist_all": "git rev-list --all --count",
    "fsck": "git fsck",
    "status": "git status",
    "branch": "git branch",
    "merge_base": "git merge-base",
}


def fmt_ms(ms):
    if ms >= 1000:
        return "%.0fs" % (ms / 1000.0)
    if ms >= 100:
        return "%.0fms" % ms
    if ms >= 10:
        return "%.0fms" % ms
    return "%.1fms" % ms


def load_benchmarks():
    rows = []
    with open(os.path.join(RESULTS, "benchmark.csv")) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def svg_open(title):
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
        'role="img" aria-label="%s" font-family="system-ui,-apple-system,sans-serif" '
        'font-size="12" fill="#222">'
        '<title>%s</title>'
        '<rect width="%d" height="%d" fill="#fff" stroke="#e5e7eb"/>'
        % (W, H, title, title, W, H)
    ]


def axes_log_y(xmin, xmax, ymin_log, ymax_log, xlabel, ylabel, xticks):
    """Return (parts, xfn, yfn) for linear-x / log10-y axes."""
    parts = []
    x0, x1 = ML, ML + PW
    y0, y1 = MT + PH, MT

    def xfn(v):
        return x0 + (v - xmin) / (xmax - xmin) * PW

    def yfn(v):
        lv = math.log10(max(v, 1e-9))
        return y0 - (lv - ymin_log) / (ymax_log - ymin_log) * PH

    for e in range(int(math.ceil(ymin_log)), int(math.floor(ymax_log)) + 1):
        v = 10 ** e
        y = yfn(v)
        parts.append(
            '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#e5e7eb"/>'
            % (x0, y, x1, y)
        )
        parts.append(
            '<text x="%.1f" y="%.1f" text-anchor="end" fill="#666">%s</text>'
            % (x0 - 6, y + 4, fmt_ms(v))
        )
    for v in xticks:
        x = xfn(v)
        parts.append(
            '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#ccc"/>'
            % (x, y0, x, y0 + 5)
        )
        lbl = "%dk" % (v // 1000) if v >= 1000 else str(v)
        parts.append(
            '<text x="%.1f" y="%.1f" text-anchor="middle" fill="#666">%s</text>'
            % (x, y0 + 18, lbl)
        )
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#999"/>' % (x0, y0, x1, y0))
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#999"/>' % (x0, y0, x0, y1))
    parts.append(
        '<text x="%.1f" y="%d" text-anchor="middle" fill="#333" font-size="13">%s</text>'
        % (x0 + PW / 2, H - 8, xlabel)
    )
    parts.append(
        '<text x="14" y="%.1f" text-anchor="middle" fill="#333" font-size="13" '
        'transform="rotate(-90 14 %.1f)">%s</text>' % (MT + PH / 2, MT + PH / 2, ylabel)
    )
    return parts, xfn, yfn


def series_line(points, color):
    d = " ".join(
        "%s %.1f,%.1f" % ("M" if i == 0 else "L", x, y)
        for i, (x, y) in enumerate(points)
    )
    return '<path d="%s" fill="none" stroke="%s" stroke-width="2"/>' % (d, color)


def dots(points, color, r=3):
    return "".join(
        '<circle cx="%.1f" cy="%.1f" r="%d" fill="%s"/>' % (x, y, r, color)
        for x, y in points
    )


def legend(items, x, y):
    parts = []
    for i, (label, color) in enumerate(items):
        yy = y + i * 18
        parts.append('<rect x="%d" y="%d" width="14" height="4" fill="%s"/>' % (x, yy + 4, color))
        parts.append('<text x="%d" y="%d" fill="#333">%s</text>' % (x + 20, yy + 9, label))
    return parts


def fig1_latency_vs_merges(rows):
    parts = svg_open("git operation latency vs merge count (log scale)")
    xticks = [0, 20000, 40000, 60000, 80000, 100000]
    ax, xfn, yfn = axes_log_y(
        0, 100000, math.log10(1), math.log10(400000), "merges", "latency (log scale)", xticks
    )
    parts += ax

    series = ["log", "log_oneline", "revlist_all", "fsck", "status", "branch", "merge_base"]
    for s in series:
        pts = []
        for r in rows:
            m = float(r["merges"])
            if s == "fsck":
                v = float(r["fsck_ms"])
            else:
                v = float(r["%s_median_ms" % s])
            pts.append((xfn(m), yfn(v)))
        parts.append(series_line(pts, COLORS[s]))
        parts.append(dots(pts, COLORS[s]))

    # Legend lives in the empty mid-right band of the plot: the top-left
    # collides with the rising fsck line and the top-right with log/rev-list.
    lx1, ly = int(ML + PW * 0.50), int(MT + PH * 0.42)
    lx2 = int(ML + PW * 0.76)
    col1 = series[:4]
    col2 = series[4:]
    parts += legend([(LABELS[s], COLORS[s]) for s in col1], lx1, ly)
    parts += legend([(LABELS[s], COLORS[s]) for s in col2], lx2, ly)
    parts.append(
        '<text x="%d" y="%d" text-anchor="middle" font-size="14" font-weight="700">'
        "Git operation latency vs merge history size (median of 5)</text>"
        % (W / 2, 18)
    )
    parts.append("</svg>")
    return "\n".join(parts)


def fig2_gc_before_after(rows, postgc):
    last = rows[-1]
    ops = [
        ("git log", float(last["log_median_ms"]), postgc["ops"]["log"]["median_ms"]),
        ("git log --oneline", float(last["log_oneline_median_ms"]), postgc["ops"]["log_oneline"]["median_ms"]),
        ("git rev-list --all --count", float(last["revlist_all_median_ms"]), postgc["ops"]["revlist_all"]["median_ms"]),
        ("git fsck", float(last["fsck_ms"]), postgc["fsck_ms"]),
    ]
    parts = svg_open("before vs after git gc (log scale)")
    xmin, xmax = 0, 100000
    ymin_log, ymax_log = math.log10(10), math.log10(400000)
    ax, xfn, yfn = axes_log_y(0, xmax, ymin_log, ymax_log, "", "latency (log scale)", [])
    parts += ax

    group_w = PW / len(ops)
    bw = 42
    for i, (name, before, after) in enumerate(ops):
        cx = ML + group_w * i + group_w / 2
        yb = yfn(before)
        ya = yfn(after)
        y0 = MT + PH
        parts.append(
            '<rect x="%.1f" y="%.1f" width="%d" height="%.1f" fill="#c0392b" opacity="0.85"/>'
            % (cx - bw - 3, yb, bw, y0 - yb)
        )
        parts.append(
            '<rect x="%.1f" y="%.1f" width="%d" height="%.1f" fill="#27ae60" opacity="0.85"/>'
            % (cx + 3, ya, bw, y0 - ya)
        )
        parts.append(
            '<text x="%.1f" y="%.1f" text-anchor="middle" font-size="11" fill="#c0392b">%s</text>'
            % (cx - bw / 2 - 3, yb - 5, fmt_ms(before))
        )
        parts.append(
            '<text x="%.1f" y="%.1f" text-anchor="middle" font-size="11" fill="#1e8449">%s</text>'
            % (cx + bw / 2 + 3, ya - 5, fmt_ms(after))
        )
        short = name.replace("git ", "").replace("--all --count", "--all")[:26]
        parts.append(
            '<text x="%.1f" y="%d" text-anchor="middle" fill="#333">%s</text>'
            % (cx, y0 + 16, short)
        )
    parts += legend(
        [("before gc (loose objects: 500,259)", "#c0392b"), ("after git gc (packed)", "#27ae60")],
        ML + 12, MT + 8,
    )
    parts.append(
        '<text x="%d" y="%d" text-anchor="middle" font-size="14" font-weight="700">'
        "Same repo at 100,000 merges: before vs after git gc</text>" % (W / 2, 18)
    )
    parts.append("</svg>")
    return "\n".join(parts)


def fig3_per_merge_time():
    xs, ys = [], []
    with open(os.path.join(RESULTS, "merge_times.csv")) as f:
        for row in csv.reader(f):
            xs.append(int(row[0]))
            ys.append(float(row[1]))

    # bin per 1000 merges: median and p95
    bins = []
    for lo in range(0, 100000, 1000):
        seg = sorted(ys[lo : lo + 1000])
        med = seg[len(seg) // 2]
        p95 = seg[int(len(seg) * 0.95)]
        bins.append((lo + 500, med, p95))

    parts = svg_open("per-merge wall time")
    xmin, xmax = 0, 100000
    ymin = 0
    # Y max follows the data: max bin p95 rounded up to a 40ms tick,
    # so the p95 line is never clipped by the plot area.
    ymax = int(math.ceil(max(b[2] for b in bins) / 40.0)) * 40

    def xfn(v):
        return ML + (v - xmin) / (xmax - xmin) * PW

    def yfn(v):
        return MT + PH - (v - ymin) / (ymax - ymin) * PH

    for v in range(0, ymax + 1, 40):
        y = yfn(v)
        parts.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e5e7eb"/>' % (ML, y, ML + PW, y))
        parts.append('<text x="%d" y="%.1f" text-anchor="end" fill="#666">%dms</text>' % (ML - 6, y + 4, v))
    for v in [0, 20000, 40000, 60000, 80000, 100000]:
        x = xfn(v)
        parts.append('<text x="%.1f" y="%d" text-anchor="middle" fill="#666">%dk</text>' % (x, MT + PH + 18, v // 1000))
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#999"/>' % (ML, MT + PH, ML + PW, MT + PH))
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#999"/>' % (ML, MT + PH, ML, MT))
    parts.append(
        '<text x="%.1f" y="%d" text-anchor="middle" fill="#333" font-size="13">merge index</text>'
        % (ML + PW / 2, H - 8)
    )

    med_pts = [(xfn(b[0]), yfn(b[1])) for b in bins]
    p95_pts = [(xfn(b[0]), yfn(b[2])) for b in bins]
    parts.append(series_line(p95_pts, "#e67e22"))
    parts.append(series_line(med_pts, "#2980b9"))
    parts += legend(
        [("median per 1,000-merge bin", "#2980b9"), ("p95 per bin", "#e67e22")],
        ML + 12, MT + 8,
    )
    parts.append(
        '<text x="%d" y="%d" text-anchor="middle" font-size="14" font-weight="700">'
        "Per-merge wall time (n=100,000, binned)</text>" % (W / 2, 18)
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = load_benchmarks()
    with open(os.path.join(RESULTS, "post_gc_bench.json")) as f:
        postgc = json.load(f)

    figs = {
        "fig1-latency-vs-merges.svg": fig1_latency_vs_merges(rows),
        "fig2-gc-before-after.svg": fig2_gc_before_after(rows, postgc),
        "fig3-per-merge-time.svg": fig3_per_merge_time(),
    }
    for name, svg in figs.items():
        p = os.path.join(OUT, name)
        with open(p, "w") as f:
            f.write(svg)
        print("wrote %s (%d bytes)" % (p, len(svg)))


if __name__ == "__main__":
    main()
