# -*- coding: utf-8 -*-
"""
The language distribution drawn as a world map.

Every language is given territory in proportion to how many bytes of it the
account actually holds, so the language with the largest share covers the most
land. The share comes from the GitHub API, the same call that feeds the rest of
the profile, so the map cannot drift out of date.

The landmass grid is baked in below rather than fetched. It was rasterised once
from Natural Earth's 110m land polygons on an equirectangular projection, with
Antarctica cropped out because it is enormous, empty, and would swallow a large
share of the territory for nothing. Baking it in keeps the daily rebuild free of
any network call beyond the API itself.

House style, matching the rest of the profile art: solid fills, no gradients and
no filters.
"""
import base64

COLS, ROWS = 104, 46

# 104x46 land mask, one bit per cell, row-major. See the module docstring.
_MASK_B64 = (
    "AAAA////AGAAAYAAAAAAU/3//gCAAABgAAAAAP34H/wAAAgP+AwAAwD/vw/8ABAR////wI////uP"
    "+AD/H//////v///zx4cB////////D///w4cAB7///////w+f/4dAAAe//////7ACB//n4AAzv///"
    "//BgAAP///AAd//////4QAAB///wAD///////AAAAP//2AAf//////QAAAD//8AAH/nf///0AAAA"
    "//8AAHv/3///yAAAAP/+AABwv9///ogAAAB//AAAPgf///74AAAAP/gAAH8j///+YAAAAB/4AAB/"
    "/////gAAAAAfCAAA//////4AAAAABwgAAf//+P/+AAAAAAckAAH///h58AAAAAAD4AAB//7wceAA"
    "AAAAAHAAAf//4GDxAAAAAAATAAH//+AgsQAAAAAAD+AA///gMIGAAAAAAAf4AH//wABEAAAAAAAH"
    "/AAB/8AAzAAAAAAAB/4AA/8AAF8gAAAAAA//gAH/AABvPAAAAAAH/8AB/wAAMA4AAAAAB//AAP8A"
    "AAICIAAAAAP/gAD/AAAANAAAAAAD/4AB/2AAAPQAAAAAAf+AAf5AAAH+AAAAAAD/AAD8wAAH/gAA"
    "AAAB/gAA/EAAB/8AAAAAAfwAAPwAAAf/AAAAAAH8AAB4AAAH/wAAAAAB+AAAcAAABx8AAAAAAfAA"
    "AAAAAAAPAgAAAAHAAAAAAAAAAAIAAAADwAAAAAAAAAIEAAAAA4AAAAAAAAAADAAAAAOAAAAAAAAA"
    "AAAAAAADAAAAAAAAAAAAAAAAAYAAAAAAAAAAAA=="
)

AEGEAN, CORAL = "#0077C8", "#F88379"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
SKY = "#F2EDE6"
GRID = "#E6DBCA"        # dot grid, as on the introduction banner
TRACE = "#E1D5C2"       # routed track
TRACE_D = "#CDBEA6"     # vias and the travelling pulse
INK = "#2E2A24"
INK_2 = "#5E5349"
MUTED = "#7D7266"
FAINT = "#A2988A"
RULE = "#D9D0C1"
CARD = "#FBF7F0"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

WHEEL = [AEGEAN, CORAL, TEAMIST, CRIMSON, BROWN, INK_2]

PITCH = 9.6            # centre-to-centre spacing of one cell
TILE = 8.2             # drawn size, the remainder reads as the gap
MAP_X, MAP_Y = 121, 104

# Anchors keep each territory somewhere sensible instead of scattering it.
# Order is by share, largest first, so the biggest language starts on the
# biggest landmass.
_ANCHORS = [(10, 80), (8, 20), (25, 55), (30, 32), (33, 88), (2, 30)]


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _txt(x, y, s, size, fill, weight="700", anchor="start", ls="0", cls=None):
    return ('<text x="%s" y="%s" font-family="%s" font-size="%s" font-weight="%s" fill="%s" '
            'text-anchor="%s" letter-spacing="%s"%s>%s</text>'
            % (x, y, MONO, size, weight, fill, anchor, ls,
               (' class="%s"' % cls) if cls else "", _esc(s)))


def _human_bytes(n):
    for unit, div in (("MB", 1024 * 1024), ("KB", 1024)):
        if n >= div:
            return "%.2f %s" % (n / float(div), unit)
    return "%d B" % n


