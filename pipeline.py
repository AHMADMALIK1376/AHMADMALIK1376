# -*- coding: utf-8 -*-
"""
"Ship It" — side elevation of a build-and-deploy line.

A cargo drone flies in with project crates → robotic arm unloads them (and the crates
actually disappear off the bed as it does) → the belt runs the work through three
build stations, FRONTEND then BACKEND then DATABASE, each fed by its own tech silos
→ ASSEMBLE merges the three layers into a website → a second arm deploys it into the
live server rack, which starts broadcasting.

The unloading arm is gated on the delivery: it idles at the pick position while the
dock is empty and only runs its swing cycles while the drone is hovering there.

House rules: SOLID FILLS ONLY. No gradients, no filters, no glow.
Layout note: CSS `transform` OVERRIDES a `transform=` attribute on the same element,
so anything animated is nested inside a plain positioning <g>.
"""
import os

OUT = "assets"
W, H = 1340, 450
GROUND, BELT_Y, ITEM_Y = 376, 306, 288
DUR = "24s"

AEGEAN, CORAL, LEMON = "#0077C8", "#F88379", "#F2D24B"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
SKY, GRD, GRD_D = "#F2EDE6", "#DFD4C5", "#CDBFAC"
STEEL, STEEL_D, STEEL_X = "#DAD8D4", "#C0BDB6", "#A8A49C"
CREAM, WHITE, INK = "#FAF5EC", "#FFFFFF", "#5E5349"
BELTC, OUTLINE, BROWN_D = "#6E645B", "#B5A695", "#BC8A5F"
AEG_D, GREEN_D = "#005A96", "#7E9A1E"
SANS = "ui-sans-serif,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"

PERIOD = 100.0 / 6.0           # one production run = 1/6 of the loop
ARM_A_START = 16.0
ARM_B_START = 39.5
RUNS = 3
# the arm cycle: dwell empty at the truck (grip closes at .11), lift at .20, arrive
# at the belt at .50, release at .60, then swing back empty from .68
REL = [ARM_A_START + k * PERIOD + PERIOD * 0.60 for k in range(RUNS)]
PICKS = [ARM_A_START + k * PERIOD + PERIOD * 0.11 for k in range(RUNS)]
DEPLOYS = [ARM_B_START + k * PERIOD + PERIOD * 0.60 for k in range(RUNS)]

css, out = [], []
add = out.append


def rr(x, y, w, h, r, fill, extra=""):
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"%s/>'
            % (x, y, w, h, r, fill, (" " + extra) if extra else ""))


def ci(cx, cy, r, fill, extra=""):
    return '<circle cx="%s" cy="%s" r="%s" fill="%s"%s/>' % (cx, cy, r, fill, (" " + extra) if extra else "")


def txt(x, y, s, size, fill, weight="700", ls="0"):
    return ('<text x="%s" y="%s" font-family="%s" font-size="%s" font-weight="%s" fill="%s" '
            'letter-spacing="%s" text-anchor="middle">%s</text>' % (x, y, SANS, size, weight, fill, ls, s))


def tech(name, x, y, s=1.0):
    g = '<g transform="translate(%s,%s) scale(%s)">' % (x, y, s)
    if name == "react":
        g += ci(0, 0, 3.2, AEGEAN)
        for rot in (0, 60, -60):
            g += ('<ellipse rx="12" ry="4.6" fill="none" stroke="%s" stroke-width="2" '
                  'transform="rotate(%d)"/>' % (AEGEAN, rot))
    elif name == "python":
        g += rr(-10, -11, 10, 15, 4, AEGEAN) + rr(0, -4, 10, 15, 4, LEMON)
        g += ci(-6, -7, 1.6, WHITE) + ci(6, 7, 1.6, INK)
    elif name == "mongo":
        g += '<path d="M0,-13 C7.5,-6 7.5,4.5 0,12.5 C-7.5,4.5 -7.5,-6 0,-13 Z" fill="%s"/>' % TEAMIST
        g += '<path d="M0,-11 V11" stroke="%s" stroke-width="1.6" fill="none"/>' % GREEN_D
    elif name == "node":
        g += '<path d="M0,-12 L10.4,-6 L10.4,6 L0,12 L-10.4,6 L-10.4,-6 Z" fill="%s"/>' % GREEN_D
        g += txt(0, 4, "N", 11, WHITE)
    elif name == "sql":
        g += '<ellipse cy="-8" rx="11" ry="4.2" fill="%s"/>' % AEGEAN
        g += rr(-11, -8, 22, 16, 0, AEGEAN)
        g += '<ellipse cy="8" rx="11" ry="4.2" fill="%s"/>' % AEG_D
        g += '<ellipse cy="0" rx="11" ry="4.2" fill="none" stroke="%s" stroke-width="1.4"/>' % AEG_D
    elif name == "ts":
        g += rr(-12, -12, 24, 24, 4, AEGEAN) + txt(0, 5, "TS", 12, WHITE)
    return g + "</g>"


