# -*- coding: utf-8 -*-
"""
Every day of work as a star chart, drawn the way a celestial atlas is printed.

Not a photograph of a night sky: an engraved chart on paper, ink on cream, the
way Bayer and Flamsteed published them. That keeps the panel inside the house
palette instead of putting one black rectangle among a dozen cream ones, and a
printed atlas is the closer metaphor anyway — this is a record of observations,
not a view through a window.

The positions are real. Horizontal is the week, vertical is the day of the week,
so the chart is the contribution calendar redrawn as a sky. Each star is jittered
within its own cell — never outside it — because stars landing on exact rows and
columns join at right angles and the figures come out looking like a grid. That makes the shape
of a working week visible — which rows fill, which stay empty — and no other
panel on the profile shows it. Magnitude is the day's contribution count, on a
root scale, because a day of two against a peak of forty-seven would otherwise
be a dot too small to see.

THE AXIS BREAK. This history has one contribution, then nine months of nothing,
then all the rest. Drawn to a linear scale that is two thirds empty paper, and
the part worth reading is squeezed into the last third. So a run of empty weeks
past a threshold collapses into a narrow gutter marked with a break — the
standard device, and an honest one, because the gutter is labelled with exactly
how many weeks it stands for rather than quietly dropping them. Everything
outside the gutters keeps a single consistent scale.

Constellations are drawn per month with a minimum spanning tree over that
month's stars. A tree is what makes the figures read: joining the stars in date
order gives a zigzag that crosses itself, while the shortest set of links that
still connects everything looks like something an astronomer would have named.

The telescope sweeps once, left to right, and each star lights as the sweep
reaches it. A month's figure is drawn only when its last star is lit, so the
constellations appear the way they would if you were actually finding them.

House style: solid fills, no gradients, no filters.
"""
import datetime
import math

AEGEAN, CORAL = "#0077C8", "#F88379"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
SKY = "#F2EDE6"
GRID = "#E6DBCA"
CHART = "#FBF7F0"
RULING = "#E7DCCA"
INK = "#2E2A24"
INK_2 = "#5E5349"
MUTED = "#7D7266"
FAINT = "#A2988A"
RULE = "#D9D0C1"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

W, H = 1240, 486
DUR = 30.0
SWEEP_FROM, SWEEP_TO = 4.0, 78.0    # the rest of the loop holds the finished chart

FX0, FX1 = 118.0, 1168.0            # the charted field
FY0, FY1 = 126.0, 380.0
ROWS = 7

GAP_MIN = 6                         # empty weeks in a row before the axis breaks
GAP_W = 54.0                        # what such a run is compressed to

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
DOW = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]


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


def _d(iso):
    return datetime.date(int(iso[:4]), int(iso[5:7]), int(iso[8:10]))


def _when(iso):
    return "%s %s %s" % (iso[8:10].lstrip("0"), MONTHS[int(iso[5:7]) - 1], iso[2:4])


def _mst(pts):
    """Prim's, over the stars of one month.

    Joining them in date order gives a zigzag that crosses itself. The shortest
    set of links that still connects every star reads as a figure instead.
    """
    n = len(pts)
    if n < 2:
        return []
    inside, out, edges = {0}, set(range(1, n)), []
    while out:
        best = None
        for i in inside:
            for j in out:
                dist = math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
                if best is None or dist < best[0]:
                    best = (dist, i, j)
        _dist, i, j = best
        edges.append((i, j))
        inside.add(j)
        out.discard(j)
    return edges


