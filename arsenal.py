# -*- coding: utf-8 -*-
"""
The tech arsenal, assembled by a pick-and-place robot.

The feed tape stands on the right. A carriage rides a linear track and a
two-link arm swings off it, taking each part from the tape and seating it on the
board, working right to left across the sockets and then parking back over the
tape once the board is full.

Anything the GitHub API reports that is not already declared below is folded
into LANGUAGES automatically and marked with a dot, so it is clear which parts
came from the API rather than from this list. That is how the section keeps up
on its own when a new language turns up in a repository.

Parts are drawn as IC packages with pins rather than plain squares, since they
are being seated on a board.

Marks are single paths from Simple Icons, published under CC0, baked into
logos.py. Nothing is fetched at render time.

Playwright, AWS, Oracle and WSL carry letters instead of a mark: Simple Icons
dropped those at the trademark owners' request, and approximating someone's
logo by hand is worse than not drawing it.

House style: solid fills, no gradients, no filters.
"""
import logos

AEGEAN, CORAL = "#0077C8", "#F88379"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
VIOLET = "#7E6BC4"
SKY = "#F2EDE6"
GRID = "#E6DBCA"
TRACE_D = "#CDBEA6"
BOARD = "#EDE5D8"
STEEL = "#B9AC97"
ARM = "#F0C419"            # industrial yellow, as on a factory robot
ARM_DK = "#39332B"         # joints and housings
INK = "#2E2A24"
MUTED = "#7D7266"
FAINT = "#A2988A"
RULE = "#D9D0C1"
CARD = "#FBF7F0"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# name, icon slug (None draws letters), brand colour, letters, short label
GROUPS = [
    ("LANGUAGES", AEGEAN, [
        ("Python", "python", "#3776AB", "Py"),
        ("TypeScript", "typescript", "#3178C6", "Ts"),
        ("JavaScript", "javascript", "#F7DF1E", "Js"),
        ("Java", "openjdk", "#437291", "Ja"),
        ("C++", "cplusplus", "#00599C", "C+"),
        ("SQL", None, "#4479A1", "SQL"),
    ]),
    ("FRONTEND", CORAL, [
        ("React", "react", "#3AA8C1", "Re"),
        ("Tailwind", "tailwindcss", "#0891A8", "Tw"),
        ("Vite", "vite", "#646CFF", "Vi"),
        # markup and styling belong with the interface, not with the languages
        ("HTML5", "html5", "#E34F26", "Ht"),
        ("CSS", "css", "#663399", "Cs"),
        ("Canvas API", None, "#C2681F", "Cv", "Canvas"),
    ]),
    ("BACKEND", TEAMIST, [
        ("Node.js", "nodedotjs", "#5FA04E", "No"),
        ("Express", "express", "#4A4A4A", "Ex"),
        ("FastAPI", "fastapi", "#009688", "Fa"),
        ("Uvicorn", None, "#C2543C", "Uv"),
    ]),
    ("DATABASES", CRIMSON, [
        ("MongoDB", "mongodb", "#47A248", "Mg"),
        ("NoSQL", None, "#6E8F3F", "NoS"),
        ("PostgreSQL", "postgresql", "#4169E1", "Pg", "Postgres"),
        ("MySQL", "mysql", "#4479A1", "My"),
        ("Firebase", "firebase", "#DD8B00", "Fb"),
        ("Oracle", None, "#C74634", "Or"),
    ]),
    # Playwright drives a browser and BeautifulSoup parses pages. Neither is a
    # backend service, which is where both of them used to sit.
    ("AUTOMATION", VIOLET, [
        ("Playwright", None, "#2EAD33", "Pw"),
        ("BeautifulSoup", None, "#8E6C3F", "Bs", "Soup"),
        ("n8n", "n8n", "#EA4B71", "N8"),
    ]),
    ("CLOUD & OPS", BROWN, [
        ("Google Cloud", "googlecloud", "#4285F4", "Gc", "GCP"),
        ("AWS", None, "#D6820B", "AWS"),
        ("Docker", "docker", "#2496ED", "Dk"),
        ("Git", "git", "#F05032", "Gi"),
        ("Linux", "linux", "#9A7B14", "Lx"),
        ("WSL 2", None, "#0078D4", "WSL"),
    ]),
]