# ══ things that ride the belt ═════════════════════════════════════════
def crate(s=1.0):
    g = '<g transform="scale(%s)">' % s
    g += rr(-19, -17, 38, 34, 4, BROWN, 'stroke="%s" stroke-width="2"' % BROWN_D)
    g += '<path d="M-19,-4 H19 M-19,7 H19" stroke="%s" stroke-width="1.8" fill="none"/>' % BROWN_D
    g += rr(-11, -14, 22, 8, 2, CREAM)
    return g + "</g>"


def layer(colr, y, s=1.0, lines=WHITE):
    g = rr(-25, y, 50, 17, 3, colr, 'stroke="%s" stroke-width="1.6"' % OUTLINE)
    g += rr(-19, y + 5, 24, 3, 1.5, lines) + rr(-19, y + 10, 14, 3, 1.5, lines)
    return g


def stack(n, s=1.0):
    """1 = frontend, 2 = +backend, 3 = +database."""
    cols = [AEGEAN, TEAMIST, CORAL]
    g = '<g transform="scale(%s)">' % s
    for i in range(n):
        g += layer(cols[i], -26 + i * 19)
    return g + "</g>"


def website(s=1.0):
    g = '<g transform="scale(%s)">' % s
    g += rr(-32, -26, 64, 52, 5, CREAM, 'stroke="%s" stroke-width="2"' % OUTLINE)
    g += rr(-32, -26, 64, 13, 5, STEEL_D)
    for i, c in enumerate((CRIMSON, LEMON, TEAMIST)):
        g += ci(-24 + i * 8, -19, 3, c)
    g += rr(-26, -8, 20, 20, 3, AEGEAN)
    g += rr(-2, -8, 28, 5, 2, TEAMIST) + rr(-2, 0, 28, 5, 2, CORAL)
    g += rr(-2, 8, 18, 5, 2, STEEL_X)
    return g + "</g>"


def drone(bodyc, accentc, cargo):
    """Side-elevation cargo quadcopter. Drawn with the ground at y=0 so it drops
    straight into the same transform the truck used; the pallet hangs at exactly
    the height the unloading arm reaches."""
    g = rr(24, -92, 144, 13, 4, STEEL_X, 'stroke="%s" stroke-width="2"' % OUTLINE)
    g += rr(24, -83, 144, 5, 2, INK)
    g += ('<path d="M78,-236 L40,-92 M114,-236 L152,-92" stroke="%s" stroke-width="2.5" '
          'fill="none" stroke-linecap="round"/>' % INK)
    g += rr(18, -262, 56, 8, 4, INK) + rr(118, -262, 56, 8, 4, INK)
    g += rr(60, -272, 72, 36, 14, bodyc, 'stroke="%s" stroke-width="2"' % OUTLINE)
    g += rr(108, -266, 20, 16, 5, CREAM)
    g += rr(66, -262, 26, 7, 3.5, accentc)
    g += rr(84, -240, 24, 9, 3, STEEL_X)
    for i, rx in enumerate((30, 162)):
        g += rr(rx - 4, -276, 8, 16, 3, STEEL_X)
        # a flat disc plus a fast-squashing blade reads as spin without any blur
        g += '<ellipse cx="%d" cy="-278" rx="34" ry="4.5" fill="%s" opacity=".26"/>' % (rx, INK)
        g += ('<g transform="translate(%d,-278)"><g class="rotor" style="animation-delay:-%.2fs">'
              '%s</g></g>' % (rx, i * 0.07, rr(-34, -2.2, 68, 4.4, 2.2, INK)))
    g += ci(64, -254, 4.5, CRIMSON, 'class="lamp"')
    return g + cargo