def land_cells():
    """Every (row, col) that is land, decoded from the baked-in mask."""
    raw = base64.b64decode(_MASK_B64)
    bits = []
    for byte in bytearray(raw):
        for k in range(7, -1, -1):
            bits.append((byte >> k) & 1)
    return [(i // COLS, i % COLS) for i, b in enumerate(bits[:ROWS * COLS]) if b]


def apportion(lang_bytes, n):
    """Whole cells per language, in proportion to bytes.

    Largest-remainder apportionment: floor every share, then hand the leftover
    cells to the largest fractions. Area has to come in whole cells, and this is
    the method that keeps the rounding error smallest and unbiased.
    """
    ranked = sorted(lang_bytes.items(), key=lambda kv: -kv[1])
    total = sum(lang_bytes.values())
    if not total or not ranked:
        return [], {}
    exact = [(name, b * float(n) / total) for name, b in ranked]
    quota = dict((name, max(1, int(v))) for name, v in exact)
    short = n - sum(quota.values())
    order_by_rem = sorted(((v - int(v), name) for name, v in exact), reverse=True)
    i = 0
    while short > 0 and order_by_rem:
        quota[order_by_rem[i % len(order_by_rem)][1]] += 1
        short -= 1
        i += 1
    while short < 0:                       # minimums overshot a tiny map
        for _, name in reversed(order_by_rem):
            if short == 0:
                break
            if quota[name] > 1:
                quota[name] -= 1
                short += 1
    return [nm for nm, _ in ranked], quota


def _dist(a, b):
    dc = abs(a[1] - b[1])
    dc = min(dc, COLS - dc)                # the map wraps at the date line
    return ((a[0] - b[0]) ** 2 + dc * dc) ** 0.5


def grow(land, order, quota):
    """Hand out cells so each language ends up with one compact territory.

    Every language grows outward from its own anchor at the same time, always
    taking the nearest cell it can reach. A language whose share outgrows the
    landmass it started on hops to the nearest free land and carries on, which
    is why the largest one spans more than one continent.
    """
    import heapq

    landset = set(land)
    seeds, taken = {}, []
    for i, name in enumerate(order):
        anchor = _ANCHORS[i] if i < len(_ANCHORS) else None
        free_now = landset - set(taken)
        if not free_now:
            break
        if anchor is not None:
            seed = min(free_now, key=lambda p: _dist(p, anchor))
        else:
            seed = max(free_now, key=lambda p: min(_dist(p, t) for t in taken))
        seeds[name] = seed
        taken.append(seed)

    def neigh(rc):
        r, c = rc
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (r + dr, (c + dc) % COLS)
            if p in landset:
                yield p

    owner, heaps, got = {}, {}, dict((n, 0) for n in order)
    for n in seeds:
        heaps[n] = [(0.0, seeds[n])]
    free = set(land)
    active = [n for n in order if quota.get(n, 0) > 0 and n in seeds]
    while active:
        for n in list(active):
            if got[n] >= quota[n]:
                active.remove(n)
                continue
            pick = None
            while heaps[n]:
                _, cell = heapq.heappop(heaps[n])
                if cell in free:
                    pick = cell
                    break
            if pick is None:
                if not free:
                    active.remove(n)
                    continue
                pick = min(free, key=lambda p: _dist(p, seeds[n]))
            free.discard(pick)
            owner[pick] = n
            got[n] += 1
            for nb in neigh(pick):
                if nb in free:
                    heapq.heappush(heaps[n], (_dist(nb, seeds[n]), nb))
    for cell in list(free):                # whatever rounding left over
        owner[cell] = order[0]
        got[order[0]] += 1
    return owner, got


def _ocean_traces(landset, limit=11):
    """Copper runs through open water, so the wiring never crosses land.

    Candidates are every long stretch of water on every other row; the picks are
    then spread out, because taking the longest run on each row alone stacks
    them all in the same ocean.
    """
    cands = []
    for r in range(2, ROWS - 2, 2):
        start = None
        for c in range(COLS + 1):
            water = c < COLS and (r, c) not in landset
            if water and start is None:
                start = c
            elif not water and start is not None:
                if c - start >= 12:
                    cands.append((r, start + 1, c - 1))
                start = None

    chosen = []
    while cands and len(chosen) < limit:
        best, best_score = None, -1.0
        for run in cands:
            r, c0, c1 = run
            span, mid = c1 - c0, (c0 + c1) / 2.0
            if not chosen:
                score = span
            else:
                gap = min(abs(r - cr) * 2.4 + abs(mid - (a + b) / 2.0)
                          for cr, a, b in chosen)
                score = gap + span * 0.22
            if score > best_score:
                best, best_score = run, score
        chosen.append(best)
        cands.remove(best)
    return chosen


def _route_clear(pts, landset):
    """True when no part of the polyline passes over land."""
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 4) + 1
        for k in range(steps + 1):
            x = x0 + (x1 - x0) * k / float(steps)
            y = y0 + (y1 - y0) * k / float(steps)
            if (int(round(y)), int(round(x)) % COLS) in landset:
                return False
    return True


def _routes(landset, limit=11):
    """Ocean runs turned into tracks that step a row via a 45 degree elbow.

    The introduction's traces run horizontally, break to a diagonal, then carry
    on; these do the same, but only where the row they step into is also open
    water. Anything that cannot bend cleanly stays a straight run.
    """
    out = []
    for (r, c0, c1) in _ocean_traces(landset, limit):
        span = c1 - c0
        bent = None
        for dr in (1, -1):
            r2 = r + dr
            if not (0 <= r2 < ROWS):
                continue
            for frac in (0.34, 0.5, 0.66):
                cm = c0 + int(span * frac)
                if cm + 1 >= c1:
                    continue
                pts = [(c0, r), (cm, r), (cm + 1, r2), (c1, r2)]
                if _route_clear(pts, landset):
                    bent = pts
                    break
            if bent:
                break
        out.append(bent or [(c0, r), (c1, r)])
    return out


def language_map(lang_bytes, repo_count=None, path="assets/lang-map.svg"):
    land = land_cells()
    landset = set(land)
    order, quota = apportion(lang_bytes, len(land))
    if not order:
        order, quota = ["No data"], {"No data": len(land)}
    owner, got = grow(land, order, quota)

    total = sum(lang_bytes.values()) or 1
    colour = dict((n, WHEEL[i % len(WHEEL)]) for i, n in enumerate(order))

    w = 1240
    map_w = COLS * PITCH
    map_h = ROWS * PITCH
    legend_y = MAP_Y + map_h + 40
    h = int(legend_y + 108)

    css = ["@keyframes pop{0%{opacity:0;transform:translateY(7px)}}",
           "@keyframes fade{0%{opacity:0}}",
           # backwards, not forwards: the keyframes only pin 0%, so the implicit
           # 100% is whatever the element already computes to. Holding opacity:0
           # on .t and filling forwards would leave every tile stuck invisible.
           ".t{animation:pop .5s ease-out backwards}",
           ".lg{animation:fade .6s ease-out both}"]
    for c in range(COLS):
        css.append(".k%d{animation-delay:%.3fs}" % (c, 0.25 + c * 0.007))

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="Language distribution as a world map, area by share">'
           % (w, h, w, h),
           "<title>Language Distribution</title>",
           '<defs><pattern id="dg" width="26" height="26" patternUnits="userSpaceOnUse">'
           '<circle cx="1.5" cy="1.5" r="1" fill="%s"/></pattern>__STYLE__</defs>' % GRID,
           '<rect width="%d" height="%d" fill="%s"/>' % (w, h, SKY)]

    # ── circuit substrate ────────────────────────────────────────────────
    # The same substrate as the introduction banner: a 26px pad grid, tracks
    # that break to a 45 degree diagonal and carry on, two-tone vias, and a
    # pulse running the first leg of a track. No ocean panel, so the board
    # reads right across the image the way it does up top.
    out.append('<rect width="%d" height="%d" fill="url(#dg)"/>' % (w, h))

    def px(cell):
        c, r = cell
        return (MAP_X + c * PITCH, MAP_Y + r * PITCH + PITCH / 2.0)

    for i, pts in enumerate(_routes(landset)):
        xy = [px(pt) for pt in pts]
        d = "M%.1f,%.1f " % xy[0] + " ".join("L%.1f,%.1f" % q for q in xy[1:])
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.6" '
                   'stroke-linecap="round" stroke-linejoin="round"/>' % (d, TRACE))
        for vx, vy in (xy[0], xy[-1]):
            out.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s"/>' % (vx, vy, TRACE_D))
            out.append('<circle cx="%.1f" cy="%.1f" r="1.7" fill="%s"/>' % (vx, vy, SKY))
        # the pulse rides the opening horizontal leg, as it does on the banner
        (x0, y0), (x1, _) = xy[0], xy[1]
        css.append(".pl%d{animation:pl%d %ds linear infinite;animation-delay:-%.1fs}"
                   % (i, i, 7 + i % 4, i * 1.6))
        css.append("@keyframes pl%d{0%%{transform:translateX(%.1fpx);opacity:0}"
                   "15%%,80%%{opacity:1}100%%{transform:translateX(%.1fpx);opacity:0}}"
                   % (i, x0, x1))
        out.append('<circle class="pl%d" cy="%.1f" r="3" fill="%s"/>' % (i, y0, TRACE_D))

    # ── territories ──────────────────────────────────────────────────────
    out.append("<g>")
    for (r, c) in land:
        nm = owner.get((r, c))
        out.append('<rect class="t k%d" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="1.7" '
                   'fill="%s"/>'
                   % (c, MAP_X + c * PITCH, MAP_Y + r * PITCH, TILE, TILE,
                      colour.get(nm, FAINT)))
    out.append("</g>")


    # ── header ───────────────────────────────────────────────────────────
    out.append(_txt(48, 52, "LANGUAGE DISTRIBUTION", 13, INK, "800", "start", "3.4"))
    meta = "%s ACROSS %s REPOS" % (_human_bytes(total), repo_count if repo_count else "ALL")
    out.append(_txt(w - 48, 52, meta.upper(), 12, FAINT, "600", "end", "2.2"))
    out.append('<path d="M48,70 H%d" stroke="%s" stroke-width="1.4" fill="none"/>' % (w - 48, RULE))
    out.append(_txt(48, 90, "TERRITORY IS PROPORTIONAL TO BYTES HELD", 9.5, MUTED, "600",
                    "start", "1.8"))
    out.append(_txt(w - 48, 90, "%d CELLS OF LAND" % len(land), 9.5, FAINT, "600", "end", "1.6"))

    # ── legend ───────────────────────────────────────────────────────────
    cols = min(len(order), 6)
    cell_w = (w - 96) / float(cols)
    for i, name in enumerate(order[:cols]):
        x = 48 + i * cell_w
        share = lang_bytes.get(name, 0) * 100.0 / total
        css.append(".l%d{animation-delay:%.2fs}" % (i, 0.9 + i * 0.07))
        out.append('<g class="lg l%d">' % i)
        out.append("  " + '<rect x="%.1f" y="%.1f" width="%.1f" height="62" rx="9" fill="%s" '
                          'stroke="%s" stroke-width="1.3"/>'
                          % (x, legend_y, cell_w - 12, CARD, RULE))
        out.append("  " + '<rect x="%.1f" y="%.1f" width="5" height="34" rx="2.5" fill="%s"/>'
                          % (x + 13, legend_y + 14, colour[name]))
        out.append("  " + _txt(x + 28, legend_y + 26, name, 11.5, INK, "700", "start", "0.4"))
        pct = "&lt;0.1%" if 0 < share < 0.05 else "%.1f%%" % share
        out.append("  " + ('<text x="%.1f" y="%.1f" font-family="%s" font-size="15" '
                           'font-weight="800" fill="%s" letter-spacing="0">%s</text>'
                           % (x + 28, legend_y + 46, MONO, colour[name], pct)))
        out.append("  " + _txt(x + cell_w - 24, legend_y + 46,
                               "%d" % got.get(name, 0), 9.5, FAINT, "600", "end", "0.6"))
        out.append("</g>")

    out.append('<path d="M48,%d H%d" stroke="%s" stroke-width="1.4" fill="none"/>'
               % (h - 34, w - 48, RULE))
    out.append(_txt(48, h - 14, "GENERATED FROM THE GITHUB API · REBUILT DAILY",
                    10, FAINT, "600", "start", "2"))
    out.append(_txt(w - 48, h - 14, "GITHUB.COM/AHMADMALIK1376", 10, FAINT, "600", "end", "1.6"))
    out.append("</svg>")

    svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote %s (%d languages over %d cells)" % (path, len(order), len(land)))
    return path


if __name__ == "__main__":
    import json
    import sys
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    language_map(data,
                 repo_count=int(sys.argv[2]) if len(sys.argv) > 2 else None,
                 path=sys.argv[3] if len(sys.argv) > 3 else "assets/lang-map.svg")
