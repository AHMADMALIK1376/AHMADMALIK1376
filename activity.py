# -*- coding: utf-8 -*-
"""
Every day of activity since the account opened, drawn as a chart recorder draws.

Paper runs left to right under a pen. A day with nothing on it is a flat line
and a busy day throws the nib off the baseline, alternately up and down, by an
amount that follows the count. Most days here are silent, and a shape that lets
the silence stay visible is more honest than one that smooths it away.

This covers the whole history rather than a window on the end of it, so the
quiet first months and the run of work after them are both on the same strip.

The numbers come from the same contributions calendar the year dial uses, so
this and that panel can never disagree with each other.

Two things that are easy to get wrong and are handled deliberately:

  - The reveal is a mask widening at a constant rate, not stroke-dashoffset.
    Dashoffset advances along the path's own LENGTH, which is not proportional
    to x: a stretch of tall spikes is long in path terms and short in x, so it
    swallows a disproportionate share of the clock while the quiet months flash
    past. With a mask, halfway through the loop is halfway through the dates,
    the month axis means something, and the nib — keyed to x on the same clock —
    sits on the leading edge of the ink by construction.
  - Runs of empty days collapse to a single straight segment. Four hundred
    days of separate vertices would be four hundred keyframes for no drawn
    difference, and the pen rule is emitted once per vertex.

Amplitude is scaled by a root rather than linearly. A day of two against a peak
of forty-seven would be half a pixel on a straight scale, which reads as nothing
happened when something did.

House style: solid fills, no gradients, no filters.
"""
AEGEAN, CORAL = "#0077C8", "#F88379"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
SKY = "#F2EDE6"
GRID = "#E6DBCA"
PAPER = "#FBF7F0"
RULING = "#E7DCCA"
INK = "#2E2A24"
MUTED = "#7D7266"
FAINT = "#A2988A"
RULE = "#D9D0C1"
STEEL = "#B9AC97"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

W, H = 1240, 320
DUR = 26.0
DRAW_FROM, DRAW_TO = 3.0, 74.0     # the rest of the loop holds the finished trace

X0, X1 = 72.0, 1168.0
BASE = 186.0
AMP = 74.0

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _txt(x, y, s, size, fill, weight="700", anchor="start", ls="0", cls=None):
    return ('<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" font-weight="%s" '
            'fill="%s" text-anchor="%s" letter-spacing="%s"%s>%s</text>'
            % (x, y, MONO, size, weight, fill, anchor, ls,
               (' class="%s"' % cls) if cls else "", _esc(s)))


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return "#%02X%02X%02X" % tuple(
        max(0, min(255, int(round(ra[i] + (rb[i] - ra[i]) * t)))) for i in range(3))


def _kf(name, body):
    return "@keyframes " + name + "{" + body + "}"


def _when(iso, with_year=False):
    if not iso:
        return ""
    s = "%s %s" % (iso[8:10].lstrip("0"), MONTHS[int(iso[5:7]) - 1])
    return s + " " + iso[2:4] if with_year else s


def trace_points(days, peak):
    """Vertices of the pen's path across the whole strip.

    One spike per active day, thrown alternately above and below the baseline so
    a run of busy days reads as oscillation rather than a row of identical
    teeth. Empty days are not given vertices of their own: a run of them is one
    straight segment, which draws the same and costs one keyframe instead of
    hundreds.
    """
    n = len(days)
    step = (X1 - X0) / float(n)
    pts = [(X0, BASE)]
    flip = 1
    for i, (_iso, count, _lvl) in enumerate(days):
        if count <= 0:
            continue                              # the flat run is closed below
        x = X0 + i * step
        if pts[-1][0] < x:                        # close the preceding silence
            pts.append((x, BASE))
        # a root scale, so a small day is still visibly a day
        a = (count / float(peak)) ** 0.6 * AMP
        pts.append((x + step * 0.5, BASE - a * flip))
        pts.append((x + step, BASE))
        flip = -flip
    if pts[-1][0] < X1:
        pts.append((X1, BASE))
    return pts