# GitHub's language names mapped to marks we hold, so a detected language
# arrives with its own logo wherever one exists.
LANG_SLUG = {"python": "python", "typescript": "typescript",
             "javascript": "javascript", "html": "html5", "css": "css",
             "java": "openjdk", "c++": "cplusplus"}
# API spellings for parts already on the board under a different name
LANG_ALIAS = {"html": "html5"}

W = 1240
DUR = 10.0                 # one full pass over the board
PLACE_END = 86.0           # the rest of the timeline rests over the tape

CHIP = 52
SLOT_P = 60
LABEL_W = 84
ROW_P = 74
BOARD_Y0 = 172
COL_LABEL_X = (48, 566)    # the two board columns
MAX_PER_ROW = 7

TRACK_Y = 104
FEED_X, FEED_Y = 1124, 198
FEED_P = 68
L1, L2 = 140.0, 105.0
CARRIAGE_OFF = 80.0        # the carriage parks this far right of its target
DIP = 14
# The gripper holds a part from above, so the part hangs this far below the
# wrist. The wrist has to aim that much high or every part lands low.
GRIP_DY = 5 + CHIP / 2.0


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
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(ra[i] + (rb[i] - ra[i]) * t for i in range(3)))


def _lum(h):
    out = []
    for v in _rgb(h):
        v = v / 255.0
        out.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def _readable(brand, backdrop):
    """Keep a mark its own colour, but dark enough to read on its package."""
    colour = brand
    for _ in range(14):
        hi, lo = max(_lum(colour), _lum(backdrop)), min(_lum(colour), _lum(backdrop))
        if (hi + 0.05) / (lo + 0.05) >= 3.1:
            break
        colour = _mix(colour, INK, 0.16)
    return colour


def _carriage_x(target_x):
    """The carriage parks right of what it reaches, and stays on the track."""
    return max(60.0, min(1200.0, target_x + CARRIAGE_OFF))


def _ik(sx, sy, tx, ty, l1, l2):
    """Shoulder and elbow angles that put the wrist on (tx, ty).

    Two-link solution. Of the two configurations that reach any given point,
    this takes the one that keeps the elbow below the rail; the other lifts it
    up over the track for a third of the sockets, which looks wrong on a machine
    hanging from an overhead rail.

    Reach is clamped to what the arm can do, so a target it cannot make becomes
    a full stretch rather than a maths error.
    """
    import math
    dx, dy = tx - sx, ty - sy
    d = math.hypot(dx, dy)
    d = max(abs(l1 - l2) + 0.01, min(l1 + l2 - 0.01, d))
    base = math.degrees(math.atan2(dy, dx))
    ca = max(-1.0, min(1.0, (d * d + l1 * l1 - l2 * l2) / (2 * d * l1)))
    cb = max(-1.0, min(1.0, (l1 * l1 + l2 * l2 - d * d) / (2 * l1 * l2)))
    return base - math.degrees(math.acos(ca)), 180.0 - math.degrees(math.acos(cb))


def _kf(name, stops):
    """A keyframes rule. Concatenated rather than formatted, because CSS braces
    and percent signs collide with Python's own formatting."""
    return ("@keyframes " + name + "{"
            + "".join("%.3f" % p + "%{" + css + "}" for p, css in stops) + "}")


def detected_languages(lang_bytes):
    """Languages the API reports that are not already declared above."""
    if not lang_bytes:
        return []
    known = set()
    for _, _, items in GROUPS:
        for it in items:
            known.add(it[0].lower())
    out = []
    for name, _b in sorted(lang_bytes.items(), key=lambda kv: -kv[1]):
        key = LANG_ALIAS.get(name.lower(), name.lower())
        if key not in known and name.lower() not in known:
            out.append(name)
    return out


