# -*- coding: utf-8 -*-
"""
The introduction banner.

Eleven carriers fly in from the right, one letter each, and set the name. The
rest of the panel writes itself behind them. The finished thing stands for about
ten seconds, and then a heavy carrier comes down, throws a net over the whole
panel, gathers it into a bundle and lifts it out of frame.

Everything converges on one point rather than each piece going its own way,
because that is what a net closing does to its contents. Each piece takes a
small fixed offset around that point so the bundle has body rather than
everything stacking on one spot, and a rotation so nothing is still sitting in
its reading position once it is in the net.

Layout note: CSS `transform` OVERRIDES a `transform=` attribute on the same
element, so anything animated is nested inside a plain positioning <g>. That is
also why a gathered piece gets its own wrapper: its reveal already animates a
transform, and the two cannot share an element.

The existing panel is not rewritten to new coordinates. It is drawn as it was
and pushed down as a block by SHIFT, which leaves the top band free. Only the
letters and the machinery live in absolute space, because they have to meet each
other and doing that through two coordinate systems is how mistakes get made.
"""
import math
import os

OUT = "assets"
SHIFT = 62                      # the whole original panel moves down by this
W, H = 1240, 312 + SHIFT
DUR = "32s"
DUR_S = 32.0

AEGEAN, CORAL = "#0077C8", "#F88379"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
AEG_D, COR_D, TEA_D, CRI_D = "#00568F", "#B84A40", "#63801A", "#A5151B"
TINTS = {AEG_D: "#E2EEF7", COR_D: "#FBE8E5", TEA_D: "#EEF4DC", CRI_D: "#FAE3E3"}
SKY = "#F2EDE6"
INK = "#2E2A24"
INK_2 = "#5E5349"
MUTED = "#7D7266"
FAINT = "#A2988A"
RULE = "#D9D0C1"
GRID = "#E6DBCA"
TRACE = "#E1D5C2"
TRACE_D = "#CDBEA6"
CARD = "#FBF7F0"
STEEL = "#B9AC97"
ARM = "#F0C419"
ARM_DK = "#39332B"
SANS = "ui-sans-serif,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

LEFT = 104
SPINE = [AEGEAN, CORAL, TEAMIST, CRIMSON, BROWN]
LINE = "Production web applications and LLM-powered systems."
LINE_W = 560
CHIPS = [("LLM INTEGRATION", AEG_D), ("COMPUTER VISION", COR_D),
         ("BROWSER AUTOMATION", TEA_D), ("API &amp; DATABASES", CRI_D)]
FACTS = [("BASED IN", "Rawalpindi, Pakistan", None),
         ("FOCUS", "LLM Integration &#183; Vision", None),
         ("STATUS", "Open to opportunities", TEAMIST)]

NAME = "M.AHMAD MALIK"
NAME_SIZE = 56
NAME_Y = 142 + SHIFT
# advance per glyph as a fraction of the size; a bold sans is not monospaced and
# setting the letters individually means their spacing has to be stated
ADV = {"M": .86, ".": .30, "A": .70, "H": .76, "D": .74, " ": .30,
       "L": .62, "I": .32, "K": .72}
# Set one glyph at a time, so the gap between them has to be added here. The
# letter-spacing attribute is no use: on a single-character run it pads the
# trailing edge rather than sitting between anything.
GAP = 6.0

FLY_Y = 70                      # the altitude the formation holds
TILE = 30
FALL = 74                       # how far a letter drops out of its carrier

# The lift. A heavy carrier drops a net over the finished panel, the panel
# gathers into it, and the whole bundle goes up and out of frame.
GX, GY = 620.0, 208.0           # where everything is drawn together
LIFT_H = H + 300                # far enough that the bundle really leaves
NET_HALF_W, NET_HALF_H = 570.0, 96.0
BIG_IN, BIG_HOVER = 78.0, 83.0  # the carrier comes down
NET_OPEN, NET_SHUT = 86.0, 92.0
RISE_END = 98.0

# One aircraft per letter, entering from the right on a stagger. Each flies to
# its own place in the name, releases, and carries on out to the left, so the
# formation is always moving one way and never has to turn around.
LEAD, STAG = 2.0, 2.2
ENTER, HOVER, EXIT = 7.0, 1.8, 5.0