def build(days, path="assets/activity.svg"):
    """days: [(iso, count, level)] oldest first. All of them are drawn."""
    days = [d for d in days if d[0]]
    if not days:
        days = [("2000-01-01", 0, 0)]
    n = len(days)
    counts = [c for _i, c, _l in days]
    peak = max(1, max(counts))
    total = sum(counts)
    active = sum(1 for c in counts if c)
    peak_i = counts.index(peak)
    step = (X1 - X0) / float(n)

    pts = trace_points(days, peak)
    css = ["@keyframes blip{0%,100%{opacity:1}50%{opacity:.25}}",
           ".blip{animation:blip 1.6s steps(1,end) infinite}",
           "@keyframes fade{0%{opacity:0}}"]

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="Every day of activity since the account opened, drawn as a '
           'chart recorder trace: %d contributions over %d active days out of %d, peaking at %d">'
           % (W, H, W, H, total, active, n, peak),
           "<title>Commit Activity</title>",
           '<defs><pattern id="ag" width="26" height="26" patternUnits="userSpaceOnUse">'
           '<circle cx="1.5" cy="1.5" r="1" fill="%s"/></pattern>'
           '<clipPath id="strip"><rect x="%.0f" y="96" width="%.0f" height="180" rx="4"/></clipPath>'
           '<mask id="reveal" maskUnits="userSpaceOnUse" x="0" y="0" '
           'width="%d" height="%d"><rect class="rv" x="%.1f" y="90" '
           'width="%.1f" height="200" fill="#fff"/></mask>'
           '__STYLE__</defs>' % (GRID, X0 - 12, X1 - X0 + 24,
                                 W, H, X0, X1 - X0),
           '<rect width="%d" height="%d" fill="%s"/>' % (W, H, SKY),
           '<rect width="%d" height="%d" fill="url(#ag)"/>' % (W, H)]

    out.append(_txt(48, 44, "COMMIT ACTIVITY", 14, INK, "800", "start", "3.4"))
    out.append(_txt(W - 66, 44, "LIVE · REBUILT DAILY", 12.5, FAINT, "600", "end", "2.2"))
    out.append('<circle cx="%d" cy="40" r="5" fill="%s" class="blip"/>' % (W - 48, TEAMIST))
    out.append('<path d="M48,58 H%d" stroke="%s" stroke-width="1.4" fill="none"/>' % (W - 48, RULE))
    out.append(_txt(48, 78, "EVERY DAY SINCE %s · A FLAT LINE IS A DAY WITH NOTHING ON IT"
                    % _when(days[0][0], True).upper(), 10.5, MUTED, "600", "start", "1.5"))

    # ── the paper ────────────────────────────────────────────────────────
    out.append('<rect x="%.0f" y="96" width="%.0f" height="180" rx="4" fill="%s" '
               'stroke="%s" stroke-width="1.3"/>' % (X0 - 12, X1 - X0 + 24, PAPER, RULE))
    for j in range(1, 6):                       # chart rulings
        y = 96 + j * 30
        out.append('<path d="M%.0f,%.0f H%.0f" stroke="%s" stroke-width="1"/>'
                   % (X0 - 12, y, X1 + 12, RULING))
    # a vertical ruling on the first of each month, rather than every day: at
    # four hundred days apart a per-day rule would fill the paper solid
    month_x = []
    for i, (iso, _c, _l) in enumerate(days):
        if iso[8:10] != "01":
            continue
        x = X0 + i * step
        month_x.append((x, iso))
        out.append('<path d="M%.1f,100 V272" stroke="%s" stroke-width="%s"/>'
                   % (x, RULING, "1.4" if iso[5:7] == "01" else "0.8"))
    out.append('<path d="M%.0f,%.0f H%.0f" stroke="%s" stroke-width="1.2" '
               'stroke-dasharray="3 4"/>' % (X0 - 12, BASE, X1 + 12, _mix(RULING, INK, 0.25)))
    for edge in (100, 268):                     # sprocket perforations
        holes = "".join("M%.0f,%dh0.1" % (X0 - 4 + k * 18, edge) for k in range(62))
        out.append('<path d="%s" stroke="%s" stroke-width="3.4" stroke-linecap="round" '
                   'fill="none"/>' % (holes, _mix(RULING, INK, 0.18)))

    # ── the trace, revealed as the paper runs ────────────────────────────
    # A mask widening at a constant rate, not stroke-dashoffset. Dashoffset
    # advances along the path's own LENGTH, so a stretch of tall spikes eats a
    # disproportionate share of the clock and the pen appears to crawl there
    # while racing across the quiet months. Paper in a real recorder moves at
    # one speed, and that is also what makes the month axis mean anything:
    # halfway through the loop is halfway through the dates.
    d = "M%.1f,%.1f " % pts[0] + " ".join("L%.1f,%.1f" % p for p in pts[1:])
    css.append(_kf("rev", "0%%,%.0f%%{transform:scaleX(0)}%.0f%%,100%%{transform:scaleX(1)}"
                   % (DRAW_FROM, DRAW_TO)))
    css.append(".rv{transform-box:fill-box;transform-origin:left center;"
               "animation:rev " + "%.1f" % DUR + "s linear infinite}")
    out.append('<g clip-path="url(#strip)" mask="url(#reveal)">'
               '<path d="%s" fill="none" stroke="%s" stroke-width="1.9" '
               'stroke-linejoin="round" stroke-linecap="round"/></g>' % (d, CRIMSON))

    # ── the pen, on the same clock as the reveal ─────────────────────────
    # Both are linear in x, so the nib is on the leading edge of the ink by
    # construction rather than by luck.
    span_x = X1 - X0
    stops, last = [], -1.0
    for x, y in pts:
        pct = DRAW_FROM + ((x - X0) / span_x) * (DRAW_TO - DRAW_FROM)
        if pct - last < 0.005:                  # two stops at one percentage is
            continue                            # a dropped keyframe, not detail
        last = pct
        stops.append("%.3f%%{transform:translate(%.1fpx,%.1fpx)}" % (pct, x, y))
    css.append(_kf("pen", "0%%{transform:translate(%.1fpx,%.1fpx)}" % pts[0]
                   + "".join(stops)
                   + "100%%{transform:translate(%.1fpx,%.1fpx)}" % pts[-1]))
    css.append(".pen{animation:pen " + "%.1f" % DUR + "s linear infinite}")
    out.append('<g class="pen">')
    out.append('  <path d="M0,0 L-7,-30 L7,-30 Z" fill="%s"/>' % STEEL)      # nib
    out.append('  <rect x="-16" y="-58" width="32" height="30" rx="5" fill="%s" '
               'stroke="%s" stroke-width="1.6"/>' % (INK, INK))
    out.append('  <rect x="-9" y="-50" width="18" height="6" rx="3" fill="%s"/>' % CRIMSON)
    out.append('  <circle cx="0" cy="0" r="3.4" fill="%s"/>' % CRIMSON)
    out.append("</g>")

    # ── the busiest day, called out when the pen reaches it ──────────────
    px = X0 + (peak_i + 0.5) * step
    reach = DRAW_FROM + (peak_i / float(n)) * (DRAW_TO - DRAW_FROM)
    css.append(".pk{animation:fade .6s ease-out both;animation-delay:%.1fs}"
               % (DUR * reach / 100.0))
    # No leader line: the busiest day is by definition the tallest spike, so a
    # leader would be drawn straight down the spike it points at. The label sits
    # directly above it instead, clamped so it cannot hang off the paper.
    lab = "%d ON %s" % (peak, _when(days[peak_i][0]))
    half = len(lab) * 3.3
    px = min(max(px, X0 + half), X1 - half)
    out.append('<g class="pk">')
    # above the paper edge, not on it: inside the strip it would land on the
    # sprocket row and, at the peak's own x, on the peak itself
    out.append("  " + _txt(px, 90, lab, 9.5, CRIMSON, "800", "middle", "1.2"))
    out.append("</g>")

    # ── the axis: months, thinned so the labels never collide ────────────
    shown_x = -999.0
    for x, iso in month_x:
        # the right end of the axis belongs to TODAY, and a month label there
        # would be printed straight through it
        if x - shown_x < 62 or X1 - x < 58:
            continue
        shown_x = x
        mo = MONTHS[int(iso[5:7]) - 1]
        out.append(_txt(x, 292, mo if iso[5:7] != "01" else mo + " " + iso[2:4],
                        9, FAINT, "600", "middle", "1.1"))
    out.append(_txt(X1, 292, "TODAY", 9, CRIMSON, "800", "end", "1.1"))

    # ── what the trace adds up to ────────────────────────────────────────
    span = "%s – %s" % (_when(days[0][0], True), _when(days[-1][0], True))
    for k, (lbl, val) in enumerate((("CONTRIBUTIONS", total),
                                    ("ACTIVE DAYS", "%d / %d" % (active, n)),
                                    ("BUSIEST DAY", peak),
                                    ("SPAN", span))):
        x = 48 + k * 215
        out.append(_txt(x, H - 12, lbl, 9, FAINT, "700", "start", "1.6"))
        out.append(_txt(x + 112, H - 12, str(val), 11, INK, "800", "start", "0.6"))
    out.append("</svg>")

    svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote %s (%d days, %d contributions, %d active, peak %d, "
          "%d vertices, %d KB)"
          % (path, n, total, active, peak, len(pts), len(svg) // 1024))
    return path


if __name__ == "__main__":
    import json
    import sys
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    build([(d["date"], d["count"], d["level"]) for d in data["days"]])