# ══ keyframe builders ═════════════════════════════════════════════════
def arm_keyframes(idx, start):
    """Idle empty at the pick angle, run RUNS swing cycles, then idle again.

    The dwells matter: the arm has to arrive empty, sit still while the gripper
    closes, and only then lift. Same in reverse at the drop-off. Without the
    dwell the load looks like it teleports into the claw.
    """
    # VERIFIED BY RENDER: rotate(+45) swings the arm DOWN-LEFT (the pick side),
    # rotate(-45) swings it DOWN-RIGHT (the drop side). Getting these backwards is
    # what made the load appear over the belt and vanish over the truck.
    k = ["0%,{:.2f}%{{transform:rotate(45deg)}}".format(start)]
    p = ["0%,{:.2f}%{{opacity:0}}".format(start + PERIOD * 0.08)]
    c_ = ["0%,{:.2f}%{{transform:scaleX(1.35)}}".format(start + PERIOD * 0.06)]
    for c in range(RUNS):
        s = start + c * PERIOD
        k.append("{:.2f}%{{transform:rotate(45deg)}}".format(s + PERIOD * 0.20))
        k.append("{:.2f}%{{transform:rotate(-45deg)}}".format(s + PERIOD * 0.50))
        k.append("{:.2f}%{{transform:rotate(-45deg)}}".format(s + PERIOD * 0.68))
        k.append("{:.2f}%{{transform:rotate(45deg)}}".format(s + PERIOD))
        p.append("{:.2f}%{{opacity:0}}".format(s + PERIOD * 0.08))
        p.append("{:.2f}%{{opacity:1}}".format(s + PERIOD * 0.11))
        p.append("{:.2f}%{{opacity:1}}".format(s + PERIOD * 0.57))
        p.append("{:.2f}%{{opacity:0}}".format(s + PERIOD * 0.60))
        # claw opens on approach, clamps shut on the load, springs open to release
        c_.append("{:.2f}%{{transform:scaleX(1.35)}}".format(s + PERIOD * 0.07))
        c_.append("{:.2f}%{{transform:scaleX(1)}}".format(s + PERIOD * 0.12))
        c_.append("{:.2f}%{{transform:scaleX(1)}}".format(s + PERIOD * 0.58))
        c_.append("{:.2f}%{{transform:scaleX(1.35)}}".format(s + PERIOD * 0.62))
    k.append("100%{transform:rotate(45deg)}")
    p.append("100%{opacity:0}")
    c_.append("100%{transform:scaleX(1.35)}")
    css.append(".au%d{transform-origin:0 0;animation:au%d %s ease-in-out infinite}" % (idx, idx, DUR))
    css.append(".ap%d{transform-origin:0 0;animation:ap%d %s ease-in-out infinite}" % (idx, idx, DUR))
    css.append(".aw%d{animation:aw%d %s linear infinite}" % (idx, idx, DUR))
    css.append(".ac%d{transform-origin:0 0;animation:ac%d %s ease-in-out infinite}" % (idx, idx, DUR))
    css.append("@keyframes au%d{%s}" % (idx, "".join(k)))
    # gripper counter-rotates so the load hangs level
    css.append("@keyframes ap%d{%s}" % (idx, "".join(k).replace("-45deg", "@").replace("45deg", "-45deg").replace("@", "45deg")))
    css.append("@keyframes aw%d{%s}" % (idx, "".join(p)))
    css.append("@keyframes ac%d{%s}" % (idx, "".join(c_)))


def item_keyframes(name, x0, x1, offset, travel, hold=0.0):
    """One pass per production run: appear at x0, ride to x1, vanish."""
    k = ["0%{{transform:translate({}px,{}px);opacity:0}}".format(x0, ITEM_Y)]
    for r in REL:
        s = r + offset
        k.append("{:.2f}%{{transform:translate({}px,{}px);opacity:0}}".format(s, x0, ITEM_Y))
        k.append("{:.2f}%{{transform:translate({}px,{}px);opacity:1}}".format(s + 0.25, x0, ITEM_Y))
        k.append("{:.2f}%{{transform:translate({}px,{}px);opacity:1}}".format(s + travel, x1, ITEM_Y))
        if hold:
            k.append("{:.2f}%{{transform:translate({}px,{}px);opacity:1}}".format(s + travel + hold, x1, ITEM_Y))
        k.append("{:.2f}%{{transform:translate({}px,{}px);opacity:0}}".format(s + travel + hold + 0.3, x1, ITEM_Y))
    k.append("100%{{transform:translate({}px,{}px);opacity:0}}".format(x0, ITEM_Y))
    css.append(".%s{animation:%s %s linear infinite}" % (name, name, DUR))
    css.append("@keyframes %s{%s}" % (name, "".join(k)))


