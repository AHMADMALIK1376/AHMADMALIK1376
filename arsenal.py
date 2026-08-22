# -*- coding: utf-8 -*-
"""
The tech arsenal, laid out like a periodic table.

Every skill is one tile: brand mark, name, and an index down the row. Tiles are
grouped by what the thing is for, and the group's colour runs along the left
edge of each of its tiles.

This replaces five collapsed <details> blocks that pulled their icons from
skillicons.dev and their badges from img.shields.io. Both are third-party hosts
that GitHub's image proxy has to reach on every page view, and when they are
slow or down the section renders as broken images. Everything here is drawn from
paths baked into logos.py, so the section has no external dependency at all.

Four tiles carry letters rather than a mark: Playwright, AWS, Oracle and WSL.
Simple Icons dropped those at the trademark owners' request, and approximating
someone's logo by hand is worse than not drawing it. A lettered tile reads as
deliberate in a periodic table anyway.

House style: solid fills, no gradients, no filters.
"""
import logos

AEGEAN, CORAL = "#0077C8", "#F88379"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
SKY = "#F2EDE6"
GRID = "#E6DBCA"
TRACE = "#E1D5C2"
TRACE_D = "#CDBEA6"
INK = "#2E2A24"
MUTED = "#7D7266"
FAINT = "#A2988A"
RULE = "#D9D0C1"
CARD = "#FBF7F0"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# label, icon slug (None draws letters instead), brand colour, letters, and an
# optional short label for names too long to sit under a tile
GROUPS = [
    ("LANGUAGES", "SPOKEN DAILY", AEGEAN, [
        ("Python", "python", "#3776AB", "Py"),
        ("TypeScript", "typescript", "#3178C6", "Ts"),
        ("JavaScript", "javascript", "#F7DF1E", "Js"),
        ("Java", "openjdk", "#437291", "Ja"),
        ("C++", "cplusplus", "#00599C", "C+"),
        ("HTML5", "html5", "#E34F26", "Ht"),
        ("CSS", "css", "#663399", "Cs"),
        ("SQL", None, "#4479A1", "Sql"),
    ]),
    ("BACKEND", "SERVICES AND APIS", TEAMIST, [
        ("Node.js", "nodedotjs", "#5FA04E", "No"),
        ("Express", "express", "#4A4A4A", "Ex"),
        ("FastAPI", "fastapi", "#009688", "Fa"),
        ("Playwright", None, "#2EAD33", "Pw"),
        ("BeautifulSoup", None, "#8E6C3F", "Bs", "Soup"),
        ("Uvicorn", None, "#C2543C", "Uv"),
    ]),
    ("FRONTEND", "INTERFACE AND UI", CORAL, [
        ("React", "react", "#3AA8C1", "Re"),
        ("Tailwind", "tailwindcss", "#0891A8", "Tw"),
        ("Vite", "vite", "#646CFF", "Vi"),
        ("Canvas API", None, "#C2681F", "Cv", "Canvas"),
    ]),
    ("DATABASES", "STORAGE AND QUERY", CRIMSON, [
        ("MongoDB", "mongodb", "#47A248", "Mg"),
        ("PostgreSQL", "postgresql", "#4169E1", "Pg", "Postgres"),
        ("MySQL", "mysql", "#4479A1", "My"),
        ("Firebase", "firebase", "#DD8B00", "Fb"),
        ("Oracle", None, "#C74634", "Or"),
    ]),
    ("CLOUD & OPS", "SHIP AND RUN", BROWN, [
        ("Google Cloud", "googlecloud", "#4285F4", "Gc", "GCP"),
        ("AWS", None, "#D6820B", "Aws"),
        ("Docker", "docker", "#2496ED", "Dk"),
        ("Git", "git", "#F05032", "Gi"),
        ("Linux", "linux", "#9A7B14", "Lx"),
        ("WSL 2", None, "#0078D4", "Wsl"),
        ("n8n", "n8n", "#EA4B71", "N8"),
    ]),
]