def _layout(weeks_active):
    """Left edge and width of every week column, with long voids compressed.

    Returns (xs, widths, gaps) where gaps is [(start_week, end_week, x, w)] for
    each compressed run, so the break can be drawn and labelled.
    """
    n = len(weeks_active)
    runs, i = [], 0
    while i < n:                                   # find the runs worth breaking
        if weeks_active[i]:
            i += 1
            continue
        j = i
        while j < n and not weeks_active[j]:
            j += 1
        if j - i >= GAP_MIN:
            runs.append((i, j))
        i = j
    kept = n - sum(j - i for i, j in runs)
    unit = ((FX1 - FX0) - GAP_W * len(runs)) / float(max(1, kept))

    xs, widths, gaps = [0.0] * n, [unit] * n, []
    x, i = FX0, 0
    run_at = {i: (i, j) for i, j in runs}
    while i < n:
        if i in run_at:
            a, b = run_at[i]
            for k in range(a, b):                  # every week in the void maps
                xs[k] = x                          # into the gutter itself
                widths[k] = GAP_W / float(b - a)
            gaps.append((a, b, x, GAP_W))
            x += GAP_W
            i = b
            continue
        xs[i], widths[i] = x, unit
        x += unit
        i += 1
    return xs, widths, gaps


def _zig(x, y0, y1, amp=3.5, seg=13.0):
    pts, k = [], 0
    y = y0
    while y < y1:
        pts.append((x + (amp if k % 2 else -amp), y))
        y += seg
        k += 1
    pts.append((x + (amp if k % 2 else -amp), y1))
    return "M" + " L".join("%.1f,%.1f" % p for p in pts)