# ══ static motion ═════════════════════════════════════════════════════
css += [
    ".beltmove{animation:beltmove 1.1s linear infinite}",
    "@keyframes beltmove{from{transform:translateX(0)}to{transform:translateX(26px)}}",
    ".press{animation:press 2s ease-in-out infinite}",
    ".needle{transform-origin:0 0;animation:needle 2s ease-in-out infinite}",
    "@keyframes needle{0%,100%{transform:rotate(-52deg)}50%{transform:rotate(52deg)}}",
    "@keyframes press{0%,100%{transform:translateY(0)}50%{transform:translateY(16px)}}",
    ".lamp{animation:lamp 1.6s steps(1,end) infinite}",
    "@keyframes lamp{0%,49%{opacity:1}50%,100%{opacity:.25}}",
    ".lamp2{animation:lamp 1.6s steps(1,end) infinite;animation-delay:-.8s}",
    ".sig{transform-origin:0 0;animation:sig 2.6s ease-out infinite}",
    "@keyframes sig{0%{transform:scale(.35);opacity:.75}100%{transform:scale(1.5);opacity:0}}",
    ".roll{transform-origin:0 0;animation:roll .9s linear infinite}",
    ".fan{transform-origin:0 0;animation:roll .6s linear infinite}",
    "@keyframes roll{to{transform:rotate(360deg)}}",
    # wheels turn only while the truck is moving; 1800deg is 5 whole turns, so the
    # loop closes on itself with no visible snap
    ".rotor{transform-origin:0 0;animation:rotor .22s linear infinite}",
    "@keyframes rotor{0%,100%{transform:scaleX(1)}50%{transform:scaleX(.12)}}",
    ".hover{animation:hover 2.8s ease-in-out infinite}",
    "@keyframes hover{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}",
    # Two aircraft share the dock. The first carries the crates for runs one
    # and two and leaves; the second is already inbound as it goes, and is
    # parked in time for run three. The dwell windows are set from PICKS, so
    # neither can be away while its own crate is due to be lifted.
    ".tin{animation:tin %s ease-in-out infinite}" % DUR,
    ("@keyframes tin{0%,3%{transform:translate(-340px,330px)}"
     "12%,40%{transform:translate(20px,376px)}"
     "50%,100%{transform:translate(-340px,330px)}}"),
    ".tin2{animation:tin2 %s ease-in-out infinite}" % DUR,
    ("@keyframes tin2{0%,42%{transform:translate(-340px,330px)}"
     "50%,72%{transform:translate(20px,376px)}"
     "82%,100%{transform:translate(-340px,330px)}}"),
]
for i in range(6):
    css.append(".dp%d{animation:dp 1.8s ease-in infinite;animation-delay:-%.2fs}" % (i, i * 0.3))
css.append("@keyframes dp{0%{transform:translateY(0);opacity:0}20%{opacity:1}"
           "80%{opacity:1}100%{transform:translateY(30px);opacity:0}}")

# crates vanish off the bed as the arm takes them, and are restocked off-screen
for i, pk in enumerate(PICKS):
    css.append(".cr%d{animation:cr%d %s steps(1,end) infinite}" % (i, i, DUR))
    css.append("@keyframes cr%d{0%%,%.2f%%{opacity:1}%.2f%%,77%%{opacity:0}78%%,100%%{opacity:1}}"
               % (i, pk - 0.6, pk))

arm_keyframes(1, ARM_A_START)
arm_keyframes(2, ARM_B_START)
item_keyframes("it0", 349, 440, 0.0, 3.0)          # raw crate
item_keyframes("it1", 496, 595, 3.6, 3.4)          # frontend
item_keyframes("it2", 651, 750, 7.4, 3.4)          # + backend
item_keyframes("it3", 806, 880, 11.2, 2.6)         # + database
item_keyframes("it4", 961, 1015, 14.2, 2.3, 1.4)   # assembled website


