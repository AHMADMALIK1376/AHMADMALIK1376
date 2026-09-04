# -*- coding: utf-8 -*-
"""
Two searches racing across the same warehouse floor, both run for real.

Nothing here is mimed. A* and Dijkstra are both executed in Python over the
floor plan below, and what plays back is the actual order in which each took
cells off its priority queue. The frontier you watch spread is the real one, it
stalls against the real racking, and the route each settles on really is the
shortest available.

Both routes are the same LENGTH — both are optimal — but not the same cells.
Where several shortest routes exist, each search returns whichever it reached
first, and here seven of sixty differ. The panel says so rather than claiming
the two agree.

They run on one shared clock, which is the entire point. A cell appears at a
time set by its position in its own search, scaled by the LONGER search — so
A* visibly finishes and sits there while Dijkstra is still flooding the floor.
Stating that A* is more efficient is easy; showing one finish while the other
grinds on is the thing worth building.

The two find routes of identical length. The only difference is that A* is told
roughly which way the goal lies, and Dijkstra is not.

Two implementation notes:

  - Expansion is bucketed into waves rather than given a keyframe per cell. Some
    five hundred cells with a rule each is a large stylesheet for something the
    eye reads as one advancing front; cells expanded at about the same moment
    share a class and appear together.
  - The rover's heading is unwrapped before it becomes CSS. Angles stepping from
    270 to 0 interpolate the long way round and the machine spins on the spot;
    accumulating the turns keeps every rotation short.

House style: solid fills, no gradients, no filters.
"""
import heapq
import math

AEGEAN, CORAL = "#0077C8", "#F88379"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
ARM, ARM_DK = "#F0C419", "#39332B"
SKY = "#F2EDE6"
GRID = "#E6DBCA"
FLOOR = "#FBF7F0"
INK = "#2E2A24"
INK_2 = "#5E5349"
MUTED = "#7D7266"
FAINT = "#A2988A"
RULE = "#D9D0C1"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

CELL = 17.0
COLS, ROWS = 60, 11
FX = 110.0
FY_A, FY_B = 128.0, 377.0
W, H = 1240, 634

DUR = 26.0
EXP_FROM, EXP_TO = 5.0, 62.0
DRIVE_FROM, DRIVE_TO = 68.0, 93.0
WAVES = 76

START, GOAL = (1, ROWS // 2), (COLS - 2, ROWS // 2)
# free-standing racks in staggered bays, the way a warehouse is actually laid
# out: cross-aisles both ways, so a detour is local rather than global. On a
# serpentine floor the heuristic is misled and A* has to search nearly all of
# it too, which makes for a true but unreadable picture.
BAY_X, BAY_Y, RACK_W, RACK_H, OFFSET, TOP = 12, 4, 9, 2, 6, 1


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _txt(x, y, s, size, fill, weight="700", anchor="start", ls="0", cls=None):
    return ('<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" font-weight="%s" '
            'fill="%s" text-anchor="%s" letter-spacing="%s"%s>%s</text>'
            % (x, y, MONO, size, weight, fill, anchor, ls,
               (' class="%s"' % cls) if cls else "", _esc(s)))


def _rr(x, y, w, h, r, fill, extra=""):
    return ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%s" fill="%s"%s/>'
            % (x, y, w, h, r, fill, (" " + extra) if extra else ""))


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return "#%02X%02X%02X" % tuple(
        max(0, min(255, int(round(ra[i] + (rb[i] - ra[i]) * t)))) for i in range(3))


def _kf(name, stops):
    return ("@keyframes " + name + "{"
            + "".join("%.2f" % p + "%{" + body + "}" for p, body in stops) + "}")


def build_grid():
    g = [[0] * COLS for _ in range(ROWS)]
    for by, r0 in enumerate(range(TOP, ROWS - 1, BAY_Y)):
        for c0 in range(3 + (OFFSET if by % 2 else 0), COLS - 3, BAY_X):
            for r in range(r0, min(ROWS, r0 + RACK_H)):
                for c in range(c0, min(COLS, c0 + RACK_W)):
                    g[r][c] = 1
    return g