W = 1240
LABEL_X = 56          # group name sits in its own column on the left
TILE_X = 232          # tiles begin here
TILE = 74
GAP = 10
ROW = 92
TOP = 104


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
    """Blend two colours and return a solid hex. No alpha anywhere, so the
    result stays a flat fill in keeping with the rest of the profile art."""
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(ra[i] + (rb[i] - ra[i]) * t for i in range(3)))


def _lum(h):
    """Relative luminance, for deciding whether a mark needs darkening."""
    out = []
    for v in _rgb(h):
        v = v / 255.0
        out.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def _readable(brand, backdrop):
    """Keep the mark recognisably its own colour, but dark enough to read.

    Several brand colours are far too light to sit on a cream tile: JavaScript
    yellow and Linux yellow all but vanish. Rather than drop the brand colour,
    walk it toward the ink until it clears a contrast floor against the tile it
    is actually drawn on.
    """
    colour = brand
    for _ in range(14):
        l1, l2 = _lum(colour), _lum(backdrop)
        hi, lo = max(l1, l2), min(l1, l2)
        if (hi + 0.05) / (lo + 0.05) >= 3.1:
            break
        colour = _mix(colour, INK, 0.16)
    return colour


def arsenal(path="assets/arsenal.svg"):
    rows = len(GROUPS)
    h = TOP + rows * ROW + 52

    css = ["@keyframes rise{0%{opacity:0;transform:translateY(9px)}}",
           "@keyframes fade{0%{opacity:0}}",
           ".ti{animation:rise .5s cubic-bezier(.22,1,.36,1) backwards}",
           ".gl{animation:fade .6s ease-out backwards}"]

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="Tech arsenal: languages, backend, frontend, databases, '
           'cloud and operations">' % (W, h, W, h),
           "<title>Tech Arsenal</title>",
           '<defs><pattern id="ag" width="26" height="26" patternUnits="userSpaceOnUse">'
           '<circle cx="1.5" cy="1.5" r="1" fill="%s"/></pattern>__STYLE__</defs>' % GRID,
           '<rect width="%d" height="%d" fill="%s"/>' % (W, h, SKY),
           '<rect width="%d" height="%d" fill="url(#ag)"/>' % (W, h)]

    # header
    out.append(_txt(48, 46, "TECH ARSENAL", 13, INK, "800", "start", "3.4"))
    total = sum(len(g[3]) for g in GROUPS)
    out.append(_txt(W - 48, 46, "%d TOOLS ACROSS %d GROUPS" % (total, rows),
                    12, FAINT, "600", "end", "2.2"))
    out.append('<path d="M48,60 H%d" stroke="%s" stroke-width="1.4" fill="none"/>' % (W - 48, RULE))
    out.append(_txt(48, 78, "WHAT I BUILD WITH, GROUPED BY WHAT IT IS FOR",
                    9.5, MUTED, "600", "start", "1.8"))

    n = 0
    for gi, (label, sub, accent, items) in enumerate(GROUPS):
        y = TOP + gi * ROW

        css.append(".gl%d{animation-delay:%.2fs}" % (gi, gi * 0.09))
        out.append('<g class="gl gl%d">' % gi)
        out.append("  " + '<rect x="%d" y="%d" width="4.5" height="30" rx="2.2" fill="%s"/>'
                          % (LABEL_X, y + 12, accent))
        out.append("  " + _txt(LABEL_X + 16, y + 27, label, 11.5, INK, "800", "start", "2"))
        out.append("  " + _txt(LABEL_X + 16, y + 43, sub, 8.5, FAINT, "600", "start", "1.2"))
        out.append("</g>")

        for k, item in enumerate(items):
            name, slug, brand, letters = item[:4]
            short = item[4] if len(item) > 4 else name
            n += 1
            x = TILE_X + k * (TILE + GAP)
            tint = _mix(CARD, brand, 0.10)
            mark = _readable(brand, tint)
            css.append(".ti%d{animation-delay:%.2fs}" % (n, 0.16 + gi * 0.07 + k * 0.03))
            out.append('<g class="ti ti%d">' % n)
            out.append("  " + '<rect x="%d" y="%d" width="%d" height="%d" rx="11" fill="%s" '
                              'stroke="%s" stroke-width="1.3"/>'
                              % (x, y, TILE, TILE, tint, RULE))
            # the group's colour down the left edge, so a tile still reads as
            # belonging to its row when the eye is scanning across
            out.append("  " + '<rect x="%d" y="%d" width="3.4" height="%d" rx="1.7" fill="%s"/>'
                              % (x + 8, y + 14, TILE - 28, accent))
            out.append("  " + _txt(x + TILE - 8, y + 15, "%02d" % n, 7, FAINT, "700", "end", "0.6"))

            d = logos.ICONS.get(slug) if slug else None
            if d:
                # 24x24 grid scaled up and centred in the tile
                s = 30.0 / 24.0
                cx = x + TILE / 2.0 - 15
                out.append('  <g transform="translate(%.2f,%d) scale(%.4f)">'
                           '<path d="%s" fill="%s"/></g>' % (cx, y + 20, s, d, mark))
            else:
                out.append("  " + _txt(x + TILE / 2.0, y + 44, letters,
                                       19 if len(letters) < 3 else 15, mark, "800", "middle", "0"))

            out.append("  " + _txt(x + TILE / 2.0, y + TILE - 10, short,
                                   7.6 if len(short) <= 10 else 6.8,
                                   INK, "700", "middle", "0.3"))
            out.append("</g>")

    # Every group has a different number of tiles, which leaves a ragged right
    # edge. Rather than pad the rows out, each one is wired off to the edge of
    # the board, using the same tracks as the rest of the profile.
    for gi, (_, _, accent, items) in enumerate(GROUPS):
        y = TOP + gi * ROW
        row_end = TILE_X + len(items) * (TILE + GAP) - GAP
        if W - row_end < 190:
            continue
        cy = y + TILE / 2.0
        x0 = row_end + 34
        knee = W - 54 - (gi % 3) * 18
        d = "M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%d,%.1f" % (
            x0, cy, knee - 24, cy, knee, cy - 24, W, cy - 24)
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.6" '
                   'stroke-linecap="round" stroke-linejoin="round"/>' % (d, TRACE))
        out.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s"/>' % (x0, cy, TRACE_D))
        out.append('<circle cx="%.1f" cy="%.1f" r="1.7" fill="%s"/>' % (x0, cy, SKY))
        css.append(".pl%d{animation:pl%d %ds linear infinite;animation-delay:-%.1fs}"
                   % (gi, gi, 7 + gi % 3, gi * 1.5))
        css.append("@keyframes pl%d{0%%{transform:translateX(%.1fpx);opacity:0}"
                   "15%%,80%%{opacity:1}100%%{transform:translateX(%.1fpx);opacity:0}}"
                   % (gi, x0, knee - 24))
        out.append('<circle class="pl%d" cy="%.1f" r="3" fill="%s"/>' % (gi, cy, TRACE_D))

    out.append('<path d="M48,%d H%d" stroke="%s" stroke-width="1.4" fill="none"/>'
               % (h - 30, W - 48, RULE))
    out.append(_txt(48, h - 12, "MARKS BY SIMPLE ICONS (CC0) · DRAWN IN, NOT FETCHED",
                    10, FAINT, "600", "start", "2"))
    out.append(_txt(W - 48, h - 12, "GITHUB.COM/AHMADMALIK1376", 10, FAINT, "600", "end", "1.6"))
    out.append("</svg>")

    svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote %s (%d tiles, %d groups)" % (path, n, rows))
    return path


if __name__ == "__main__":
    arsenal()