def arm(idx, bx, shoulder_y, seg, payload):
    """Column, shoulder, upper arm, wrist, claw.

    The detail is all structural: a bolted base plate, hazard banding up the
    column, a cable conduit, a counterweight behind the shoulder, and a hydraulic
    ram alongside the upper arm. The ram is nested inside the same rotating group
    as the arm, so it swings with it instead of floating loose.
    """
    col_h = GROUND - shoulder_y
    g = rr(bx - 36, GROUND - 20, 72, 20, 4, STEEL_X, 'stroke="%s" stroke-width="2"' % OUTLINE)
    for bolt in (-26, -9, 9, 26):                      # anchor bolts in the floor plate
        g += ci(bx + bolt, GROUND - 10, 3.2, INK)
    g += rr(bx - 21, shoulder_y, 42, col_h, 6, LEMON,
            'stroke="%s" stroke-width="2"' % OUTLINE)
    # hazard banding, cut to the column width
    for hb in range(4):
        hy = shoulder_y + 40 + hb * 13
        if hy + 7 < GROUND - 22:
            g += '<path d="M%d,%d l10,-9 h9 l-10,9 Z" fill="%s"/>' % (bx - 19, hy, INK)
            g += '<path d="M%d,%d l10,-9 h9 l-10,9 Z" fill="%s"/>' % (bx - 1, hy, INK)
    g += rr(bx - 21, shoulder_y + 26, 42, 7, 0, INK)
    g += rr(bx + 13, shoulder_y + 18, 6, col_h - 40, 3, STEEL_D)     # cable conduit
    for cly in range(4):
        g += rr(bx + 12, shoulder_y + 30 + cly * 26, 8, 3, 1.5, STEEL_X)
    g += rr(bx - 21, shoulder_y, 42, 11, 5, INK)
    g += '<g transform="translate(%s,%s)"><g class="au%d">' % (bx, shoulder_y + 6, idx)
    g += rr(-19, -13, 38, 20, 6, STEEL_D, 'stroke="%s" stroke-width="2"' % OUTLINE)  # counterweight
    g += rr(-15, -9, 30, 5, 2.5, INK)
    g += rr(-12, 0, 24, seg, 12, LEMON, 'stroke="%s" stroke-width="2"' % OUTLINE)
    g += rr(-12, seg * 0.42, 24, 9, 0, INK)
    g += rr(9, seg * 0.16, 9, seg * 0.5, 4, STEEL_X,                 # hydraulic barrel
            'stroke="%s" stroke-width="1.6"' % OUTLINE)
    g += rr(11.5, seg * 0.62, 4, seg * 0.24, 2, STEEL_D)             # ram rod
    g += ci(0, seg * 0.42 + 4.5, 3, STEEL_X)
    g += '<g transform="translate(0,%s)"><g class="ap%d">' % (seg, idx)
    g += rr(-16, -7, 32, 14, 3, INK)
    g += rr(-11, -4, 22, 4, 2, STEEL_X)                              # wrist plate
    g += '<g class="ac%d">%s%s</g>' % (idx, rr(-16, 4, 6, 17, 2, INK), rr(10, 4, 6, 17, 2, INK))
    g += '<g class="aw%d"><g transform="translate(0,14)">%s</g></g>' % (idx, payload)
    g += "</g></g></g></g>"
    g += ci(bx, shoulder_y + 6, 13, INK) + ci(bx, shoulder_y + 6, 6, STEEL_X)
    for bl in ((-7, -7), (7, -7), (-7, 7), (7, 7)):                  # shoulder bolt circle
        g += ci(bx + bl[0], shoulder_y + 6 + bl[1], 1.7, STEEL_D)
    return g


# ══ build ═════════════════════════════════════════════════════════════
add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
    'aria-label="Robotic line building a website from frontend, backend and database, then deploying '
    'it to a live server">' % (W, H, W, H))
add("<title>Ship It</title>")
add("<defs>")
add('<clipPath id="bc"><rect x="300" y="306" width="740" height="11" rx="3"/></clipPath>')
add("__STYLE__")
add("</defs>")
add(rr(0, 0, W, H, 0, SKY))
add(rr(0, GROUND, W, H - GROUND, 0, GRD))
add(rr(0, GROUND, W, 4, 0, GRD_D))
for dx in range(30, W, 70):
    add(rr(dx, 424, 34, 5, 2.5, GRD_D))

# ── silos, two per build station ──────────────────────────────────────
SILOS = [(402, "react", AEGEAN), (472, "ts", AEGEAN),
         (557, "node", TEAMIST), (627, "python", LEMON),
         (712, "mongo", TEAMIST), (782, "sql", CRIMSON)]
for i, (cx, tname, capc) in enumerate(SILOS):
    add(rr(cx - 31, 54, 62, 82, 8, CREAM, 'stroke="%s" stroke-width="2"' % OUTLINE))
    add(rr(cx - 31, 54, 62, 14, 7, capc))
    add('<path d="M%d,136 H%d L%d,166 H%d Z" fill="%s"/>' % (cx - 31, cx + 31, cx + 10, cx - 10, STEEL_D))
    add(tech(tname, cx, 102, 1.1))
    add(rr(cx - 7, 166, 14, 34, 0, STEEL_X))
    add('<g class="dp%d">%s</g>' % (i, tech(tname, cx, 172, 0.55)))

# ── build stations ────────────────────────────────────────────────────
STATIONS = [(370, 510, 440, "FRONTEND", AEGEAN),
            (525, 665, 595, "BACKEND", TEAMIST),
            (680, 820, 750, "DATABASE", CORAL),
            (835, 975, 905, "ASSEMBLE", LEMON)]
