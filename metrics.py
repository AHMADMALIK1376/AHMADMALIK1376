# -*- coding: utf-8 -*-
"""
System metrics drawn as a year dial.

A year of contributions wrapped into a ring: one full turn is twelve months,
each day a spoke whose length and colour follow that day's real count. The total
sits in the middle and the account's other figures read out beside it.

This replaces six tiles that only ever showed a number each. The dial shows the
shape of a year rather than a single figure, and every spoke is a real day.

Contribution data comes from github.com/users/<login>/contributions, the same
endpoint that renders the calendar on a profile page. It needs no token, which
matters because the REST API does not expose contributions at all and the
GraphQL route that does would need a scope the workflow's built-in token has no
reason to carry.

House style, matching the rest of the profile art: solid fills, no gradients and
no filters.
"""
import math

AEGEAN, CORAL = "#0077C8", "#F88379"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
SKY = "#F2EDE6"
GRID = "#E6DBCA"
TRACK = "#E0D6C4"
INK = "#2E2A24"
MUTED = "#7D7266"
FAINT = "#A2988A"
RULE = "#D9D0C1"
CARD = "#FBF7F0"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

W, H = 1240, 580
CX, CY = 350, 320          # centre of the dial
R_IN, R_OUT = 112, 196     # a zero day sits at R_IN, the busiest reaches R_OUT

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _txt(x, y, s, size, fill, weight="700", anchor="start", ls="0"):
    return ('<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" font-weight="%s" '
            'fill="%s" text-anchor="%s" letter-spacing="%s">%s</text>'
            % (x, y, MONO, size, weight, fill, anchor, ls, _esc(s)))


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return "#%02X%02X%02X" % tuple(
        max(0, min(255, int(round(ra[i] + (rb[i] - ra[i]) * t)))) for i in range(3))


# a single-hue ramp, so spoke colour reads as intensity rather than category
LEVELS = [TRACK, _mix(SKY, AEGEAN, 0.34), _mix(SKY, AEGEAN, 0.62),
          AEGEAN, _mix(AEGEAN, INK, 0.38)]


def _human(n):
    return "%.1fk" % (n / 1000.0) if n >= 1000 else str(n)