def _build_groups(lang_bytes):
    """GROUPS with anything new from the API folded into LANGUAGES."""
    groups = [(nm, col, list(items)) for nm, col, items in GROUPS]
    found = detected_languages(lang_bytes)
    room = MAX_PER_ROW - len(groups[0][2])
    for name in found[:max(0, room)]:
        groups[0][2].append((name, LANG_SLUG.get(name.lower()), "#7A6A55",
                             name[:2].title(), name, True))
    return groups, found


def _flat(groups):
    """Every part with its socket, ordered the way the robot works: right to
    left across the board, top to bottom within each vertical pass."""
    out = []
    for gi, (label, accent, items) in enumerate(groups):
        col, row = gi // 3, gi % 3
        x0 = COL_LABEL_X[col] + LABEL_W
        y = BOARD_Y0 + row * ROW_P
        for k, item in enumerate(items[:MAX_PER_ROW]):
            name, slug, brand, letters = item[:4]
            out.append({"name": name, "slug": slug, "brand": brand, "letters": letters,
                        "short": item[4] if len(item) > 4 else name,
                        "accent": accent, "auto": len(item) > 5,
                        "x": x0 + k * SLOT_P, "y": y})
    out.sort(key=lambda c: (-c["x"], c["y"]))
    return out


def _package(i, c):
    """One part as an IC package: body, pins down both sides, pin-one dot."""
    tint = _mix(CARD, c["brand"], 0.12)
    mark = _readable(c["brand"], tint)
    g = ['<g id="c%d">' % i]
    for j in range(3):
        py = 11 + j * 15
        g.append('<rect x="0" y="%d" width="5.5" height="7" rx="1.5" fill="%s"/>' % (py, STEEL))
        g.append('<rect x="%.1f" y="%d" width="5.5" height="7" rx="1.5" fill="%s"/>'
                 % (CHIP - 5.5, py, STEEL))
    g.append('<rect x="5" y="0" width="%d" height="%d" rx="7" fill="%s" stroke="%s" '
             'stroke-width="1.4"/>' % (CHIP - 10, CHIP, tint, _mix(RULE, c["brand"], 0.35)))
    g.append('<circle cx="12" cy="10" r="2" fill="%s"/>' % _mix(tint, INK, 0.35))
    d = logos.ICONS.get(c["slug"]) if c["slug"] else None
    if d:
        g.append('<g transform="translate(%.2f,%.2f) scale(%.4f)"><path d="%s" fill="%s"/></g>'
                 % ((CHIP - 26) / 2.0, (CHIP - 26) / 2.0 + 2, 26.0 / 24.0, d, mark))
    else:
        g.append(_txt(CHIP / 2.0, CHIP / 2.0 + 7, c["letters"],
                      16 if len(c["letters"]) < 3 else 11.5, mark, "800", "middle", "0"))
    if c["auto"]:
        g.append('<circle cx="%d" cy="10" r="2.6" fill="%s"/>' % (CHIP - 12, TEAMIST))
    g.append("</g>")
    return "".join(g)