for si, (x0, x1, chx, label, colr) in enumerate(STATIONS):
    add(rr(x0, 200, x1 - x0, 80, 10, STEEL, 'stroke="%s" stroke-width="2"' % OUTLINE))
    add(rr(x0, 268, x1 - x0, 12, 6, STEEL_D))
    add(rr(x0, 200, x1 - x0, 14, 6, colr))
    add(rr(x0 + 12, 224, 48, 38, 4, STEEL_D))
    add(rr(x0 + 16, 228, 40, 30, 3, AEGEAN))
    for li, lw in enumerate((22, 30, 16)):
        add(rr(x0 + 20, 234 + li * 8, lw, 3, 1.5, CREAM))
    add(ci(x0 + 74, 232, 6, TEAMIST, 'class="lamp"'))
    add(ci(x0 + 74, 250, 6, LEMON, 'class="lamp2"'))
    # station number, stencilled on the coloured header
    add(rr(x0 + 8, 202, 20, 11, 2, INK))
    add(txt(x0 + 18, 211, str(si + 1), 9, CREAM))
    # twin piston rods above the chute head
    for pr in (chx + 14, chx + 42):
        add(rr(pr - 3, 176, 6, 26, 3, STEEL_X))
        add('<g transform="translate(%d,202)"><g class="press">%s</g></g>'
            % (pr, rr(-4, -8, 8, 12, 3, STEEL_D)))
    if label != "ASSEMBLE":
        add(rr(chx, 200, 56, 140, 6, STEEL_D, 'stroke="%s" stroke-width="2"' % OUTLINE))
        add(rr(chx, 200, 56, 14, 6, colr))
        add(rr(chx + 8, 226, 40, 44, 4, INK))
        add('<g class="press">' + rr(chx + 13, 230, 30, 14, 3, colr) + "</g>")
        # the gauge lives on the chute face, below the window, where nothing covers it
        add(ci(chx + 28, 300, 14, CREAM, 'stroke="%s" stroke-width="2"' % OUTLINE))
        add(ci(chx + 28, 300, 2.4, INK))
        add('<g transform="translate(%d,300)"><g class="needle">%s</g></g>'
            % (chx + 28, rr(-1.3, -11, 2.6, 12, 1.3, CRIMSON)))
        for tick in (-52, 0, 52):
            add('<g transform="translate(%d,300) rotate(%d)">%s</g>'
                % (chx + 28, tick, rr(-0.9, -13, 1.8, 4, 0.9, INK)))
    add(txt((x0 + x1) / 2.0, 367, label, 17, INK, ls="2"))

# ── conveyor ──────────────────────────────────────────────────────────
add(rr(300, 316, 740, 22, 4, STEEL_D))
for rx in range(314, 1040, 44):
    add(ci(rx, 327, 9, STEEL))
    add('<g transform="translate(%d,327)"><g class="roll">%s</g></g>'
        % (rx, rr(-1.4, -7, 2.8, 14, 1.4, STEEL_X)))
add(rr(300, BELT_Y, 740, 11, 3, BELTC))
add('<g clip-path="url(#bc)"><g class="beltmove">')
for dx in range(274, 1074, 26):
    add(rr(dx, BELT_Y, 13, 11, 0, "#8A8078"))
add("</g></g>")
add(rr(296, 338, 14, 38, 3, STEEL_X))
add(rr(1030, 338, 14, 38, 3, STEEL_X))

# ── work in progress ──────────────────────────────────────────────────
add('<g class="it0">%s</g>' % crate(0.78))
add('<g class="it1">%s</g>' % stack(1, 0.9))
add('<g class="it2">%s</g>' % stack(2, 0.9))
add('<g class="it3">%s</g>' % stack(3, 0.9))
add('<g class="it4">%s</g>' % website(0.86))

# ── the assembler ─────────────────────────────────────────────────────
# The three layers arrive stacked but loose. Two side clamps swing in, a ram
# comes down, and the finished site leaves as one piece. The timings are derived
# from REL rather than guessed: it3 finishes its run at REL+13.8 and it4 appears
# at REL+14.2, so the clamps have to be shut across that handover or the site
# would appear to assemble itself in mid-air.
CLAMP_IN, CLAMP_OUT = 13.3, 15.2
_cl, _cr, _rm, _wd = [], [], [], []
for _r in REL:
    for arr, out_v, in_v in ((_cl, "translateX(0)", "translateX(30px)"),
                             (_cr, "translateX(0)", "translateX(-30px)"),
                             (_rm, "translateY(0)", "translateY(26px)")):
        arr.append("{:.2f}%{{transform:{}}}".format(_r + CLAMP_IN - 1.2, out_v))
        arr.append("{:.2f}%{{transform:{}}}".format(_r + CLAMP_IN, in_v))
        arr.append("{:.2f}%{{transform:{}}}".format(_r + CLAMP_OUT - 0.5, in_v))
        arr.append("{:.2f}%{{transform:{}}}".format(_r + CLAMP_OUT, out_v))
    _wd.append("{:.2f}%{{opacity:0;transform:scale(.4)}}".format(_r + 13.9))
    _wd.append("{:.2f}%{{opacity:1;transform:scale(1)}}".format(_r + 14.2))
    _wd.append("{:.2f}%{{opacity:0;transform:scale(1.9)}}".format(_r + 15.0))