def year_dial(days, total, stats, path="assets/year-dial.svg"):
    """days: [(iso_date, count, level)] oldest first. stats: [(label, value, sub)]."""
    if not days:
        days = [("2000-01-01", 0, 0)]
    n = len(days)
    peak = max(1, max(d[1] for d in days))

    css = ["@keyframes sweep{to{stroke-dashoffset:0}}",
           "@keyframes fade{0%{opacity:0}}",
           ".sp{stroke-dashoffset:1;animation:sweep .5s ease-out forwards}",
           ".rd{animation:fade .7s ease-out backwards}"]

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="System metrics: %d contributions over the last year shown '
           'as a radial dial, with repository, follower and activity counts">'
           % (W, H, W, H, total),
           "<title>System Metrics</title>",
           '<defs><pattern id="mg" width="26" height="26" patternUnits="userSpaceOnUse">'
           '<circle cx="1.5" cy="1.5" r="1" fill="%s"/></pattern>__STYLE__</defs>' % GRID,
           '<rect width="%d" height="%d" fill="%s"/>' % (W, H, SKY),
           '<rect width="%d" height="%d" fill="url(#mg)"/>' % (W, H)]

    out.append(_txt(48, 46, "SYSTEM METRICS", 14, INK, "800", "start", "3.4"))
    out.append(_txt(W - 48, 46, "LIVE FROM THE GITHUB API", 12.5, FAINT, "600", "end", "2.2"))
    out.append('<path d="M48,60 H%d" stroke="%s" stroke-width="1.4" fill="none"/>' % (W - 48, RULE))
    out.append(_txt(48, 80, "ONE TURN IS ONE YEAR · EVERY SPOKE IS A DAY",
                    10.5, MUTED, "600", "start", "1.5"))

    # ── the ring the spokes stand on ─────────────────────────────────────
    out.append('<circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" stroke-width="1.4"/>'
               % (CX, CY, R_IN, RULE))
    out.append('<circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" stroke-width="1.2" '
               'stroke-dasharray="2 6"/>' % (CX, CY, R_OUT, RULE))

    # ── one spoke per day ────────────────────────────────────────────────
    for i, (iso, count, level) in enumerate(days):
        ang = math.radians(-90.0 + i * 360.0 / n)
        # square-rooted so a single very busy day cannot flatten the rest
        grow = (count / float(peak)) ** 0.5
        r2 = R_IN + (R_OUT - R_IN) * grow
        if count == 0:
            r2 = R_IN + 3
        x1, y1 = CX + math.cos(ang) * R_IN, CY + math.sin(ang) * R_IN
        x2, y2 = CX + math.cos(ang) * r2, CY + math.sin(ang) * r2
        css.append(".s%d{animation-delay:%.3fs}" % (i, 0.25 + i * 0.0035))
        out.append('<path class="sp s%d" pathLength="1" stroke-dasharray="1" '
                   'd="M%.1f,%.1f L%.1f,%.1f" stroke="%s" stroke-width="1.9" '
                   'stroke-linecap="round"/>'
                   % (i, x1, y1, x2, y2, LEVELS[min(4, level)]))

    # ── month marks ──────────────────────────────────────────────────────
    seen = set()
    for i, (iso, _c, _l) in enumerate(days):
        mo = int(iso[5:7])
        if mo in seen or iso[8:10] > "07":      # first week of each month only
            continue
        seen.add(mo)
        ang = math.radians(-90.0 + i * 360.0 / n)
        tx, ty = CX + math.cos(ang) * (R_OUT + 22), CY + math.sin(ang) * (R_OUT + 22)
        out.append('<path d="M%.1f,%.1f L%.1f,%.1f" stroke="%s" stroke-width="1.3"/>'
                   % (CX + math.cos(ang) * (R_OUT + 4), CY + math.sin(ang) * (R_OUT + 4),
                      CX + math.cos(ang) * (R_OUT + 12), CY + math.sin(ang) * (R_OUT + 12),
                      RULE))
        out.append(_txt(tx, ty + 3.4, MONTHS[mo - 1], 8.5, FAINT, "700", "middle", "1"))

    # ── the total, in the middle ─────────────────────────────────────────
    out.append('<circle cx="%d" cy="%d" r="%d" fill="%s"/>' % (CX, CY, R_IN - 10, CARD))
    out.append('<g class="rd" style="animation-delay:.9s">')
    out.append("  " + _txt(CX, CY - 12, _human(total), 46, AEGEAN, "800", "middle", "-1"))
    out.append("  " + _txt(CX, CY + 12, "CONTRIBUTIONS", 10.5, INK, "800", "middle", "2.2"))
    out.append("  " + _txt(CX, CY + 30, "LAST 12 MONTHS", 8.5, FAINT, "600", "middle", "1.4"))
    busiest = max(days, key=lambda d: d[1])
    out.append("  " + _txt(CX, CY + 52, "BUSIEST DAY %d" % busiest[1], 8.5,
                           MUTED, "700", "middle", "1.2"))
    out.append("</g>")

    # ── the other figures, read out beside the dial ──────────────────────
    col_x, row_y = (700, 980), (150, 258, 366)
    for i, (label, value, sub) in enumerate(stats[:6]):
        x, y = col_x[i % 2], row_y[i // 2]
        css.append(".r%d{animation-delay:%.2fs}" % (i, 1.0 + i * 0.08))
        out.append('<g class="rd r%d">' % i)
        out.append("  " + _txt(x, y, label, 10, MUTED, "800", "start", "2.2"))
        out.append("  " + '<path d="M%d,%d H%d" stroke="%s" stroke-width="1.2"/>'
                          % (x, y + 10, x + 200, RULE))
        out.append("  " + _txt(x, y + 46, str(value), 32, INK, "800", "start", "-0.5"))
        out.append("  " + _txt(x, y + 64, sub, 9, FAINT, "600", "start", "1.2"))
        out.append("</g>")

    # ── legend for the ramp ──────────────────────────────────────────────
    lx = 700
    out.append(_txt(lx, H - 66, "PER DAY", 8.5, FAINT, "800", "start", "1.8"))
    out.append(_txt(lx + 62, H - 66, "LESS", 8, FAINT, "600", "start", "1"))
    for i, col in enumerate(LEVELS):
        out.append('<rect x="%d" y="%d" width="13" height="13" rx="3" fill="%s"/>'
                   % (lx + 96 + i * 17, H - 76, col))
    out.append(_txt(lx + 96 + 5 * 17 + 6, H - 66, "MORE", 8, FAINT, "600", "start", "1"))

    out.append('<path d="M48,%d H%d" stroke="%s" stroke-width="1.4" fill="none"/>'
               % (H - 32, W - 48, RULE))
    out.append(_txt(48, H - 12, "REBUILT DAILY FROM THE GITHUB API", 10, FAINT,
                    "600", "start", "1.6"))
    out.append(_txt(W - 48, H - 12, "GITHUB.COM/AHMADMALIK1376", 10, FAINT, "600", "end", "1.6"))
    out.append("</svg>")

    svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote %s (%d days, %d contributions, peak %d, %d KB)"
          % (path, n, total, peak, len(svg) // 1024))
    return path


if __name__ == "__main__":
    import json
    import sys
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    year_dial([(d["date"], d["count"], d["level"]) for d in data["days"]],
              data["total"], data.get("stats", []))