def arsenal(lang_bytes=None, path="assets/robot-arsenal.svg"):
    groups, found = _build_groups(lang_bytes)
    chips = _flat(groups)
    n = len(chips)
    span = PLACE_END / float(n)

    board_bottom = BOARD_Y0 + 2 * ROW_P + CHIP + 18
    h = int(board_bottom + 74)

    css = []
    defs = ['<pattern id="ag" width="26" height="26" patternUnits="userSpaceOnUse">'
            '<circle cx="1.5" cy="1.5" r="1" fill="%s"/></pattern>' % GRID,
            '<clipPath id="feedwin"><rect x="%d" y="%d" width="%d" height="%d" rx="7"/></clipPath>'
            % (FEED_X - 32, FEED_Y - 30, 64, FEED_P * 2 + 62)]
    for i, c in enumerate(chips):
        defs.append(_package(i, c))

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="Tech arsenal: a robot arm seating %d tools onto a board, '
           'grouped by languages, frontend, backend, databases, automation, and cloud and '
           'operations">' % (W, h, W, h, n),
           "<title>Tech Arsenal</title>",
           "<defs>" + "".join(defs) + "__STYLE__</defs>",
           '<rect width="%d" height="%d" fill="%s"/>' % (W, h, SKY),
           '<rect width="%d" height="%d" fill="url(#ag)"/>' % (W, h)]

    out.append(_txt(48, 44, "TECH ARSENAL", 13, INK, "800", "start", "3.4"))
    out.append(_txt(W - 48, 44, "%d PARTS · %d GROUPS" % (n, len(groups)),
                    12, FAINT, "600", "end", "2.2"))
    out.append('<path d="M48,58 H%d" stroke="%s" stroke-width="1.4" fill="none"/>' % (W - 48, RULE))
    out.append(_txt(48, 76, "NEW LANGUAGES ARE DETECTED FROM THE GITHUB API AND ADDED "
                            "AUTOMATICALLY", 9.5, MUTED, "600", "start", "1.6"))

    # ── board ────────────────────────────────────────────────────────────
    out.append('<rect x="32" y="150" width="1046" height="%d" rx="14" fill="%s" '
               'stroke="%s" stroke-width="1.4"/>' % (board_bottom - 150, BOARD, RULE))
    for gi, (label, accent, items) in enumerate(groups):
        col, row = gi // 3, gi % 3
        lx = COL_LABEL_X[col]
        y = BOARD_Y0 + row * ROW_P
        out.append('<rect x="%d" y="%d" width="4" height="%d" rx="2" fill="%s"/>'
                   % (lx, y + 6, CHIP - 14, accent))
        out.append(_txt(lx + 12, y + 20, label, 9.5, INK, "800", "start", "1.3"))
        out.append(_txt(lx + 12, y + 34, "%d" % len(items[:MAX_PER_ROW]), 8.5,
                        FAINT, "600", "start", "1"))
        for k, item in enumerate(items[:MAX_PER_ROW]):
            x = lx + LABEL_W + k * SLOT_P
            short = item[4] if len(item) > 4 else item[0]
            out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="7" fill="none" '
                       'stroke="%s" stroke-width="1.3" stroke-dasharray="4 4"/>'
                       % (x + 5, y, CHIP - 10, CHIP, STEEL))
            out.append(_txt(x + CHIP / 2.0, y + CHIP + 11, short,
                            6.8 if len(short) <= 10 else 6.1, MUTED, "700", "middle", "0.2"))

    # ── feed tape, standing on the right ─────────────────────────────────
    out.append(_txt(FEED_X, FEED_Y - 44, "FEED", 9, FAINT, "800", "middle", "2"))
    out.append('<rect x="%d" y="%d" width="72" height="%d" rx="9" fill="%s" stroke="%s" '
               'stroke-width="1.4"/>' % (FEED_X - 36, FEED_Y - 34, FEED_P * 2 + 70, BOARD, RULE))
    holes = "".join("M%d,%dh0.1" % (FEED_X + 29, FEED_Y - 18 + j * 16) for j in range(11))
    out.append('<path d="%s" stroke="%s" stroke-width="3" stroke-linecap="round" '
               'fill="none"/>' % (holes, STEEL))
    out.append('<g clip-path="url(#feedwin)"><g class="strip">')
    for i in range(n):
        out.append('  <use href="#c%d" x="%d" y="%d"/>'
                   % (i, FEED_X - CHIP / 2, FEED_Y - CHIP / 2 + i * FEED_P))
    out.append("</g></g>")
    css.append(_kf("strip", [(0.0, "transform:translateY(0)")] + [
        st for i in range(n) for st in (
            (i * span + span * 0.22, "transform:translateY(" + "%d" % (-i * FEED_P) + "px)"),
            (i * span + span * 0.34, "transform:translateY(" + "%d" % (-(i + 1) * FEED_P) + "px)"))]
        + [(100.0, "transform:translateY(" + "%d" % (-n * FEED_P) + "px)")]))
    css.append(".strip{animation:strip " + "%.1f" % DUR + "s linear infinite}")

    # ── seated parts ─────────────────────────────────────────────────────
    for i, c in enumerate(chips):
        rel = i * span + span * 0.78
        css.append(_kf("seat%d" % i, [(0.0, "opacity:0"), (max(0.0, rel - 0.01), "opacity:0"),
                                      (rel, "opacity:1"), (100.0, "opacity:1")]))
        css.append(".seat%d{animation:seat%d " % (i, i) + "%.1f" % DUR + "s linear infinite}")
        out.append('<use class="seat%d" href="#c%d" x="%d" y="%d"/>' % (i, i, c["x"], c["y"]))

    # ── the robot ────────────────────────────────────────────────────────
    out.append('<rect x="36" y="%d" width="1168" height="5" rx="2.5" fill="%s"/>'
               % (TRACK_Y - 12, STEEL))
    out.append('<rect x="36" y="%d" width="1168" height="5" rx="2.5" fill="%s"/>'
               % (TRACK_Y + 7, STEEL))
    teeth = "".join("M%d,%dv8" % (tx, TRACK_Y - 4) for tx in range(46, 1202, 13))
    out.append('<path d="%s" stroke="%s" stroke-width="2" fill="none"/>' % (teeth, TRACE_D))
    for ex in (40, 1200):
        out.append('<rect x="%d" y="%d" width="9" height="30" rx="3" fill="%s"/>'
                   % (ex - 4, TRACK_Y - 15, ARM_DK))

    car, upper, fore, wrist = [], [], [], []
    for i, c in enumerate(chips):
        c0 = i * span
        tx, ty = c["x"] + CHIP / 2.0, c["y"] + CHIP / 2.0
        for at, (px_, py_, touch) in (
                (0.00, (FEED_X, FEED_Y, False)), (0.08, (FEED_X, FEED_Y, True)),
                (0.20, (FEED_X, FEED_Y, False)), (0.25, (FEED_X, FEED_Y, False)),
                (0.62, (tx, ty, False)), (0.72, (tx, ty, True)),
                (0.84, (tx, ty, False)), (0.86, (tx, ty, False))):
            cx = _carriage_x(px_)
            aim = py_ - GRIP_DY + (0 if touch else -DIP)
            sh, el = _ik(cx, TRACK_Y, px_, aim, L1, L2)
            t = c0 + span * at
            car.append((t, "transform:translateX(" + "%.1f" % cx + "px)"))
            upper.append((t, "transform:rotate(" + "%.2f" % sh + "deg)"))
            fore.append((t, "transform:rotate(" + "%.2f" % el + "deg)"))
            wrist.append((t, "transform:rotate(" + "%.2f" % (-(sh + el)) + "deg)"))

    # park back over the tape, on the right, for the rest of the loop
    cx = _carriage_x(FEED_X)
    sh, el = _ik(cx, TRACK_Y, FEED_X, FEED_Y - GRIP_DY - DIP, L1, L2)
    car.append((100.0, "transform:translateX(" + "%.1f" % cx + "px)"))
    upper.append((100.0, "transform:rotate(" + "%.2f" % sh + "deg)"))
    fore.append((100.0, "transform:rotate(" + "%.2f" % el + "deg)"))
    wrist.append((100.0, "transform:rotate(" + "%.2f" % (-(sh + el)) + "deg)"))

    for nm, stops in (("car", car), ("upper", upper), ("fore", fore), ("wrist", wrist)):
        css.append(_kf(nm, stops))
        css.append("." + nm + "{transform-origin:0 0;animation:" + nm + " "
                   + "%.1f" % DUR + "s ease-in-out infinite}")

    out.append('<g transform="translate(0,%d)">' % TRACK_Y)
    out.append('  <g class="car">')
    out.append('    <rect x="-23" y="-16" width="46" height="31" rx="6" fill="%s" '
               'stroke="%s" stroke-width="1.8"/>' % (ARM_DK, INK))
    for rx_ in (-12, 12):
        out.append('    <circle cx="%d" cy="-8" r="4.2" fill="%s" stroke="%s" '
                   'stroke-width="1.5"/>' % (rx_, SKY, INK))
    out.append('    <rect x="-11" y="3" width="22" height="6" rx="3" fill="%s"/>' % ARM)
    out.append('    <g class="upper">')
    out.append('      <rect x="-6" y="-6" width="%d" height="12" rx="6" fill="%s" '
               'stroke="%s" stroke-width="1.7"/>' % (int(L1) + 12, ARM, INK))
    out.append('      <circle cx="0" cy="0" r="5.5" fill="%s"/>' % ARM_DK)
    out.append('      <g transform="translate(%d,0)">' % int(L1))
    out.append('        <g class="fore">')
    out.append('          <rect x="-5" y="-5" width="%d" height="10" rx="5" fill="%s" '
               'stroke="%s" stroke-width="1.6"/>' % (int(L2) + 10, ARM, INK))
    out.append('          <circle cx="0" cy="0" r="5" fill="%s"/>' % ARM_DK)
    out.append('          <g transform="translate(%d,0)">' % int(L2))
    out.append('            <g class="wrist">')
    out.append('              <rect x="-11" y="-11" width="22" height="17" rx="4" fill="%s" '
               'stroke="%s" stroke-width="1.7"/>' % (ARM_DK, INK))
    for jx in (-12, 9):
        out.append('              <rect x="%d" y="3" width="3.4" height="14" rx="1.7" '
                   'fill="%s"/>' % (jx, ARM_DK))
    for i in range(n):
        c0 = i * span
        css.append(_kf("grip%d" % i, [
            (0.0, "opacity:0"), (max(0.0, c0 + span * 0.13), "opacity:0"),
            (c0 + span * 0.15, "opacity:1"), (c0 + span * 0.76, "opacity:1"),
            (min(100.0, c0 + span * 0.78), "opacity:0"), (100.0, "opacity:0")]))
        css.append(".grip%d{animation:grip%d " % (i, i) + "%.1f" % DUR + "s linear infinite}")
        out.append('              <use class="grip%d" href="#c%d" x="%d" y="5"/>'
                   % (i, i, -CHIP / 2))
    out.append("            </g></g></g></g></g></g></g>")

    out.append('<path d="M48,%d H%d" stroke="%s" stroke-width="1.4" fill="none"/>'
               % (h - 28, W - 48, RULE))
    foot = "MARKS BY SIMPLE ICONS (CC0) · DRAWN IN, NOT FETCHED"
    if found:
        foot = "DETECTED FROM THE API: " + ", ".join(found[:4]).upper() + " · " + foot
    out.append(_txt(48, h - 10, foot, 9.5, FAINT, "600", "start", "1.6"))
    out.append(_txt(W - 48, h - 10, "GITHUB.COM/AHMADMALIK1376", 9.5, FAINT, "600", "end", "1.6"))
    out.append("</svg>")

    svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote %s (%d parts, %d groups, %.0fs loop, %d KB%s)"
          % (path, n, len(groups), DUR, len(svg) // 1024,
             (", detected: " + ", ".join(found)) if found else ""))
    return path


if __name__ == "__main__":
    import json
    import sys
    lb = json.load(open(sys.argv[1], encoding="utf-8")) if len(sys.argv) > 1 else None
    arsenal(lang_bytes=lb)