for nm, arr, rest in (("clL", _cl, "translateX(0)"), ("clR", _cr, "translateX(0)"),
                      ("ram", _rm, "translateY(0)")):
    css.append("@keyframes %s{0%%{transform:%s}%s100%%{transform:%s}}"
               % (nm, rest, "".join(arr), rest))
    css.append(".%s{animation:%s %s ease-in-out infinite}" % (nm, nm, DUR))
css.append("@keyframes wld{0%%{opacity:0}%s100%%{opacity:0}}" % "".join(_wd))
css.append(".wld{transform-origin:0 0;animation:wld %s ease-out infinite}" % DUR)

AX = 933                                   # where the ASSEMBLE chute would stand
add(rr(AX - 62, 196, 124, 16, 5, STEEL_D, 'stroke="%s" stroke-width="2"' % OUTLINE))
add(rr(AX - 62, 196, 124, 6, 3, LEMON))
for gx in (AX - 56, AX + 48):              # frame legs, down to the belt
    add(rr(gx - 5, 210, 10, 96, 4, STEEL_X, 'stroke="%s" stroke-width="1.6"' % OUTLINE))
    for bolt in range(3):
        add(ci(gx, 226 + bolt * 30, 2.4, STEEL_D))
# the ram, on its rail
add(rr(AX - 4, 210, 8, 30, 4, STEEL_D))
add('<g transform="translate(%d,212)"><g class="ram">%s%s%s%s</g></g>'
    % (AX, rr(-11, 0, 22, 40, 5, STEEL_X, 'stroke="%s" stroke-width="1.8"' % OUTLINE),
       rr(-32, 36, 64, 20, 5, LEMON, 'stroke="%s" stroke-width="2"' % OUTLINE),
       rr(-25, 41, 50, 6, 3, INK),
       ci(0, 20, 5, STEEL_D)))
# jaws that close on the stack from both sides
add('<g transform="translate(%d,262)"><g class="clL">%s%s%s</g></g>'
    % (AX - 60, rr(0, 0, 40, 14, 4, STEEL_D, 'stroke="%s" stroke-width="1.6"' % OUTLINE),
       rr(34, -14, 12, 42, 4, LEMON, 'stroke="%s" stroke-width="2"' % OUTLINE),
       rr(36, -8, 8, 6, 2, INK)))
add('<g transform="translate(%d,262)"><g class="clR">%s%s%s</g></g>'
    % (AX + 20, rr(6, 0, 40, 14, 4, STEEL_D, 'stroke="%s" stroke-width="1.6"' % OUTLINE),
       rr(-6, -14, 12, 42, 4, LEMON, 'stroke="%s" stroke-width="2"' % OUTLINE),
       rr(-4, -8, 8, 6, 2, INK)))
add('<g transform="translate(%d,290)"><g class="wld">%s</g></g>'
    % (AX, '<path d="M-19,0 L-6,-6 L0,-20 L6,-6 L19,0 L6,6 L0,20 L-6,6 Z" fill="%s"/>' % LEMON))

# ── live server rack ──────────────────────────────────────────────────
css += [
    "@keyframes pbfill{0%{transform:scaleX(0)}72%,90%{transform:scaleX(1)}100%{transform:scaleX(0)}}",
    "@keyframes tbar{0%,100%{transform:scaleY(.22)}50%{transform:scaleY(1)}}",
    ".dpul{transform-origin:0 0;animation:dpul %s ease-out infinite}" % DUR,
]
# the rack reacts the moment a site lands in it
_pl = ["0%{transform:scale(.3);opacity:0}"]
for _d in DEPLOYS:
    _pl.append("{:.2f}%{{transform:scale(.3);opacity:0}}".format(_d))
    _pl.append("{:.2f}%{{transform:scale(.5);opacity:.9}}".format(_d + 0.4))
    _pl.append("{:.2f}%{{transform:scale(2.3);opacity:0}}".format(_d + 4.5))
_pl.append("100%{transform:scale(2.3);opacity:0}")
css.append("@keyframes dpul{%s}" % "".join(_pl))

# bundled cabling, drawn first so the cabinet sits in front of it
for cx0, col in ((1318, TEAMIST), (1325, AEGEAN), (1332, CORAL)):
    add('<path d="M1300,168 C%d,200 %d,262 %d,%d" fill="none" stroke="%s" stroke-width="5" '
        'stroke-linecap="round"/>' % (cx0, cx0 + 3, cx0 - 6, GROUND - 4, col))
