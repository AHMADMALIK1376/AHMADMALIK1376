# -*- coding: utf-8 -*-
"""
The tech arsenal, assembled by a pick-and-place machine.

A gantry runs over an empty board. For each of the thirty tools it drops to the
feed tape on the left, picks the next chip, carries it across, and seats it in
its socket. The board fills up as it works, then the loop starts over.

This is how a real circuit board is populated, which is the point: the rest of
the profile is already drawn on a board, so the section that lists the tools may
as well be the machine that puts them there.

The marks are single paths from Simple Icons, published under CC0, baked into
logos.py. Nothing is fetched at render time. The previous version of this
section pulled from skillicons.dev and img.shields.io, twelve requests that
GitHub's image proxy had to make on every page view.

Each chip is defined once in <defs> and referenced three times with <use>: on
the tape, in the gantry's grip, and in its socket. Ninety copies of the path
data would otherwise make the file several hundred kilobytes.

Four chips carry letters rather than a mark. Simple Icons dropped Playwright,
AWS, Oracle and Azure at the trademark owners' request, and approximating
someone's logo by hand is worse than not drawing it.

House style: solid fills, no gradients, no filters.
"""
import logos

AEGEAN, CORAL = "#0077C8", "#F88379"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
SKY = "#F2EDE6"
GRID = "#E6DBCA"
TRACE = "#E1D5C2"
TRACE_D = "#CDBEA6"
BOARD = "#EDE5D8"
STEEL = "#B9AC97"
INK = "#2E2A24"
MUTED = "#7D7266"
FAINT = "#A2988A"
RULE = "#D9D0C1"
CARD = "#FBF7F0"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# label, icon slug (None draws letters), brand colour, letters, short label
GROUPS = [
    ("LANGUAGES", AEGEAN, [
        ("Python", "python", "#3776AB", "Py"),
        ("TypeScript", "typescript", "#3178C6", "Ts"),
        ("JavaScript", "javascript", "#F7DF1E", "Js"),
        ("Java", "openjdk", "#437291", "Ja"),
        ("C++", "cplusplus", "#00599C", "C+"),
        ("HTML5", "html5", "#E34F26", "Ht"),
        ("CSS", "css", "#663399", "Cs"),
        ("SQL", None, "#4479A1", "SQL"),
    ]),
    ("BACKEND", TEAMIST, [
        ("Node.js", "nodedotjs", "#5FA04E", "No"),
        ("Express", "express", "#4A4A4A", "Ex"),
        ("FastAPI", "fastapi", "#009688", "Fa"),
        ("Playwright", None, "#2EAD33", "Pw"),
        ("BeautifulSoup", None, "#8E6C3F", "Bs", "Soup"),
        ("Uvicorn", None, "#C2543C", "Uv"),
    ]),
    ("FRONTEND", CORAL, [
        ("React", "react", "#3AA8C1", "Re"),
        ("Tailwind", "tailwindcss", "#0891A8", "Tw"),
        ("Vite", "vite", "#646CFF", "Vi"),
        ("Canvas API", None, "#C2681F", "Cv", "Canvas"),
    ]),
    ("DATABASES", CRIMSON, [
        ("MongoDB", "mongodb", "#47A248", "Mg"),
        ("PostgreSQL", "postgresql", "#4169E1", "Pg", "Postgres"),
        ("MySQL", "mysql", "#4479A1", "My"),
        ("Firebase", "firebase", "#DD8B00", "Fb"),
        ("Oracle", None, "#C74634", "Or"),
    ]),
    ("CLOUD & OPS", BROWN, [
        ("Google Cloud", "googlecloud", "#4285F4", "Gc", "GCP"),
        ("AWS", None, "#D6820B", "AWS"),
        ("Docker", "docker", "#2496ED", "Dk"),
        ("Git", "git", "#F05032", "Gi"),
        ("Linux", "linux", "#9A7B14", "Lx"),
        ("WSL 2", None, "#0078D4", "WSL"),
        ("n8n", "n8n", "#EA4B71", "N8"),
    ]),
]