css, out = [], []
add = out.append


def rr(x, y, w, h, r, fill, extra=""):
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"%s/>'
            % (x, y, w, h, r, fill, (" " + extra) if extra else ""))


def ci(cx, cy, r, fill, extra=""):
    return ('<circle cx="%s" cy="%s" r="%s" fill="%s"%s/>'
            % (cx, cy, r, fill, (" " + extra) if extra else ""))


def txt(x, y, s, size, fill, weight="700", anchor="start", fam=None, ls="0", cls=None):
    return ('<text x="%s" y="%s" font-family="%s" font-size="%s" font-weight="%s" fill="%s" '
            'text-anchor="%s" letter-spacing="%s"%s>%s</text>'
            % (x, y, fam or SANS, size, weight, fill, anchor, ls,
               (' class="%s"' % cls) if cls else "", s))


def kf(name, body):
    css.append("@keyframes " + name + "{" + body + "}")


# ── where each letter lands ───────────────────────────────────────────
# The initial and its full stop travel together, because "M." is one mark and
# splitting it would mean twelve aircraft for eleven letters.
glyphs, lx = [], float(LEFT)
for chn in NAME:
    wdt = ADV.get(chn, .70) * NAME_SIZE
    glyphs.append((chn, lx, wdt))
    lx += wdt + GAP
NAME_W = lx - LEFT

tiles, i = [], 0
while i < len(glyphs):
    chn, gx, gw = glyphs[i]
    if chn == " ":
        i += 1
        continue
    if chn == "M" and i + 1 < len(glyphs) and glyphs[i + 1][0] == ".":
        gw = glyphs[i + 1][1] + glyphs[i + 1][2] - gx
        tiles.append(("M.", gx, gx + gw / 2.0))
        i += 2
        continue
    tiles.append((chn, gx, gx + gw / 2.0))
    i += 1
N = len(tiles)

# ══ motion ════════════════════════════════════════════════════════════
# Everything that used to run on a ten second cycle now reveals once and holds,
# because the loop is thirty two seconds and a panel that fades itself out and
# back in every time would be exhausting at that length.
css += [
    ".sp{transform-origin:0 0}",
    ".eb{animation:eb %s ease-out infinite}" % DUR,
    ".rl{stroke-dasharray:100;stroke-dashoffset:100;animation:rl %s ease-out infinite}" % DUR,
    ".typ{animation:typ %s steps(38,end) infinite}" % DUR,
    ".tc{animation:tc %s steps(38,end) infinite, blink 1.05s steps(1,end) infinite}" % DUR,
    "@keyframes blink{0%,50%{opacity:1}51%,100%{opacity:0}}",
    ".dot{animation:dot 2.2s ease-in-out infinite}",
    "@keyframes dot{0%,100%{opacity:1}50%{opacity:.35}}",
]
kf("eb", "0%,1%{opacity:0}4%,100%{opacity:1}")
# the rest writes itself once the name is down, then the machine clears it
HOLD_FROM = 52.0

_kn = [0]
KNOCKS = []          # (x, y, is_letter) per piece, for offline previews


def knock(x, y, markup, gy):
    """Wrap a piece so the net gathers it in and carries it out.

    Every piece converges on the same point rather than each going its own way:
    a net closing pulls its contents together, so they have to end up bunched.
    Each one gets a small fixed offset around that point so the bundle has some
    body instead of everything stacking on one spot, and a rotation so nothing
    is still sitting in its reading position once it is in the net.

    `gy` is the gather height in whatever space the piece lives in, since the
    panel is drawn shifted and the name is not.

    transform-box:fill-box is not optional here. On an SVG element
    transform-origin defaults to the view-box origin, not the element, so a
    rotated piece swings about the top-left corner of the whole banner and is
    flung hundreds of pixels off. This makes it turn where it lies.
    """
    i = _kn[0]
    _kn[0] += 1
    KNOCKS.append((x, y))
    jx = (-84, 52, -32, 94, -112, 16, 68, -62)[i % 8]
    jy = (-28, 14, 36, -16, 6, -38, 24, -4)[i % 8]
    ang = (17, -23, 31, -12, 24, -34, 9, -28)[i % 8]
    dx, dy = GX + jx - x, gy + jy - y
    kf("kn%d" % i,
       "0%%,%.2f%%{transform:translate(0,0) rotate(0)}"
       "%.2f%%{transform:translate(%.0fpx,%.0fpx) rotate(%.0fdeg) scale(.5)}"
       "%.2f%%,100%%{transform:translate(%.0fpx,%.0fpx) rotate(%.0fdeg) scale(.5)}"
       % (NET_OPEN, NET_SHUT, dx, dy, ang,
          RISE_END, dx, dy - LIFT_H, ang))
    css.append(".kn%d{transform-box:fill-box;transform-origin:center;"
               "animation:kn%d %s cubic-bezier(.5,0,.5,1) infinite}" % (i, i, DUR))
    return '<g class="kn%d">%s</g>' % (i, markup)