add(rr(1150, 120, 162, GROUND - 120, 10, STEEL, 'stroke="%s" stroke-width="2"' % OUTLINE))
add(rr(1150, 120, 162, 18, 8, INK))
add(txt(1231, 158, "LIVE SERVER", 16, INK, ls="1.6"))
for i in range(3):
    sy = 172 + i * 44
    add(rr(1162, sy, 138, 34, 4, STEEL_D))
    css.append(".pb%d{transform-origin:0 0;animation:pbfill 2.6s ease-in-out infinite;"
               "animation-delay:-%.1fs}" % (i, i * 0.75))
    add(rr(1170, sy + 9, 90, 8, 4, STEEL_X))
    add('<g transform="translate(1170,%d)"><rect class="pb%d" width="90" height="8" rx="4" '
        'fill="%s"/></g>' % (sy + 9, i, (TEAMIST, AEGEAN, TEAMIST)[i]))
    add(ci(1272, sy + 24, 5, TEAMIST, 'class="lamp"' if i % 2 == 0 else 'class="lamp2"'))
    add(ci(1286, sy + 24, 5, AEGEAN, 'class="lamp2"' if i % 2 == 0 else 'class="lamp"'))
    # each unit named, and cooled by its own fan
    add(txt(1195, sy + 29, ("WEB", "API", "DB")[i], 8, STEEL_X, ls="1.2"))
    add(ci(1280, sy + 10, 8.5, STEEL_X))
    add('<g transform="translate(1280,%d)"><g class="fan" style="animation-delay:-%.1fs">'
        '%s%s</g></g>' % (sy + 10, i * 0.35,
                          rr(-7.5, -1.4, 15, 2.8, 1.4, STEEL_D),
                          rr(-1.4, -7.5, 2.8, 15, 1.4, STEEL_D)))

# live traffic readout at the foot of the rack
for i in range(6):
    css.append(".tb%d{transform-origin:0 0;animation:tbar 1.9s ease-in-out infinite;"
               "animation-delay:-%.2fs}" % (i, i * 0.28))
    add('<g transform="translate(%d,344)"><rect class="tb%d" x="0" y="-36" width="15" height="36" '
        'rx="2" fill="%s"/></g>' % (1168 + i * 23, i, (TEAMIST, AEGEAN)[i % 2]))

# rack rails, punched the way a real cabinet is
for rail in (1156, 1300):
    for hy in range(150, GROUND - 40, 14):
        add(rr(rail - 2, hy, 4, 6, 1.5, STEEL_D))
# network switch across the foot of the cabinet, ports blinking
add(rr(1162, 302, 138, 20, 3, INK))
for i in range(8):
    add(ci(1172 + i * 16, 312, 3.2, (TEAMIST, AEGEAN)[i % 2],
           'class="%s"' % ("lamp" if i % 3 else "lamp2")))
add(txt(1288, 316, "SW", 8, STEEL_X))
add(txt(1231, 367, "DEPLOY", 17, INK, ls="2"))
add('<g transform="translate(1213,289)"><circle class="dpul" r="26" fill="none" stroke="%s" '
    'stroke-width="4"/></g>' % TEAMIST)
for i, d in enumerate(("0s", "-.87s", "-1.74s")):
    add('<g transform="translate(1231,104)"><g class="sig" style="animation-delay:%s">'
        '<path d="M-26,0 A26,26 0 0,1 26,0" fill="none" stroke="%s" stroke-width="4" '
        'stroke-linecap="round"/></g></g>' % (d, TEAMIST))

# ── inbound truck, crates depleting as they are lifted ────────────────
# crates 0 and 1 ride the first aircraft, crate 2 the second, matching PICKS
cargo_a = ""
for i, cx in enumerate((60, 116)):
    cargo_a += '<g class="cr%d"><g transform="translate(%d,-104)">%s</g></g>' % (i, cx, crate(0.72))
cargo_b = '<g class="cr2"><g transform="translate(88,-104)">%s</g></g>' % crate(0.72)
add(rr(26, 356, 148, 16, 4, STEEL_X))            # landing pad stays when the drone is out
add(rr(40, 361, 24, 6, 3, LEMON)) 
add(rr(96, 361, 24, 6, 3, LEMON))
add(rr(136, 361, 24, 6, 3, LEMON))
add('<g class="tin"><g class="hover">%s</g></g>' % drone(AEGEAN, LEMON, cargo_a))
add('<g class="tin2"><g class="hover" style="animation-delay:-1.4s">%s</g></g>'
    % drone(TEAMIST, CORAL, cargo_b))

# ── robots ────────────────────────────────────────────────────────────
add(arm(1, 250, 170, 140, crate(0.66)))
add(arm(2, 1114, 170, 140, website(0.6)))

add("</svg>")
svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
p = os.path.join(OUT, "pipeline.svg")
with open(p, "w", encoding="utf-8") as f:
    f.write(svg)
print("pipeline.svg  %d bytes" % os.path.getsize(p))