def search(g, start, goal, heuristic=True):
    """A* with the heuristic on, Dijkstra with it off. Same code, same floor.

    Returns (path, expansion_order); the order is exactly what gets replayed.
    """
    def h(n):
        return abs(n[0] - goal[0]) + abs(n[1] - goal[1]) if heuristic else 0

    q = [(h(start), 0, start)]
    came, cost, seen, order = {}, {start: 0}, set(), []
    while q:
        _f, gc, cur = heapq.heappop(q)
        if cur in seen:
            continue
        seen.add(cur)
        order.append(cur)
        if cur == goal:
            break
        cx, cy = cur
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < COLS and 0 <= ny < ROWS) or g[ny][nx]:
                continue
            ng = gc + 1
            if ng < cost.get((nx, ny), 1 << 30):
                cost[(nx, ny)] = ng
                came[(nx, ny)] = cur
                heapq.heappush(q, (ng + h((nx, ny)), ng, (nx, ny)))
    path, node = [], goal
    while node in came:
        path.append(node)
        node = came[node]
    path.append(start)
    path.reverse()
    return path, order


def _floor_symbol(g):
    """Grid and racking, drawn once and placed on both floors."""
    s = ['<g id="floor">',
         '  ' + _rr(-6, -6, COLS * CELL + 12, ROWS * CELL + 12, 5, FLOOR,
                    'stroke="%s" stroke-width="1.3"' % RULE)]
    faint = _mix(FLOOR, INK, 0.055)
    for c in range(COLS + 1):
        s.append('  <path d="M%.1f,0 V%.1f" stroke="%s" stroke-width="0.55"/>'
                 % (c * CELL, ROWS * CELL, faint))
    for r in range(ROWS + 1):
        s.append('  <path d="M0,%.1f H%.1f" stroke="%s" stroke-width="0.55"/>'
                 % (r * CELL, COLS * CELL, faint))
    rack = _mix(BROWN, INK, 0.30)
    beam = _mix(BROWN, FLOOR, 0.42)
    for r in range(ROWS):
        for c in range(COLS):
            if not g[r][c]:
                continue
            s.append('  ' + _rr(c * CELL + 0.5, r * CELL + 0.5, CELL - 1, CELL - 1, 2, rack))
            s.append('  <path d="M%.1f,%.1f H%.1f" stroke="%s" stroke-width="0.9"/>'
                     % (c * CELL + 3, r * CELL + CELL / 2.0, c * CELL + CELL - 3, beam))
    s.append("</g>")
    return s


def _rover():
    """Centred on its own origin, so translate-then-rotate turns it in place
    instead of swinging it around the corner of the floor."""
    return ['<g id="rov">',
            '  <rect x="-7" y="-5.5" width="14" height="11" rx="2.5" fill="%s"/>' % ARM,
            '  <rect x="-7" y="-5.5" width="14" height="3" rx="1.5" fill="%s"/>'
            % _mix(ARM, INK, 0.22),
            '  <rect x="-5" y="-7.5" width="3.4" height="2" rx="1" fill="%s"/>' % ARM_DK,
            '  <rect x="1.6" y="-7.5" width="3.4" height="2" rx="1" fill="%s"/>' % ARM_DK,
            '  <rect x="-5" y="5.5" width="3.4" height="2" rx="1" fill="%s"/>' % ARM_DK,
            '  <rect x="1.6" y="5.5" width="3.4" height="2" rx="1" fill="%s"/>' % ARM_DK,
            '  <circle cx="0" cy="0" r="2.4" fill="%s"/>' % ARM_DK,
            '  <path d="M7,0 l-3.4,-2.6 v5.2 Z" fill="%s"/>' % CRIMSON,
            "</g>"]