add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
    'aria-label="M. Ahmad Malik, Full-Stack AI Engineer: a drone delivers the letters of the name '
    'and a robot arm sets them one at a time">' % (W, H, W, H))
add("<title>M. Ahmad Malik</title>")
add('<defs><clipPath id="tp"><rect class="typ" x="%d" y="180" width="0" height="30"/></clipPath>'
    '<pattern id="dg" width="26" height="26" patternUnits="userSpaceOnUse">'
    '<circle cx="1.5" cy="1.5" r="1" fill="%s"/></pattern>'
    "__STYLE__</defs>" % (LEFT, GRID))
add(rr(0, 0, W, H, 0, SKY))
add(rr(0, 0, W, H, 0, "url(#dg)"))

# ══ the original panel, moved down as one piece ════════════════════════
add('<g transform="translate(0,%d)">' % SHIFT)

# ── circuit substrate ────────────────────────────────────────────────
# Routed only through the margins and the gap between the chips and the
# divider, so it never sits under the type.
for d in ("M0,33 H32 L72,73", "M0,113 H32 L72,153", "M0,193 H32 L72,233",
          "M120,14 H300 L326,40 H520", "M600,40 H740 L766,14 H960",
          "M1000,14 H1120 L1146,40 H1240",
          "M60,296 H240 L266,272 H460", "M540,272 H700 L726,296 H900",
          "M960,296 H1080 L1106,272 H1240",
          "M812,70 V150 L840,178 V240", "M900,240 V170 L928,142 V70",
          "M1240,120 H1204 V196 H1240"):
    add('<path d="%s" fill="none" stroke="%s" stroke-width="1.6" stroke-linecap="round" '
        'stroke-linejoin="round"/>' % (d, TRACE))
for vx, vy in ((120, 14), (520, 14), (600, 40), (960, 14), (1000, 14), (1240, 14),
               (60, 296), (460, 272), (540, 272), (900, 296), (960, 296),
               (812, 70), (840, 240), (900, 240), (928, 70), (1204, 120), (1204, 196)):
    add(ci(vx, vy, 4, TRACE_D))
    add(ci(vx, vy, 1.7, SKY))
for i, (x0, x1, yy) in enumerate(((120, 300, 14), (540, 700, 272), (1000, 1120, 14))):
    css.append(".pl%d{animation:pl%d %ds linear infinite;animation-delay:-%ds}"
               % (i, i, 7 + i, i * 3))
    kf("pl%d" % i, "0%%{transform:translateX(%dpx);opacity:0}"
       "15%%,80%%{opacity:1}100%%{transform:translateX(%dpx);opacity:0}" % (x0, x1))
    add('<circle class="pl%d" cy="%d" r="3" fill="%s"/>' % (i, yy, TRACE_D))
add("</g>")

# ══ everything written on the board, which is what gets cleared ════════
add('<g transform="translate(0,%d)">' % SHIFT)

for i, c in enumerate(SPINE):
    add(knock(72, 56 + i * 40, '<g transform="translate(72,%d)"><g class="sp%d">%s'
              "</g></g>" % (56 + i * 40, i, rr(0, 0, 5, 34, 2.5, c)),
              GY - SHIFT))

add(knock(LEFT, 80, '<g class="eb">' + txt(LEFT, 80, "FULL-STACK AI ENGINEER", 13, AEG_D, "800",
                                       "start", MONO, "3.6") + "</g>", GY - SHIFT))
