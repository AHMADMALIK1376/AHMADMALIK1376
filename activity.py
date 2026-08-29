# -*- coding: utf-8 -*-
"""
Thirty days of activity, drawn the way a chart recorder draws it.

Paper runs left to right under a pen. A day with nothing on it is a flat line,
and a busy day is a burst of oscillation whose height follows the count. That
suits this data: most days are silent and a few are not, and a shape that makes
the silence visible is more honest than one that smooths it away.

The numbers come from the same contributions endpoint the year dial uses, so
this and that panel can never disagree with each other.

The pen is not decoration. Its path is generated from the trace's own vertices,
so the nib sits on the line it is drawing rather than near it.

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
DUR = 18.0
DRAW_FROM, DRAW_TO = 4.0, 66.0     # the rest of the loop holds the finished trace

X0, X1 = 72.0, 1168.0
BASE = 186.0
AMP = 74.0
DAYS = 30

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


def trace_points(days, peak):
    """Vertices of the pen's path across the whole strip.

    A quiet day is two points at the baseline. A busy one is a burst: the nib
    thrown up, past the line, up again and back, which is what a recorder does
    when something actually happens rather than a single tidy peak.
    """
    step = (X1 - X0) / float(DAYS)
    pts = [(X0, BASE)]
    for i, (_iso, count, _lvl) in enumerate(days):
        x = X0 + i * step
        if count <= 0:
            pts.append((x + step, BASE))
            continue
        # a root scale, so a small day is still visibly a day
        a = (count / float(peak)) ** 0.6 * AMP
        for f, m in ((0.18, -1.0), (0.34, 0.72), (0.50, -0.80),
                     (0.66, 0.45), (0.82, -0.30), (1.0, 0.0)):
            pts.append((x + step * f, BASE + a * m))
    return pts


def build(days, path="assets/activity.svg"):
    """days: [(iso, count, level)] oldest first; the last 30 are used."""
    days = list(days)[-DAYS:]
    while len(days) < DAYS:
        days.insert(0, ("", 0, 0))
    counts = [c for _i, c, _l in days]
    peak = max(1, max(counts))
    total = sum(counts)
    active = sum(1 for c in counts if c)
    peak_i = counts.index(peak)
    step = (X1 - X0) / float(DAYS)

    pts = trace_points(days, peak)
    css = ["@keyframes blip{0%,100%{opacity:1}50%{opacity:.25}}",
           ".blip{animation:blip 1.6s steps(1,end) infinite}",
           "@keyframes fade{0%{opacity:0}}"]

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="Thirty days of activity drawn as a chart recorder trace: '
           '%d contributions over %d active days, peaking at %d">'
           % (W, H, W, H, total, active, peak),
           "<title>Commit Activity</title>",
           '<defs><pattern id="ag" width="26" height="26" patternUnits="userSpaceOnUse">'
           '<circle cx="1.5" cy="1.5" r="1" fill="%s"/></pattern>'
           '<clipPath id="strip"><rect x="%.0f" y="96" width="%.0f" height="180" rx="4"/></clipPath>'
           '__STYLE__</defs>' % (GRID, X0 - 12, X1 - X0 + 24),
           '<rect width="%d" height="%d" fill="%s"/>' % (W, H, SKY),
           '<rect width="%d" height="%d" fill="url(#ag)"/>' % (W, H)]

    out.append(_txt(48, 44, "COMMIT ACTIVITY", 14, INK, "800", "start", "3.4"))
    out.append(_txt(W - 66, 44, "LIVE · REBUILT DAILY", 12.5, FAINT, "600", "end", "2.2"))
    out.append('<circle cx="%d" cy="40" r="5" fill="%s" class="blip"/>' % (W - 48, TEAMIST))
    out.append('<path d="M48,58 H%d" stroke="%s" stroke-width="1.4" fill="none"/>' % (W - 48, RULE))
    out.append(_txt(48, 78, "LAST 30 DAYS · A FLAT LINE IS A DAY WITH NOTHING ON IT",
                    10.5, MUTED, "600", "start", "1.5"))

    # ── the paper ────────────────────────────────────────────────────────
    out.append('<rect x="%.0f" y="96" width="%.0f" height="180" rx="4" fill="%s" '
               'stroke="%s" stroke-width="1.3"/>' % (X0 - 12, X1 - X0 + 24, PAPER, RULE))
    for j in range(1, 6):                       # chart rulings
        y = 96 + j * 30
        out.append('<path d="M%.0f,%.0f H%.0f" stroke="%s" stroke-width="1"/>'
                   % (X0 - 12, y, X1 + 12, RULING))
    for i in range(DAYS + 1):
        x = X0 + i * step
        out.append('<path d="M%.1f,100 V272" stroke="%s" stroke-width="%s"/>'
                   % (x, RULING, "1.4" if i % 5 == 0 else "0.7"))
    out.append('<path d="M%.0f,%.0f H%.0f" stroke="%s" stroke-width="1.2" '
               'stroke-dasharray="3 4"/>' % (X0 - 12, BASE, X1 + 12, _mix(RULING, INK, 0.25)))
    for edge in (100, 268):                     # sprocket perforations
        holes = "".join("M%.0f,%dh0.1" % (X0 - 4 + k * 18, edge) for k in range(62))
        out.append('<path d="%s" stroke="%s" stroke-width="3.4" stroke-linecap="round" '
                   'fill="none"/>' % (holes, _mix(RULING, INK, 0.18)))

    # ── the trace, drawn as the paper runs ───────────────────────────────
    d = "M%.1f,%.1f " % pts[0] + " ".join("L%.1f,%.1f" % p for p in pts[1:])
    css.append(_kf("draw", "0%%,%.0f%%{stroke-dashoffset:1}%.0f%%,100%%{stroke-dashoffset:0}"
                   % (DRAW_FROM, DRAW_TO)))
    css.append(".draw{stroke-dasharray:1;stroke-dashoffset:1;animation:draw "
               + "%.1f" % DUR + "s linear infinite}")
    out.append('<g clip-path="url(#strip)"><path class="draw" pathLength="1" d="%s" fill="none" '
               'stroke="%s" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>'
               "</g>" % (d, CRIMSON))

    # ── the pen, riding the vertices of the line it draws ────────────────
    total_len = X1 - X0
    stops = []
    for x, y in pts:
        f = (x - X0) / total_len
        stops.append("%.3f%%{transform:translate(%.1fpx,%.1fpx)}"
                     % (DRAW_FROM + f * (DRAW_TO - DRAW_FROM), x, y))
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

    # ── the busiest day, called out ──────────────────────────────────────
    px = X0 + (peak_i + 0.18) * step
    py = BASE - AMP
    lab = days[peak_i][0]
    when = "%s %s" % (lab[8:10].lstrip("0"), MONTHS[int(lab[5:7]) - 1]) if lab else ""
    css.append(".pk{animation:fade .6s ease-out both;animation-delay:%.1fs}"
               % (DUR * (DRAW_FROM + (peak_i / float(DAYS)) * (DRAW_TO - DRAW_FROM)) / 100.0))
    out.append('<g class="pk">')
    out.append("  " + '<path d="M%.1f,%.1f V%.1f" stroke="%s" stroke-width="1.1" '
                      'stroke-dasharray="2 3"/>' % (px, py, 118, _mix(RULING, INK, 0.4)))
    out.append("  " + _txt(px, 112, "%d ON %s" % (peak, when), 9.5, CRIMSON, "800", "middle", "1.2"))
    out.append("</g>")

    # ── the axis, and what the trace adds up to ──────────────────────────
    for i in (0, 7, 14, 21, 29):
        iso = days[i][0]
        when = "%s %s" % (iso[8:10].lstrip("0"), MONTHS[int(iso[5:7]) - 1]) if iso else ""
        out.append(_txt(X0 + (i + 0.5) * step, 292,
                        "TODAY" if i == 29 else when, 9,
                        CRIMSON if i == 29 else FAINT, "800" if i == 29 else "600",
                        "middle", "1.1"))
    for k, (lbl, val) in enumerate((("CONTRIBUTIONS", total), ("ACTIVE DAYS", "%d / 30" % active),
                                    ("BUSIEST DAY", peak))):
        x = 48 + k * 190
        out.append(_txt(x, H - 12, lbl, 9, FAINT, "700", "start", "1.6"))
        out.append(_txt(x + 118, H - 12, str(val), 11, INK, "800", "start", "0.6"))
    out.append(_txt(W - 48, H - 12, "GITHUB.COM/AHMADMALIK1376", 9.5, FAINT, "600", "end", "1.5"))
    out.append("</svg>")

    svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote %s (%d days, %d contributions, %d active, peak %d, %d KB)"
          % (path, DAYS, total, active, peak, len(svg) // 1024))
    return path


if __name__ == "__main__":
    import json
    import sys
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    build([(d["date"], d["count"], d["level"]) for d in data["days"]])