W, H = 1240, 560
DUR = 20.0                 # one full pass over the board
PLACE_END = 85.0           # the rest of the timeline holds the finished board

CHIP = 46
SLOT_P = 66                # socket to socket across a row
ROW_P = 68                 # row to row down the board
SLOT_X0 = 404
BOARD_Y0 = 176             # top edge of the first row of chips

RAIL_L, RAIL_R = 84, 1196
FEED_X, FEED_Y = 140, 199  # where the gantry picks, centre of the top chip
FEED_P = 58                # chip pitch on the tape
DIP = 13                   # how far the nozzle drops to pick and to seat


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _txt(x, y, s, size, fill, weight="700", anchor="start", ls="0"):
    return ('<text x="%s" y="%s" font-family="%s" font-size="%s" font-weight="%s" fill="%s" '
            'text-anchor="%s" letter-spacing="%s">%s</text>'
            % (x, y, MONO, size, weight, fill, anchor, ls, _esc(s)))


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(t):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(v)))) for v in t)


def _mix(a, b, t):
    """Blend two colours to a flat hex, so there is no alpha anywhere."""
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(ra[i] + (rb[i] - ra[i]) * t for i in range(3)))


def _lum(h):
    out = []
    for v in _rgb(h):
        v = v / 255.0
        out.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def _readable(brand, backdrop):
    """Keep a mark its own colour, but dark enough to read on its chip.

    JavaScript yellow and Linux yellow all but vanish on cream at full strength,
    so walk them toward the ink until they clear a contrast floor.
    """
    colour = brand
    for _ in range(14):
        l1, l2 = _lum(colour), _lum(backdrop)
        hi, lo = max(l1, l2), min(l1, l2)
        if (hi + 0.05) / (lo + 0.05) >= 3.1:
            break
        colour = _mix(colour, INK, 0.16)
    return colour


def _kf(name, stops):
    """A keyframes rule from (percent, declarations) pairs.

    Built by concatenation rather than formatting, because the braces and the
    percent signs in CSS collide with Python's own formatting.
    """
    body = "".join("%.3f" % p + "%{" + css + "}" for p, css in stops)
    return "@keyframes " + name + "{" + body + "}"


def _flat():
    """Every chip in placement order, with where it comes to rest."""
    out = []
    for gi, (label, accent, items) in enumerate(GROUPS):
        for k, item in enumerate(items):
            name, slug, brand, letters = item[:4]
            short = item[4] if len(item) > 4 else name
            out.append({
                "name": name, "slug": slug, "brand": brand, "letters": letters,
                "short": short, "accent": accent, "group": gi,
                "x": SLOT_X0 + k * SLOT_P,
                "y": BOARD_Y0 + gi * ROW_P,
            })
    return out