def build(path_out="assets/pathfinder.svg"):
    g = build_grid()
    a_path, a_order = search(g, START, GOAL, heuristic=True)
    d_path, d_order = search(g, START, GOAL, heuristic=False)
    free = sum(1 for r in range(ROWS) for c in range(COLS) if not g[r][c])
    slowest = float(max(len(a_order), len(d_order)))

    def when(k):                                # one clock for both searches
        return EXP_FROM + (k / slowest) * (EXP_TO - EXP_FROM)

    css = ["@keyframes blip{0%,100%{opacity:1}50%{opacity:.25}}",
           ".blip{animation:blip 1.6s steps(1,end) infinite}"]
    for w in range(WAVES):
        at = EXP_FROM + (w / float(WAVES)) * (EXP_TO - EXP_FROM)
        css.append(_kf("w%d" % w, [(0.0, "opacity:0"), (max(0.0, at - 0.01), "opacity:0"),
                                   (at, "opacity:1"), (100.0, "opacity:1")]))
        css.append(".w%d{animation:w%d " % (w, w) + "%.1f" % DUR + "s linear infinite}")

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="A star and Dijkstra racing across the same warehouse floor: '
           'both find the same %d step route, A star by examining %d cells and Dijkstra %d, of '
           'a %d cell floor">'
           % (W, H, W, H, len(a_path) - 1, len(a_order), len(d_order), free),
           "<title>Two Ways to Find a Route</title>",
           '<defs><pattern id="pg" width="26" height="26" patternUnits="userSpaceOnUse">'
           '<circle cx="1.5" cy="1.5" r="1" fill="%s"/></pattern>' % GRID]
    out += _floor_symbol(g)
    out += _rover()
    out.append("__STYLE__</defs>")
    out.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, SKY))
    out.append('<rect width="%d" height="%d" fill="url(#pg)"/>' % (W, H))

    out.append(_txt(48, 44, "TWO WAYS TO FIND A ROUTE", 14, INK, "800", "start", "3.4"))
    out.append(_txt(W - 66, 44, "BOTH RUN FOR REAL", 12.5, FAINT, "600", "end", "2.2"))
    out.append('<circle cx="%d" cy="40" r="5" fill="%s" class="blip"/>' % (W - 48, TEAMIST))
    out.append('<path d="M48,58 H%d" stroke="%s" stroke-width="1.4" fill="none"/>' % (W - 48, RULE))
    out.append(_txt(48, 80, "SAME FLOOR · SAME START · SAME GOAL · ONE OF THEM KNOWS WHICH WAY "
                            "TO LOOK", 10.5, MUTED, "600", "start", "1.5"))

    for fy, order, pth, tint, name, sub in (
            (FY_A, a_order, a_path, AEGEAN, "A*",
             "GUIDED BY A HEURISTIC · PREFERS CELLS THAT LOOK CLOSER TO THE GOAL"),
            (FY_B, d_order, d_path, CORAL, "DIJKSTRA",
             "NO HEURISTIC · EXPANDS EVERY DIRECTION EQUALLY UNTIL IT ARRIVES")):
        out.append(_txt(48, fy - 30, name, 12, INK, "800", "start", "2.6"))
        out.append(_txt(48 + len(name) * 9 + 24, fy - 30, sub, 8.6, FAINT, "600", "start", "1.2"))
        out.append('<use href="#floor" x="%.0f" y="%.0f"/>' % (FX, fy))

        n = len(order)
        for i, (cx, cy) in enumerate(order):
            t = when(i)
            w = min(WAVES - 1, int(((t - EXP_FROM) / (EXP_TO - EXP_FROM)) * WAVES))
            shade = _mix(_mix(FLOOR, tint, 0.26), tint, (i / float(n)) * 0.5)
            out.append(_rr(FX + cx * CELL + 1, fy + cy * CELL + 1, CELL - 2, CELL - 2,
                           2, shade, 'class="w%d"' % w))

        # the route, drawn the moment that search actually finished
        done = when(n)
        d = "M" + " L".join("%.1f,%.1f" % (FX + (c + 0.5) * CELL, fy + (r + 0.5) * CELL)
                            for c, r in pth)
        cls = "rt%d" % int(fy)
        css.append(_kf(cls, [(0.0, "stroke-dashoffset:1"), (done, "stroke-dashoffset:1"),
                             (min(99.0, done + 5.0), "stroke-dashoffset:0"),
                             (100.0, "stroke-dashoffset:0")]))
        css.append("." + cls + "{stroke-dasharray:1;animation:" + cls + " "
                   + "%.1f" % DUR + "s linear infinite}")
        out.append('<path class="%s" pathLength="1" d="%s" fill="none" stroke="%s" '
                   'stroke-width="3.4" stroke-linejoin="round" stroke-linecap="round"/>'
                   % (cls, d, CRIMSON))

        # a badge stating what that search cost, the moment it stops
        bcls = "bd%d" % int(fy)
        css.append(_kf(bcls, [(0.0, "opacity:0"), (max(0.0, done + 0.5), "opacity:0"),
                              (min(99.0, done + 3.0), "opacity:1"), (100.0, "opacity:1")]))
        css.append("." + bcls + "{animation:" + bcls + " " + "%.1f" % DUR + "s linear infinite}")
        bx = FX + COLS * CELL + 10
        out.append('<g class="%s">' % bcls)
        out.append("  " + _txt(bx, fy + 62, "FOUND", 9, _mix(tint, INK, 0.3), "800", "start", "1.6"))
        out.append("  " + _txt(bx, fy + 82, "%d" % n, 20, INK, "800", "start", "-0.5"))
        out.append("  " + _txt(bx, fy + 96, "CELLS", 8, FAINT, "700", "start", "1.4"))
        out.append("  " + _txt(bx, fy + 116, "%d%% OF FLOOR" % round(100.0 * n / free), 8,
                               FAINT, "600", "start", "0.9"))
        out.append("</g>")

        for (cx, cy), col, lab in ((START, TEAMIST, "DOCK"), (GOAL, CRIMSON, "PICK")):
            x, y = FX + (cx + 0.5) * CELL, fy + (cy + 0.5) * CELL
            out.append('<circle cx="%.1f" cy="%.1f" r="7" fill="%s"/>' % (x, y, col))
            out.append('<circle cx="%.1f" cy="%.1f" r="2.8" fill="%s"/>' % (x, y, FLOOR))
            out.append(_txt(x, y - 12, lab, 7, _mix(col, INK, 0.35), "800", "middle", "1"))

    # ── the rover, running the route A* handed it ────────────────────────
    stops, ang = [], 0.0
    for i, (cx, cy) in enumerate(a_path):
        x, y = FX + (cx + 0.5) * CELL, FY_A + (cy + 0.5) * CELL
        if i + 1 < len(a_path):
            nx, ny = a_path[i + 1]
            want = math.degrees(math.atan2(ny - cy, nx - cx))
        else:
            want = ang
        while want - ang > 180:
            want -= 360
        while want - ang < -180:
            want += 360
        ang = want
        pct = DRIVE_FROM + (i / float(max(1, len(a_path) - 1))) * (DRIVE_TO - DRIVE_FROM)
        stops.append((pct, "transform:translate(%.1fpx,%.1fpx) rotate(%.1fdeg)" % (x, y, ang)))
    css.append(_kf("drive", [(0.0, stops[0][1]), (DRIVE_FROM - 0.01, stops[0][1])]
                   + stops + [(100.0, stops[-1][1])]))
    css.append(".drive{animation:drive " + "%.1f" % DUR + "s linear infinite}")
    css.append(_kf("show", [(0.0, "opacity:0"), (DRIVE_FROM - 0.01, "opacity:0"),
                            (DRIVE_FROM, "opacity:1"), (100.0, "opacity:1")]))
    css.append(".show{animation:show " + "%.1f" % DUR + "s linear infinite}")
    out.append('<g class="show"><g class="drive"><use href="#rov"/></g></g>')

    # ── what it all came to ──────────────────────────────────────────────
    out.append('<path d="M48,%d H%d" stroke="%s" stroke-width="1.4" fill="none"/>'
               % (H - 46, W - 48, RULE))
    ratio = len(d_order) / float(max(1, len(a_order)))
    same = a_path == d_path
    for k, (lab, val) in enumerate((("BOTH ROUTES", "%d STEPS" % (len(a_path) - 1)),
                                    ("BOTH OPTIMAL", "SAME" if same else "TIES DIFFER"),
                                    ("FLOOR", "%d CELLS" % free),
                                    ("A* SEARCHED", "%.1fx LESS" % ratio))):
        x = 48 + k * 296
        out.append(_txt(x, H - 26, lab, 8.6, FAINT, "700", "start", "1.5"))
        out.append(_txt(x + 146, H - 26, val, 11, INK, "800", "start", "0.6"))
    out.append(_txt(48, H - 8, "WHERE SEVERAL SHORTEST ROUTES EXIST EACH SEARCH RETURNS "
                               "WHICHEVER IT REACHED FIRST · BOTH ARE OPTIMAL · THE HEURISTIC "
                               "IS WHY ONE FINISHED SO MUCH SOONER",
                    9, FAINT, "600", "start", "1.3"))
    out.append("</svg>")

    svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
    with open(path_out, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote %s (route %d, A* %d cells, Dijkstra %d, floor %d, %.1fx, %d KB)"
          % (path_out, len(a_path) - 1, len(a_order), len(d_order), free, ratio,
             len(svg) // 1024))
    # Both must be OPTIMAL, which means equal length. They need not be the same
    # cells: where several shortest routes exist, each search returns whichever
    # it happened to reach first, and here 7 of 60 cells differ.
    assert len(a_path) == len(d_path), "one of the searches returned a non-optimal route"
    return path_out


if __name__ == "__main__":
    build()