add(knock(LEFT + 330, 164,
          '<path class="rl" pathLength="100" d="M%d,164 H%d" stroke="%s" stroke-width="1.6" '
          'fill="none"/>' % (LEFT, LEFT + 660, RULE), GY - SHIFT))
add(knock(LEFT + 180, 200,
          '<g clip-path="url(#tp)">'
          + txt(LEFT, 202, LINE, 16.5, MUTED, "400", "start", SANS, "0") + "</g>"
          + '<g transform="translate(%d,186)"><rect class="tc" width="2" height="20" rx="1" '
            'fill="%s"/></g>' % (LEFT + 2, INK_2), GY - SHIFT))

cx = LEFT
for i, (label, colr) in enumerate(CHIPS):
    plain = label.replace("&amp;", "&")
    cw = len(plain) * 7.3 + 30
    add(knock(cx + cw / 2, 245,
              '<g class="ch%d">%s%s</g>'
              % (i, rr(cx, 230, cw, 30, 15, TINTS[colr]),
                 txt(cx + cw / 2, 249, label, 11, colr, "700", "middle", MONO, "1.4")),
              GY - SHIFT))
    cx += cw + 12

for i, (label, val, dot) in enumerate(FACTS):
    y = 88 + i * 62
    body = txt(W - 72, y, label, 10, FAINT, "700", "end", MONO, "2.4")
    if dot:
        body += ci(W - 72 - 152, y + 18, 5, dot, 'class="dot"')
    body += txt(W - 72, y + 22, val, 14, INK_2, "600", "end", SANS, "0")
    add(knock(W - 150, y + 10, '<g class="fa%d">%s</g>' % (i, body),
              GY - SHIFT))
add(knock(W - 250, 156,
          '<path d="M%d,56 V256" stroke="%s" stroke-width="1.4" fill="none"/>'
          % (W - 250, RULE), GY - SHIFT))
add("</g>")

# ══ the letters, each dropped by its own aircraft ══════════════════════
lettermk = []
css.append(".rot{transform-origin:0 0;animation:rot .24s linear infinite}")
kf("rot", "0%,100%{transform:scaleX(1)}50%{transform:scaleX(.12)}")
css.append(".bob{animation:bob 2.6s ease-in-out infinite}")
kf("bob", "0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}")


def drone(colr, accent, letter):
    """A small carrier, drawn about its own centre with the tile slung under."""
    g = rr(-46, -5, 92, 4, 2, ARM_DK)
    for rx in (-42, 42):
        g += rr(rx - 2.5, -12, 5, 8, 2, STEEL)
        g += '<ellipse cx="%d" cy="-13" rx="19" ry="2.6" fill="%s" opacity=".2"/>' % (rx, INK)
        g += ('<g transform="translate(%d,-13)"><g class="rot" style="animation-delay:-%.2fs">'
              "%s</g></g>" % (rx, 0 if rx < 0 else .08, rr(-19, -1.4, 38, 2.8, 1.4, INK)))
    g += rr(-24, -19, 48, 24, 9, colr, 'stroke="%s" stroke-width="1.6"' % ARM_DK)
    g += rr(7, -15, 13, 10, 3.5, CARD)
    g += rr(-19, -15, 16, 5, 2.5, accent)
    g += ci(-21, -4, 2.8, CORAL, 'class="dot"')
    g += ('<path d="M-13,5 L-10,26 M13,5 L10,26" stroke="%s" stroke-width="1.5" '
          'fill="none"/>' % ARM_DK)
    return g