def arsenal(path="assets/assembly.svg"):
    chips = _flat()
    n = len(chips)
    span = PLACE_END / float(n)          # one pick-and-place cycle

    css = []
    defs = ['<pattern id="ag" width="26" height="26" patternUnits="userSpaceOnUse">'
            '<circle cx="1.5" cy="1.5" r="1" fill="%s"/></pattern>' % GRID,
            '<clipPath id="feedwin"><rect x="%d" y="%d" width="%d" height="%d" rx="6"/></clipPath>'
            % (FEED_X - 30, FEED_Y - 26, 60, FEED_P * 3 + 46)]

    # ── one definition per chip, used on the tape, in the grip and in its socket
    for i, c in enumerate(chips):
        tint = _mix(CARD, c["brand"], 0.12)
        mark = _readable(c["brand"], tint)
        body = ['<g id="c%d">' % i,
                '<rect width="%d" height="%d" rx="9" fill="%s" stroke="%s" stroke-width="1.3"/>'
                % (CHIP, CHIP, tint, _mix(RULE, c["brand"], 0.3))]
        d = logos.ICONS.get(c["slug"]) if c["slug"] else None
        if d:
            s = 26.0 / 24.0
            off = (CHIP - 26) / 2.0
            body.append('<g transform="translate(%.2f,%.2f) scale(%.4f)">'
                        '<path d="%s" fill="%s"/></g>' % (off, off, s, d, mark))
        else:
            size = 17 if len(c["letters"]) < 3 else 12.5
            body.append(_txt(CHIP / 2.0, CHIP / 2.0 + 6, c["letters"], size, mark,
                             "800", "middle", "0"))
        body.append("</g>")
        defs.append("".join(body))

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="Tech arsenal: a pick and place machine seating thirty '
           'tools onto a board, grouped by languages, backend, frontend, databases, cloud '
           'and operations">' % (W, H, W, H),
           "<title>Tech Arsenal</title>",
           "<defs>" + "".join(defs) + "__STYLE__</defs>",
           '<rect width="%d" height="%d" fill="%s"/>' % (W, H, SKY),
           '<rect width="%d" height="%d" fill="url(#ag)"/>' % (W, H)]

    # ── header ───────────────────────────────────────────────────────────
    out.append(_txt(48, 46, "TECH ARSENAL", 13, INK, "800", "start", "3.4"))
    out.append(_txt(W - 48, 46, "%d TOOLS · %d GROUPS" % (n, len(GROUPS)),
                    12, FAINT, "600", "end", "2.2"))
    out.append('<path d="M48,60 H%d" stroke="%s" stroke-width="1.4" fill="none"/>' % (W - 48, RULE))
    out.append(_txt(48, 78, "PICK AND PLACE · EVERY TOOL SEATED ON THE BOARD",
                    9.5, MUTED, "600", "start", "1.8"))

    # ── the board and its empty sockets ──────────────────────────────────
    out.append('<rect x="296" y="158" width="900" height="354" rx="14" fill="%s" '
               'stroke="%s" stroke-width="1.4"/>' % (BOARD, RULE))
    for gi, (label, accent, items) in enumerate(GROUPS):
        y = BOARD_Y0 + gi * ROW_P
        out.append('<rect x="312" y="%d" width="4" height="%d" rx="2" fill="%s"/>'
                   % (y + 6, CHIP - 12, accent))
        out.append(_txt(324, y + 20, label, 9.5, INK, "800", "start", "1.4"))
        out.append(_txt(324, y + 34, "%d" % len(items), 8.5, FAINT, "600", "start", "1"))
        for k, item in enumerate(items):
            x = SLOT_X0 + k * SLOT_P
            short = item[4] if len(item) > 4 else item[0]
            out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="9" fill="none" '
                       'stroke="%s" stroke-width="1.3" stroke-dasharray="4 4"/>'
                       % (x, y, CHIP, CHIP, STEEL))
            out.append(_txt(x + CHIP / 2.0, y + CHIP + 12, short,
                            6.9 if len(short) <= 10 else 6.2, MUTED, "700", "middle", "0.2"))

    # Every group holds a different number of tools, so the rows end ragged and
    # the right of the board sits bare. Each row is run out to a via near the
    # edge, the way a real board fans its signals off to a connector.
    for gi, (label, accent, items) in enumerate(GROUPS):
        cy = BOARD_Y0 + gi * ROW_P + CHIP / 2.0
        x0 = SLOT_X0 + len(items) * SLOT_P - (SLOT_P - CHIP) + 16
        if 1150 - x0 < 90:
            continue
        out.append('<path d="M%.1f,%.1f H%.1f L%.1f,%.1f H1150" fill="none" stroke="%s" '
                   'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
                   % (x0, cy, 1150 - 58, 1150 - 34, cy - 24, TRACE_D))
        for vx, vy in ((x0, cy), (1150, cy - 24)):
            out.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s"/>' % (vx, vy, STEEL))
            out.append('<circle cx="%.1f" cy="%.1f" r="1.7" fill="%s"/>' % (vx, vy, BOARD))

    # mounting holes, silkscreen only
    for hx in (316, 1176):
        for hy in (176, 494):
            out.append('<circle cx="%d" cy="%d" r="5.5" fill="none" stroke="%s" '
                       'stroke-width="1.6"/>' % (hx, hy, STEEL))
            out.append('<circle cx="%d" cy="%d" r="1.6" fill="%s"/>' % (hx, hy, STEEL))

    # ── feed tape ────────────────────────────────────────────────────────
    out.append(_txt(FEED_X, 140, "FEED", 9, FAINT, "800", "middle", "2"))
    out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="8" fill="%s" stroke="%s" '
               'stroke-width="1.4"/>' % (FEED_X - 34, FEED_Y - 30, 68, FEED_P * 3 + 54,
                                         BOARD, RULE))
    # sprocket holes down one edge, so it reads as tape rather than a list
    holes = "".join("M%d,%dh0.1" % (FEED_X - 27, FEED_Y - 14 + j * 16) for j in range(12))
    out.append('<path d="%s" stroke="%s" stroke-width="3" stroke-linecap="round" '
               'fill="none"/>' % (holes, STEEL))
    out.append('<g clip-path="url(#feedwin)"><g class="strip">')
    for i in range(n):
        out.append('  <use href="#c%d" x="%d" y="%d"/>'
                   % (i, FEED_X - CHIP / 2, FEED_Y - CHIP / 2 + i * FEED_P))
    out.append("</g></g>")

    css.append(_kf("strip", [(0.0, "transform:translateY(0)")] + [
        stop for i in range(n) for stop in (
            (i * span + span * 0.22, "transform:translateY(" + "%d" % (-i * FEED_P) + "px)"),
            (i * span + span * 0.34, "transform:translateY(" + "%d" % (-(i + 1) * FEED_P) + "px)"),
        )] + [(100.0, "transform:translateY(" + "%d" % (-n * FEED_P) + "px)")]))
    css.append(".strip{animation:strip " + "%.1f" % DUR + "s linear infinite}")

    # ── seated chips, each appearing as the head lets go ─────────────────
    for i, c in enumerate(chips):
        rel = i * span + span * 0.78
        css.append(_kf("seat%d" % i, [
            (0.0, "opacity:0"), (max(0.0, rel - 0.01), "opacity:0"),
            (rel, "opacity:1"), (100.0, "opacity:1")]))
        css.append(".seat%d{animation:seat%d " % (i, i) + "%.1f" % DUR + "s linear infinite}")
        out.append('<use class="seat%d" href="#c%d" x="%d" y="%d"/>'
                   % (i, i, c["x"], c["y"]))

    # ── the gantry ───────────────────────────────────────────────────────
    # Crossbeam moves in Y, the head rides it in X, the nozzle dips in Z. Each
    # sits in its own group: a CSS transform overrides a transform attribute on
    # the same element, so the three motions have to nest rather than share.
    for rail in (RAIL_L, RAIL_R):
        out.append('<rect x="%d" y="150" width="5" height="370" rx="2.5" fill="%s"/>'
                   % (rail - 2, STEEL))

    beam, head, noz = [], [], []
    for i, c in enumerate(chips):
        c0 = i * span
        cx = c["x"] + CHIP / 2.0
        cy = c["y"] + CHIP / 2.0
        beam += [(c0, "transform:translateY(" + "%.1f" % FEED_Y + "px)"),
                 (c0 + span * 0.25, "transform:translateY(" + "%.1f" % FEED_Y + "px)"),
                 (c0 + span * 0.62, "transform:translateY(" + "%.1f" % cy + "px)"),
                 (c0 + span * 0.86, "transform:translateY(" + "%.1f" % cy + "px)")]
        head += [(c0, "transform:translateX(" + "%.1f" % FEED_X + "px)"),
                 (c0 + span * 0.25, "transform:translateX(" + "%.1f" % FEED_X + "px)"),
                 (c0 + span * 0.62, "transform:translateX(" + "%.1f" % cx + "px)"),
                 (c0 + span * 0.86, "transform:translateX(" + "%.1f" % cx + "px)")]
        noz += [(c0, "transform:translateY(0)"),
                (c0 + span * 0.08, "transform:translateY(" + "%d" % DIP + "px)"),
                (c0 + span * 0.20, "transform:translateY(0)"),
                (c0 + span * 0.64, "transform:translateY(0)"),
                (c0 + span * 0.72, "transform:translateY(" + "%d" % DIP + "px)"),
                (c0 + span * 0.84, "transform:translateY(0)")]
    beam.append((100.0, "transform:translateY(" + "%.1f" % FEED_Y + "px)"))
    head.append((100.0, "transform:translateX(" + "%.1f" % FEED_X + "px)"))
    noz.append((100.0, "transform:translateY(0)"))

    css.append(_kf("beam", beam))
    css.append(_kf("head", head))
    css.append(_kf("noz", noz))
    css.append(".beam{animation:beam " + "%.1f" % DUR + "s ease-in-out infinite}")
    css.append(".head{animation:head " + "%.1f" % DUR + "s ease-in-out infinite}")
    css.append(".noz{animation:noz " + "%.1f" % DUR + "s ease-in-out infinite}")

    out.append('<g class="beam">')
    out.append('  <rect x="%d" y="-3" width="%d" height="6" rx="3" fill="%s"/>'
               % (RAIL_L, RAIL_R - RAIL_L, STEEL))
    out.append('  <g class="head">')
    out.append('    <g class="noz">')
    out.append('      <rect x="-26" y="-21" width="52" height="26" rx="6" fill="%s" '
               'stroke="%s" stroke-width="1.6"/>' % (CARD, INK))
    out.append('      <rect x="-19" y="-16" width="38" height="6" rx="3" fill="%s"/>' % TRACE_D)
    out.append('      <rect x="-4" y="4" width="8" height="12" rx="2" fill="%s"/>' % INK)
    out.append('      <path d="M-9,16 H9 L5,22 H-5 Z" fill="%s"/>' % INK)
    for i in range(n):
        c0 = i * span
        css.append(_kf("grip%d" % i, [
            (0.0, "opacity:0"),
            (max(0.0, c0 + span * 0.13), "opacity:0"),
            (c0 + span * 0.15, "opacity:1"),
            (c0 + span * 0.76, "opacity:1"),
            (min(100.0, c0 + span * 0.78), "opacity:0"),
            (100.0, "opacity:0")]))
        css.append(".grip%d{animation:grip%d " % (i, i) + "%.1f" % DUR + "s linear infinite}")
        out.append('      <use class="grip%d" href="#c%d" x="%d" y="22"/>'
                   % (i, i, -CHIP / 2))
    out.append("    </g>")
    out.append("  </g>")
    out.append("</g>")

    # ── progress ─────────────────────────────────────────────────────────
    out.append(_txt(48, H - 47, "SEATING", 8.5, FAINT, "800", "start", "2"))
    out.append('<rect x="48" y="%d" width="%d" height="4" rx="2" fill="%s"/>'
               % (H - 38, W - 96, _mix(SKY, INK, 0.08)))
    out.append('<g transform="translate(48,%d)"><rect class="prog" width="%d" height="4" rx="2" '
               'fill="%s"/></g>' % (H - 38, W - 96, AEGEAN))
    css.append(_kf("prog", [(0.0, "transform:scaleX(0)"),
                            (PLACE_END, "transform:scaleX(1)"),
                            (100.0, "transform:scaleX(1)")]))
    css.append(".prog{transform-origin:0 0;animation:prog " + "%.1f" % DUR
               + "s linear infinite}")

    out.append('<path d="M48,%d H%d" stroke="%s" stroke-width="1.4" fill="none"/>'
               % (H - 26, W - 48, RULE))
    out.append(_txt(48, H - 10, "MARKS BY SIMPLE ICONS (CC0) · DRAWN IN, NOT FETCHED",
                    9.5, FAINT, "600", "start", "1.8"))
    out.append(_txt(W - 48, H - 10, "GITHUB.COM/AHMADMALIK1376", 9.5, FAINT, "600", "end", "1.6"))
    out.append("</svg>")

    svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote %s (%d chips, %.0fs loop, %d KB)"
          % (path, n, DUR, len(svg) // 1024))
    return path


if __name__ == "__main__":
    arsenal()