def build(days, path="assets/constellation.svg"):
    """days: [(iso, count, level)] oldest first. Every day is placed."""
    days = [d for d in days if d[0]]
    if not days:
        days = [(datetime.date.today().isoformat(), 0, 0)]
    counts = [c for _i, c, _l in days]
    peak = max(1, max(counts))
    total, active, n_days = sum(counts), sum(1 for c in counts if c), len(days)

    # ── weeks across, weekdays down ──────────────────────────────────────
    first = _d(days[0][0])
    origin = first - datetime.timedelta(days=(first.weekday() + 1) % 7)   # Sunday on or before
    def week_of(dt):
        return (dt - origin).days // 7
    n_weeks = week_of(_d(days[-1][0])) + 1
    live = [False] * n_weeks
    for iso, count, _l in days:
        if count > 0:
            live[week_of(_d(iso))] = True
    xs, widths, gaps = _layout(live)
    rh = (FY1 - FY0) / float(ROWS)
    in_gap = set()
    for a, b, _x, _w in gaps:
        in_gap.update(range(a, b))

    stars, by_month = [], {}
    for iso, count, _lvl in days:
        if count <= 0:
            continue
        dt = _d(iso)
        wk = week_of(dt)
        # Jittered inside its own cell. Without this, stars that share a week or
        # a weekday sit on exact rows and columns, and the figures joining them
        # come out as right angles — a grid, not a sky. The offset is derived
        # from the date, so it is the same on every rebuild, and it never leaves
        # the day's own cell: the week and weekday stay readable.
        h = 0
        for ch in iso:
            h = (h * 131 + ord(ch)) & 0xFFFFFF
        jx = ((h & 0xFF) / 255.0 - 0.5) * 0.52
        jy = (((h >> 8) & 0xFF) / 255.0 - 0.5) * 0.54
        cx = xs[wk] + widths[wk] * (0.5 + jx)
        cy = FY0 + ((dt.weekday() + 1) % 7 + 0.5 + jy) * rh
        mag = (count / float(peak)) ** 0.55        # a root scale, so a small day still shows
        by_month.setdefault(iso[:7], []).append(len(stars))
        stars.append({"iso": iso, "n": count, "x": cx, "y": cy, "mag": mag,
                      "r": 1.6 + mag * 5.4})

    def at(x):                                     # when the sweep reaches an x
        return SWEEP_FROM + ((x - FX0) / (FX1 - FX0)) * (SWEEP_TO - SWEEP_FROM)

    css = ["@keyframes blip{0%,100%{opacity:1}50%{opacity:.25}}",
           ".blip{animation:blip 1.6s steps(1,end) infinite}",
           ".st{transform-box:fill-box;transform-origin:center}"]

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="Every day of work as a printed star chart: %d '
           'contributions across %d active days out of %d, each star a day placed by its week '
           'and weekday, brightness by commit count, brightest %d">'
           % (W, H, W, H, total, active, n_days, peak),
           "<title>Commit Activity</title>",
           '<defs><pattern id="cg" width="26" height="26" patternUnits="userSpaceOnUse">'
           '<circle cx="1.5" cy="1.5" r="1" fill="%s"/></pattern>__STYLE__</defs>' % GRID,
           '<rect width="%d" height="%d" fill="%s"/>' % (W, H, SKY),
           '<rect width="%d" height="%d" fill="url(#cg)"/>' % (W, H)]

    out.append(_txt(48, 44, "COMMIT ACTIVITY", 14, INK, "800", "start", "3.4"))
    out.append(_txt(W - 66, 44, "LIVE · REBUILT DAILY", 12.5, FAINT, "600", "end", "2.2"))
    out.append('<circle cx="%d" cy="40" r="5" fill="%s" class="blip"/>' % (W - 48, TEAMIST))
    out.append('<path d="M48,58 H%d" stroke="%s" stroke-width="1.4" fill="none"/>' % (W - 48, RULE))
    out.append(_txt(48, 78, "EVERY ACTIVE DAY IS A STAR · ACROSS IS THE WEEK, DOWN IS THE "
                            "WEEKDAY, BRIGHTER IS MORE", 10.5, MUTED, "600", "start", "1.5"))

    # ── the plate ────────────────────────────────────────────────────────
    out.append('<rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" rx="4" fill="%s" '
               'stroke="%s" stroke-width="1.3"/>'
               % (FX0 - 46, FY0 - 22, (FX1 - FX0) + 68, (FY1 - FY0) + 44, CHART, RULE))
    for r in range(ROWS + 1):
        y = FY0 + r * rh
        out.append('<path d="M%.0f,%.1f H%.0f" stroke="%s" stroke-width="0.9"/>'
                   % (FX0 - 30, y, FX1 + 14, RULING))
    for wk in range(0, n_weeks, 4):                # right-ascension rulings
        if wk in in_gap:
            continue
        out.append('<path d="M%.1f,%.0f V%.0f" stroke="%s" stroke-width="0.9" '
                   'stroke-dasharray="2 5"/>' % (xs[wk], FY0 - 6, FY1 + 6, RULING))
    for r in range(ROWS):
        out.append(_txt(FX0 - 36, FY0 + (r + 0.5) * rh + 3, DOW[r], 7.5, FAINT,
                        "700", "end", "0.8"))

    # ── the breaks, each labelled with what it stands for ────────────────
    for a, b, gx, gw in gaps:
        out.append('<rect x="%.1f" y="%.0f" width="%.1f" height="%.0f" fill="%s"/>'
                   % (gx + 1, FY0 - 8, gw - 2, (FY1 - FY0) + 16, CHART))
        for off in (gw * 0.34, gw * 0.66):
            out.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.1"/>'
                       % (_zig(gx + off, FY0 - 6, FY1 + 6), _mix(RULE, INK, 0.15)))
        out.append(_txt(gx + gw / 2.0, FY1 + 34, "%d WEEKS" % (b - a), 7.5,
                        _mix(FAINT, INK, 0.1), "700", "middle", "0.8"))
        out.append(_txt(gx + gw / 2.0, FY1 + 46, "NO WORK", 7.5,
                        _mix(FAINT, INK, 0.1), "700", "middle", "0.8"))

    # ── constellations: one figure per month, drawn as its last star lights
    for mkey in sorted(by_month):
        idxs = by_month[mkey]
        pts = [(stars[i]["x"], stars[i]["y"]) for i in idxs]
        lit_last = max(at(p[0]) for p in pts)
        for a, b in _mst(pts):
            x1, y1 = pts[a]
            x2, y2 = pts[b]
            cls = "cl%d" % len(css)
            css.append(_kf(cls, "0%%,%.2f%%{stroke-dashoffset:1}%.2f%%,100%%{stroke-dashoffset:0}"
                           % (lit_last, min(99.0, lit_last + 4.0))))
            css.append("." + cls + "{stroke-dasharray:1;stroke-dashoffset:1;animation:" + cls
                       + " " + "%.1f" % DUR + "s linear infinite}")
            out.append('<path class="%s" pathLength="1" d="M%.1f,%.1f L%.1f,%.1f" fill="none" '
                       'stroke="%s" stroke-width="1.1" stroke-linecap="round"/>'
                       % (cls, x1, y1, x2, y2, _mix(RULING, INK, 0.42)))
        cxs = sum(p[0] for p in pts) / len(pts)
        top = min(p[1] for p in pts)
        cls = "ml%d" % len(css)
        css.append(_kf(cls, "0%%,%.2f%%{opacity:0}%.2f%%,100%%{opacity:1}"
                       % (lit_last + 2.0, min(99.0, lit_last + 6.0))))
        css.append("." + cls + "{animation:" + cls + " " + "%.1f" % DUR + "s linear infinite}")
        out.append(_txt(max(FX0 + 20, min(FX1 - 20, cxs)), top - 11,
                        "%s %s" % (MONTHS[int(mkey[5:7]) - 1], mkey[2:4]), 7.5,
                        _mix(FAINT, INK, 0.3), "700", "middle", "1.4", cls))

    # ── the stars ────────────────────────────────────────────────────────
    for i, s in enumerate(stars):
        lit = at(s["x"])
        css.append(_kf("s%d" % i, "0%%,%.2f%%{opacity:0;transform:scale(.3)}"
                                  "%.2f%%,100%%{opacity:1;transform:scale(1)}"
                       % (max(0.0, lit - 0.6), min(99.5, lit + 1.4))))
        css.append(".s%d{animation:s%d " % (i, i) + "%.1f" % DUR + "s ease-out infinite}")
        ink = _mix(INK_2, INK, s["mag"])
        out.append('<g class="st s%d">' % i)
        if s["r"] > 4.2:                           # a chart marks its bright stars
            sp = s["r"] * 2.5
            out.append('  <path d="M%.1f,%.1f v%.1f M%.1f,%.1f h%.1f" stroke="%s" '
                       'stroke-width="0.9" stroke-linecap="round"/>'
                       % (s["x"], s["y"] - sp, sp * 2, s["x"] - sp, s["y"], sp * 2,
                          _mix(ink, CHART, 0.45)))
        out.append('  <circle cx="%.1f" cy="%.1f" r="%.2f" fill="%s"/>'
                   % (s["x"], s["y"], s["r"], ink))
        out.append("</g>")

    # ── the brightest star, ringed and named above the plate ─────────────
    # No leader down to it: the ring identifies it, and a line dropped through
    # the column would be drawn straight over the other stars in that week.
    if stars:
        b = max(stars, key=lambda s: s["n"])
        lit = at(b["x"])
        css.append(_kf("bn", "0%%,%.2f%%{opacity:0}%.2f%%,100%%{opacity:1}"
                       % (lit + 1.0, min(99.0, lit + 5.0))))
        css.append(".bn{animation:bn " + "%.1f" % DUR + "s linear infinite}")
        lab = "BRIGHTEST · %d ON %s" % (b["n"], _when(b["iso"]))
        lx = max(FX0 + len(lab) * 2.6, min(FX1 - len(lab) * 2.6, b["x"]))
        out.append('<g class="bn">')
        out.append("  " + '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" '
                          'stroke-width="1.2"/>' % (b["x"], b["y"], b["r"] + 5.0, CRIMSON))
        out.append("  " + _txt(lx, FY0 - 30, lab, 8.5, CRIMSON, "800", "middle", "1.1"))
        out.append("</g>")

    # ── the telescope, sweeping once across the plate ────────────────────
    css.append(_kf("sweep", "0%%,%.0f%%{transform:translateX(0)}%.0f%%,100%%"
                            "{transform:translateX(%.1fpx)}"
                   % (SWEEP_FROM, SWEEP_TO, FX1 - FX0)))
    css.append(".sw{animation:sweep " + "%.1f" % DUR + "s linear infinite}")
    out.append('<g class="sw">')
    out.append('  <path d="M%.1f,%.0f V%.0f" stroke="%s" stroke-width="1.2" '
               'stroke-dasharray="3 4"/>' % (FX0, FY0 - 14, FY1 + 14, _mix(CRIMSON, CHART, 0.3)))
    out.append('  <path d="M%.1f,%.0f l-5,-8 h10 Z" fill="%s"/>' % (FX0, FY0 - 14, CRIMSON))
    out.append('  <path d="M%.1f,%.0f l-5,8 h10 Z" fill="%s"/>' % (FX0, FY1 + 14, CRIMSON))
    out.append("</g>")

    # ── months along the foot, skipping anything inside a break ──────────
    shown = -999.0
    for iso, _c, _l in days:
        if iso[8:10] != "01":
            continue
        wk = week_of(_d(iso))
        if wk in in_gap:
            continue
        x = xs[wk] + widths[wk] * 0.5
        if x - shown < 44:
            continue
        shown = x
        out.append(_txt(x, FY1 + 34, MONTHS[int(iso[5:7]) - 1]
                        + ("" if iso[5:7] != "01" else " " + iso[2:4]),
                        8.5, FAINT, "600", "middle", "1.1"))

    # ── totals, with the magnitude key beside them ───────────────────────
    out.append('<path d="M48,%d H%d" stroke="%s" stroke-width="1.4" fill="none"/>'
               % (H - 50, W - 48, RULE))
    span = "%s – %s" % (_when(days[0][0]), _when(days[-1][0]))
    for k, (lbl, val) in enumerate((("CONTRIBUTIONS", total),
                                    ("ACTIVE DAYS", "%d / %d" % (active, n_days)),
                                    ("BRIGHTEST", peak))):
        x = 48 + k * 205
        out.append(_txt(x, H - 26, lbl, 9, FAINT, "700", "start", "1.6"))
        out.append(_txt(x + 112, H - 26, str(val), 11, INK, "800", "start", "0.6"))
    out.append(_txt(48, H - 8, "CHARTED", 9, FAINT, "700", "start", "1.6"))
    out.append(_txt(160, H - 8, span, 11, INK, "800", "start", "0.6"))

    kx = 760
    out.append(_txt(kx, H - 26, "MAGNITUDE", 9, FAINT, "700", "start", "1.6"))
    for k, val in enumerate(sorted({1, max(2, peak // 8), max(3, peak // 3), peak})):
        cx = kx + 106 + k * 82
        rr = 1.6 + (val / float(peak)) ** 0.55 * 5.4
        out.append('<circle cx="%.1f" cy="%.1f" r="%.2f" fill="%s"/>'
                   % (cx, H - 30, rr, _mix(INK_2, INK, (val / float(peak)) ** 0.55)))
        out.append(_txt(cx + 12, H - 26, str(val), 10, MUTED, "700", "start", "0.6"))
    out.append(_txt(W - 48, H - 8, "GITHUB.COM/AHMADMALIK1376", 9, FAINT, "600", "end", "1.5"))
    out.append("</svg>")

    svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote %s (%d stars over %d days, %d figures, %d break(s), brightest %d, %d KB)"
          % (path, len(stars), n_days, len(by_month), len(gaps), peak, len(svg) // 1024))
    return path


if __name__ == "__main__":
    import json
    import sys
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    build([(d["date"], d["count"], d["level"]) for d in data["days"]])