for i, (chn, gx, cxx) in enumerate(tiles):
    t0 = LEAD + i * STAG
    drop = t0 + ENTER + HOVER * 0.5
    gone = t0 + ENTER + HOVER + EXIT
    colr = SPINE[i % len(SPINE)]

    # the flight: in from the right, a pause over its own letter, out to the left
    kf("fl%d" % i,
       "0%%,%.3f%%{transform:translateX(1360px)}"
       "%.3f%%,%.3f%%{transform:translateX(%.1fpx)}"
       "%.3f%%,100%%{transform:translateX(-190px)}"
       % (t0, t0 + ENTER, t0 + ENTER + HOVER, cxx, gone))
    css.append(".fl%d{animation:fl%d %s ease-in-out infinite}" % (i, i, DUR))
    # only in the air between entering and leaving
    kf("fv%d" % i, "0%%,%.3f%%{opacity:0}%.3f%%,%.3f%%{opacity:1}%.3f%%,100%%{opacity:0}"
       % (t0 - 0.01, t0, gone - 0.4, gone))
    css.append(".fv%d{animation:fv%d %s linear infinite}" % (i, i, DUR))
    # the tile is aboard until it is released
    kf("tv%d" % i, "0%%,%.3f%%{opacity:1}%.3f%%,100%%{opacity:0}" % (drop, drop + 0.01))
    css.append(".tv%d{animation:tv%d %s steps(1,end) infinite}" % (i, i, DUR))

    add('<g class="fv%d"><g class="fl%d"><g transform="translate(0,%d)"><g class="bob" '
        'style="animation-delay:-%.2fs">' % (i, i, FLY_Y, i * 0.31))
    add("  " + drone(colr, ARM, chn))
    add('  <g class="tv%d"><g transform="translate(%d,26)">%s%s</g></g>'
        % (i, -TILE // 2,
           rr(0, 0, TILE, TILE, 5, CARD, 'stroke="%s" stroke-width="1.4"' % colr),
           txt(TILE / 2.0, 21, chn, 15 if len(chn) < 2 else 12, colr, "800", "middle", SANS)))
    add("</g></g></g></g>")

    # the letter itself, falling the last stretch into its place in the name
    kf("ln%d" % i,
       "0%%,%.3f%%{opacity:0;transform:translateY(-%dpx)}"
       "%.3f%%{opacity:1;transform:translateY(-%dpx)}"
       "%.3f%%,100%%{opacity:1;transform:translateY(0)}"
       % (drop - 0.01, FALL, drop, FALL, drop + 1.1))
    css.append(".ln%d{animation:ln%d %s cubic-bezier(.4,1.5,.6,1) infinite}" % (i, i, DUR))
    lettermk.append(knock(cxx, NAME_Y, '<g class="ln%d">%s</g>'
                          % (i, txt(gx, NAME_Y, chn, NAME_SIZE, INK, "800", "start",
                                    SANS, "0")), GY))

for mk in lettermk:
    add(mk)



# ══ the heavy carrier and its net ══════════════════════════════════════
# The carrier drops in above the finished panel, the net falls open across the
# full width of the type, closes as the panel gathers into it, and the whole
# bundle goes up together. Net and carrier ride one transform each so they
# cannot drift apart, and the net's scale is what reads as open or shut.
kf("bigfly",
   "0%%,%.0f%%{transform:translateY(-300px)}"
   "%.0f%%,%.0f%%{transform:translateY(0)}"
   "%.0f%%,100%%{transform:translateY(-%dpx)}"
   % (BIG_IN, BIG_HOVER, NET_SHUT, RISE_END, LIFT_H))
css.append(".bigfly{animation:bigfly %s cubic-bezier(.4,0,.4,1) infinite}" % DUR)
kf("bigv", "0%%,%.2f%%{opacity:0}%.2f%%,%.2f%%{opacity:1}%.2f%%,100%%{opacity:0}"
   % (BIG_IN - 0.01, BIG_IN, RISE_END, RISE_END + 1.0))
css.append(".bigv{animation:bigv %s steps(1,end) infinite}" % DUR)
# furled on the way in, thrown wide over the panel, then drawn shut on the bundle
kf("netopen",
   "0%%,%.0f%%{transform:scale(.16,.30)}"
   "%.0f%%{transform:scale(1,1)}"
   "%.0f%%,100%%{transform:scale(.44,.70)}"
   % (BIG_HOVER, NET_OPEN, NET_SHUT))
css.append(".netopen{transform-box:fill-box;transform-origin:center top;"
           "animation:netopen %s cubic-bezier(.4,0,.4,1) infinite}" % DUR)

add('<g class="bigv"><g class="bigfly">')
add('  <g transform="translate(%.0f,%.0f)">' % (GX, 44))
# four rotors on two booms, the far pair drawn smaller so it reads as depth
for bx, scl in ((-176, .82), (-92, 1.0), (92, 1.0), (176, .82)):
    add("    " + rr(bx - 4, -20, 8, 16, 3, STEEL))
    add('    <ellipse cx="%d" cy="-21" rx="%.0f" ry="%.0f" fill="%s" opacity=".18"/>'
        % (bx, 46 * scl, 5 * scl, INK))
    add('    <g transform="translate(%d,-21)"><g class="rot" style="animation-delay:-%.2fs">%s'
        "</g></g>" % (bx, abs(bx) * 0.002, rr(-46 * scl, -2.4, 92 * scl, 4.8, 2.4, INK)))
add("    " + rr(-190, -6, 380, 7, 3.5, ARM_DK))
add("    " + rr(-70, -34, 140, 42, 12, AEGEAN, 'stroke="%s" stroke-width="2"' % ARM_DK))
add("    " + rr(24, -27, 38, 20, 5, CARD))
add("    " + rr(-58, -27, 40, 9, 4, ARM))
add("    " + ci(-62, -12, 4, CORAL, 'class="dot"'))
add("    " + rr(-24, 8, 48, 10, 4, ARM_DK))
add("  </g>")

# the net: a bag hung on four lines, drawn open and scaled shut
add('  <g class="netopen"><g transform="translate(%.0f,%.0f)">' % (GX, GY))
for sx in (-1, 1):
    add('    <path d="M%.0f,%.0f L%.0f,%.0f" stroke="%s" stroke-width="2.2" fill="none"/>'
        % (sx * 66, -164, sx * NET_HALF_W, -NET_HALF_H, ARM_DK))
    add('    <path d="M%.0f,%.0f L%.0f,%.0f" stroke="%s" stroke-width="1.8" fill="none"/>'
        % (sx * 30, -164, sx * NET_HALF_W * .45, -NET_HALF_H, ARM_DK))
add('    <path d="M%.0f,%.0f Q0,%.0f %.0f,%.0f" fill="none" stroke="%s" stroke-width="3" '
    'stroke-linecap="round"/>'
    % (-NET_HALF_W, -NET_HALF_H, NET_HALF_H * 2.5, NET_HALF_W, -NET_HALF_H, ARM_DK))
add('    <path d="M%.0f,%.0f H%.0f" stroke="%s" stroke-width="3" stroke-linecap="round"/>'
    % (-NET_HALF_W, -NET_HALF_H, NET_HALF_W, ARM_DK))
# the mesh, converging toward the bottom of the bag the way a net does
for k in range(-9, 10):
    fx = k / 9.0
    add('    <path d="M%.0f,%.0f Q%.0f,%.0f %.0f,%.0f" fill="none" stroke="%s" '
        'stroke-width="1.3" opacity=".65"/>'
        % (fx * NET_HALF_W, -NET_HALF_H, fx * NET_HALF_W * .6, NET_HALF_H * 1.1,
           fx * NET_HALF_W * .22, NET_HALF_H * 1.55, ARM_DK))
for lvl in (0.34, 0.72, 1.06):
    add('    <path d="M%.0f,%.0f Q0,%.0f %.0f,%.0f" fill="none" stroke="%s" '
        'stroke-width="1.3" opacity=".65"/>'
        % (-NET_HALF_W * (1 - lvl * .42), -NET_HALF_H + lvl * NET_HALF_H * 1.5,
           NET_HALF_H * (1.1 + lvl),
           NET_HALF_W * (1 - lvl * .42), -NET_HALF_H + lvl * NET_HALF_H * 1.5, ARM_DK))
add("  </g></g>")
add("</g></g>")

add("</svg>")

svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
p = os.path.join(OUT, "intro.svg")
with open(p, "w", encoding="utf-8") as f:
    f.write(svg)
last = LEAD + (N - 1) * STAG + ENTER + HOVER + EXIT
print("intro.svg  %d bytes  (%d aircraft, %.0fs loop, name complete at %.0fs, still for %.0fs)"
      % (os.path.getsize(p), N, DUR_S,
         (LEAD + (N - 1) * STAG + ENTER + HOVER * .5) / 100 * DUR_S,
         (100 - last) / 100 * DUR_S))
