# -*- coding: utf-8 -*-
"""
What happens between a photograph and a box drawn round the thing in it.

A kernel slides over the pixels, and what it produces is not a picture but a
stack of feature maps: at the first layer, edges; a few layers down, textures;
deeper still, parts and whole objects. Each layer halves the resolution and
doubles the channels, so the network sees less detail and more meaning as it
goes. Then a detection head proposes far more boxes than there are objects, and
most of them are thrown away.

Four things here are the real mechanics rather than decoration:

  - The kernel is small and fixed — three by three — and never gets bigger. What
    grows is the RECEPTIVE FIELD: because each layer looks at the layer below,
    a single unit deep in the network is influenced by a wide patch of the
    original image. That is how a 3x3 window ends up recognising a whole car.
  - Resolution falls and channel count rises together. The numbers on the maps
    are the actual shapes a network of this kind produces.
  - Detection proposes many overlapping candidates and then suppresses them.
    Non-maximum suppression keeps the highest-scoring box and discards any that
    overlap it beyond a threshold. Nine candidates becoming three is the step
    most diagrams leave out, and it is the one that makes the output clean.
  - The scores are confidences, not certainties. They are shown as they are.

This describes object detection in general. Nothing here is specific to any
particular system.

House style: solid fills, no gradients, no filters.
"""

AEGEAN, CORAL = "#0077C8", "#F88379"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
VIOLET = "#7E6BC4"
SKY = "#F2EDE6"
GRID = "#E6DBCA"
INK = "#2E2A24"
INK_2 = "#5E5349"
MUTED = "#7D7266"
FAINT = "#A2988A"
RULE = "#D9D0C1"
CARD = "#FBF7F0"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

W, H = 1240, 410
DUR = 24.0
BAND_Y = 150
IMG = 176.0

IN_X, CONV_X, MAP_X, CAND_X, OUT_X = 44.0, 252.0, 416.0, 844.0, 1020.0

# (label, cells across, box size, channels) — resolution halves, channels double
LAYERS = [("112 x 112 x 64", 8, 8.4, "EDGES"),
          ("56 x 56 x 128", 6, 9.4, "TEXTURES"),
          ("28 x 28 x 256", 4, 11.5, "PARTS"),
          ("14 x 14 x 512", 3, 13.5, "OBJECTS")]
FIELD = ["3 PX", "7 PX", "15 PX", "31 PX"]

# boxes in the scene's own 176-unit space: (x, y, w, h, label, score)
# the last field is where the caption goes: the person stands between the two
# cars, so a label above it would be printed straight through the far car's
TRUTH = [(24.0, 100.0, 60.0, 40.0, "CAR", "0.94", "above"),
         (104.0, 88.0, 44.0, 32.0, "CAR", "0.87", "above"),
         (82.0, 96.0, 17.0, 36.0, "PERSON", "0.71", "below")]
# what the head proposes before anything is thrown away
CANDIDATES = [(24, 100, 60, 40, 1), (18, 96, 66, 47, 0), (31, 106, 52, 33, 0),
              (104, 88, 44, 32, 1), (99, 83, 54, 41, 0), (110, 93, 34, 24, 0),
              (82, 96, 17, 36, 1), (77, 91, 27, 45, 0), (86, 101, 12, 27, 0)]


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


def _stage(out, x, w, title, sub):
    out.append(_rr(x, BAND_Y - 34, w, 22, 6, _mix(SKY, INK, 0.05)))
    out.append(_txt(x + 9, BAND_Y - 19, title, 9.5, INK, "800", "start", "1.8"))
    out.append(_txt(x, BAND_Y + IMG + 26, sub, 8.5, FAINT, "600", "start", "1.2"))


def _scene():
    """The photograph, in its own 176-unit space, drawn once and re-used.

    Deliberately plain geometry: the point of the panel is the pipeline, and a
    scene that reads instantly at 176px leaves the attention where it belongs.
    """
    g = ['<symbol id="scene" viewBox="0 0 176 176">',
         '  <rect width="176" height="176" fill="%s"/>' % _mix(CARD, AEGEAN, 0.07),
         '  <rect y="92" width="176" height="84" fill="%s"/>' % _mix(CARD, BROWN, 0.20),
         '  <rect y="120" width="176" height="56" fill="%s"/>' % _mix(INK, CARD, 0.66),
         '  <path d="M0,148 H176" stroke="%s" stroke-width="2" stroke-dasharray="12 10"/>'
         % _mix(CARD, INK, 0.12)]
    for cx, cy in ((44, 40), (96, 28), (140, 46)):          # a little weather
        g.append('  <circle cx="%d" cy="%d" r="9" fill="%s"/>' % (cx, cy, _mix(CARD, AEGEAN, 0.02)))
    # near vehicle
    g.append('  <rect x="26" y="108" width="56" height="22" rx="5" fill="%s"/>' % AEGEAN)
    g.append('  <rect x="36" y="100" width="32" height="12" rx="4" fill="%s"/>'
             % _mix(AEGEAN, INK, 0.25))
    g.append('  <circle cx="38" cy="132" r="7" fill="%s"/>' % INK)
    g.append('  <circle cx="72" cy="132" r="7" fill="%s"/>' % INK)
    # far vehicle
    g.append('  <rect x="106" y="98" width="40" height="16" rx="4" fill="%s"/>' % CORAL)
    g.append('  <rect x="114" y="92" width="22" height="9" rx="3" fill="%s"/>'
             % _mix(CORAL, INK, 0.25))
    g.append('  <circle cx="115" cy="116" r="5" fill="%s"/>' % INK)
    g.append('  <circle cx="139" cy="116" r="5" fill="%s"/>' % INK)
    # figure
    g.append('  <circle cx="90" cy="101" r="6" fill="%s"/>' % _mix(INK, CARD, 0.15))
    g.append('  <rect x="85" y="108" width="11" height="18" rx="4" fill="%s"/>' % TEAMIST)
    g.append('  <rect x="86" y="125" width="4" height="9" fill="%s"/>' % _mix(INK, CARD, 0.3))
    g.append('  <rect x="92" y="125" width="4" height="9" fill="%s"/>' % _mix(INK, CARD, 0.3))
    # sign
    g.append('  <rect x="158" y="86" width="3" height="34" fill="%s"/>' % _mix(INK, CARD, 0.4))
    g.append('  <rect x="150" y="72" width="19" height="16" rx="3" fill="%s"/>' % BROWN)
    g.append("</symbol>")
    return g


def build(path="assets/vision.svg"):
    css = ["@keyframes fade{0%{opacity:0}}",
           "@keyframes glow{0%,100%{opacity:.2}50%{opacity:1}}",
           ".pulse{animation:glow 2.2s ease-in-out infinite}",
           ".kn{transform-box:fill-box;transform-origin:center}"]

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="How a vision model sees: a kernel slides over the pixels, '
           'feature maps go from edges to whole objects as resolution falls and channels rise, '
           'the detection head proposes nine candidate boxes, and non-maximum suppression keeps '
           'three">' % (W, H, W, H),
           "<title>How a Vision Model Sees</title>",
           '<defs><pattern id="vg" width="26" height="26" patternUnits="userSpaceOnUse">'
           '<circle cx="1.5" cy="1.5" r="1" fill="%s"/></pattern>' % GRID]
    out += _scene()
    out.append("__STYLE__</defs>")
    out.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, SKY))
    out.append('<rect width="%d" height="%d" fill="url(#vg)"/>' % (W, H))

    out.append(_txt(48, 46, "HOW A VISION MODEL SEES", 14, INK, "800", "start", "3.4"))
    out.append(_txt(W - 48, 46, "IN GENERAL · NOT ANY ONE SYSTEM", 12.5, FAINT, "600", "end", "2.2"))
    out.append('<path d="M48,60 H%d" stroke="%s" stroke-width="1.4" fill="none"/>' % (W - 48, RULE))
    out.append(_txt(48, 80, "PIXELS → CONVOLUTION → FEATURE MAPS → CANDIDATE BOXES → "
                            "SUPPRESSION → LABELS", 10.5, MUTED, "600", "start", "1.5"))

    # ── the photograph ───────────────────────────────────────────────────
    _stage(out, IN_X, IMG, "INPUT", "224 x 224 x 3")
    out.append('<use href="#scene" x="%.0f" y="%d" width="%.0f" height="%.0f"/>'
               % (IN_X, BAND_Y, IMG, IMG))
    out.append(_rr(IN_X, BAND_Y, IMG, IMG, 4, "none",
                   'stroke="%s" stroke-width="1.4"' % RULE))
    for k in range(1, 8):                       # the pixel grid it is really made of
        p = IN_X + k * IMG / 8.0
        out.append('<path d="M%.1f,%d V%.1f" stroke="%s" stroke-width="0.6" opacity=".5"/>'
                   % (p, BAND_Y, BAND_Y + IMG, CARD))
        q = BAND_Y + k * IMG / 8.0
        out.append('<path d="M%.0f,%.1f H%.1f" stroke="%s" stroke-width="0.6" opacity=".5"/>'
                   % (IN_X, q, IN_X + IMG, CARD))

    # the kernel, sliding over it in a raster
    # The window is 3 cells wide, so the last position it can take is IMG - 3
    # cells, not IMG. Stepping by a whole cell instead walks it off the bottom
    # right corner of the photograph.
    step = IMG / 8.0
    reach = IMG - step * 3
    stops, i, n_scan = [], 0, 4 * 8
    for r in range(4):
        for c in range(8):
            cc = c if r % 2 == 0 else 7 - c     # a boustrophedon scan, so it never jumps back
            at = 4.0 + i * (30.0 / float(n_scan))
            stops.append((at, "transform:translate(%.1fpx,%.1fpx)"
                          % (cc * reach / 7.0, r * reach / 3.0)))
            i += 1
    # and it retires once it has covered the frame, rather than parking on it
    stops.append((36.0, stops[-1][1] + ";opacity:1"))
    stops.append((39.0, stops[-1][1].split(";")[0] + ";opacity:0"))
    css.append(_kf("scan", [(0.0, stops[0][1])] + stops + [(100.0, stops[-1][1])]))
    css.append(".scan{animation:scan " + "%.1f" % DUR + "s steps(1,end) infinite}")
    out.append('<g class="scan">')
    out.append("  " + _rr(IN_X, BAND_Y, step * 3, step * 3, 2, "none",
                          'stroke="%s" stroke-width="2"' % CRIMSON))
    out.append("</g>")

    # ── the kernel itself ────────────────────────────────────────────────
    _stage(out, CONV_X, 132, "CONVOLVE", "3 x 3 · stride 1")
    kx, ky = CONV_X + 18, BAND_Y + 30
    wts = [0.11, -0.24, 0.08, -0.19, 0.62, -0.21, 0.07, -0.26, 0.13]
    for r in range(3):
        for c in range(3):
            v = wts[r * 3 + c]
            fill = _mix(CARD, AEGEAN if v > 0 else CORAL, min(0.85, abs(v) * 1.5 + 0.12))
            out.append(_rr(kx + c * 32, ky + r * 32, 29, 29, 4, fill,
                           'stroke="%s" stroke-width="1"' % _mix(RULE, INK, 0.15)))
            out.append(_txt(kx + c * 32 + 14.5, ky + r * 32 + 18.5, "%+.2f" % v, 6.6,
                            INK_2, "700", "middle", "0"))
    out.append(_txt(CONV_X + 66, ky + 116, "ONE WINDOW,", 8.5, MUTED, "700", "middle", "1.1"))
    out.append(_txt(CONV_X + 66, ky + 128, "ONE NUMBER OUT", 8.5, MUTED, "700", "middle", "1.1"))
    out.append(_txt(CONV_X + 66, ky + 148, "SLID OVER EVERY", 8.5, FAINT, "600", "middle", "1"))
    out.append(_txt(CONV_X + 66, ky + 159, "POSITION IN TURN", 8.5, FAINT, "600", "middle", "1"))

    # ── the feature maps ─────────────────────────────────────────────────
    _stage(out, MAP_X, 396, "FEATURE MAPS", "smaller and deeper at every layer")
    for li, (shape, n, cell, what) in enumerate(LAYERS):
        bx = MAP_X + li * 100
        side = n * cell
        by = BAND_Y + 26 + (100 - side) / 2.0
        appear = 34.0 + li * 7.0
        css.append(_kf("fm%d" % li, [(0.0, "opacity:0"), (max(0.0, appear - 0.01), "opacity:0"),
                                     (appear, "opacity:1"), (100.0, "opacity:1")]))
        css.append(".fm%d{animation:fm%d " % (li, li) + "%.1f" % DUR + "s linear infinite}")
        out.append('<g class="fm%d">' % li)
        for d in (2, 1):                        # the stack behind, hinting at channels
            out.append("  " + _rr(bx + d * 5, by - d * 5, side, side, 3,
                                  _mix(CARD, VIOLET, 0.10),
                                  'stroke="%s" stroke-width="1"' % _mix(RULE, VIOLET, 0.3)))
        for r in range(n):
            for c in range(n):
                # a deterministic response pattern: low layers fire on edges,
                # deep layers on a few concentrated regions
                h = (r * 37 + c * 17 + li * 91) % 13
                t = (0.08 + h / 15.0) if li < 2 else (0.05 + (h % 4) / 4.6)
                out.append("  " + _rr(bx + c * cell, by + r * cell, cell - 1.4, cell - 1.4, 1.5,
                                      _mix(CARD, VIOLET, min(0.86, t))))
        out.append("  " + _rr(bx, by, side, side, 3, "none",
                              'stroke="%s" stroke-width="1.2"' % _mix(RULE, VIOLET, 0.45)))
        out.append("  " + _txt(bx + side / 2.0, by + side + 16, shape, 7.6, INK_2,
                               "700", "middle", "0.6"))
        out.append("  " + _txt(bx + side / 2.0, by + side + 28, what, 7.4, FAINT,
                               "700", "middle", "1.2"))
        out.append("  " + _txt(bx + side / 2.0, by - 14, "FIELD " + FIELD[li], 7.2,
                               _mix(FAINT, INK, 0.15), "700", "middle", "0.9"))
        out.append("</g>")
        if li < len(LAYERS) - 1:
            out.append(_txt(bx + side + (100 - side) / 2.0, BAND_Y + 78, "→", 13,
                            _mix(FAINT, INK, 0.1), "700", "middle", "0", "fm%d" % (li + 1)))

    # ── candidates, then suppression ─────────────────────────────────────
    _stage(out, CAND_X, 144, "PROPOSE", "9 boxes, mostly wrong")
    out.append('<use href="#scene" x="%.0f" y="%d" width="144" height="144" opacity=".45"/>'
               % (CAND_X, BAND_Y + 16))
    out.append(_rr(CAND_X, BAND_Y + 16, 144, 144, 4, "none",
                   'stroke="%s" stroke-width="1.4"' % RULE))
    sc = 144.0 / 176.0
    for ci, (bx, by, bw, bh, keep) in enumerate(CANDIDATES):
        born = 58.0 + ci * 0.7
        gone = 74.0
        if keep:
            css.append(_kf("cd%d" % ci, [(0.0, "opacity:0"), (born - 0.01, "opacity:0"),
                                         (born, "opacity:1"), (100.0, "opacity:1")]))
        else:
            css.append(_kf("cd%d" % ci, [(0.0, "opacity:0"), (born - 0.01, "opacity:0"),
                                         (born, "opacity:.85"), (gone, "opacity:.85"),
                                         (gone + 3.0, "opacity:0"), (100.0, "opacity:0")]))
        css.append(".cd%d{animation:cd%d " % (ci, ci) + "%.1f" % DUR + "s linear infinite}")
        out.append(_rr(CAND_X + bx * sc, BAND_Y + 16 + by * sc, bw * sc, bh * sc, 2, "none",
                       'stroke="%s" stroke-width="%s" class="cd%d"%s'
                       % (AEGEAN if keep else _mix(MUTED, CARD, 0.25),
                          "1.9" if keep else "1.1", ci,
                          "" if keep else ' stroke-dasharray="3 2"')))
    css.append(_kf("nms", [(0.0, "opacity:0"), (73.9, "opacity:0"), (75.0, "opacity:1"),
                           (100.0, "opacity:1")]))
    css.append(".nms{animation:nms " + "%.1f" % DUR + "s linear infinite}")
    out.append(_txt(CAND_X + 72, BAND_Y + 176, "NON-MAX SUPPRESSION", 8, CRIMSON,
                    "800", "middle", "1.1", "nms"))
    out.append(_txt(CAND_X + 72, BAND_Y + 188, "DROP ANY OVERLAP > 0.5 IoU", 7.6, FAINT,
                    "600", "middle", "0.9", "nms"))

    # ── what comes out ───────────────────────────────────────────────────
    _stage(out, OUT_X, IMG, "OUTPUT", "3 boxes, with confidences")
    out.append('<use href="#scene" x="%.0f" y="%d" width="%.0f" height="%.0f"/>'
               % (OUT_X, BAND_Y, IMG, IMG))
    out.append(_rr(OUT_X, BAND_Y, IMG, IMG, 4, "none",
                   'stroke="%s" stroke-width="1.4"' % RULE))
    for bi, (bx, by, bw, bh, lab, score, side) in enumerate(TRUTH):
        born = 80.0 + bi * 2.0
        css.append(_kf("ob%d" % bi, [(0.0, "opacity:0"), (born - 0.01, "opacity:0"),
                                     (born, "opacity:1"), (100.0, "opacity:1")]))
        css.append(".ob%d{animation:ob%d " % (bi, bi) + "%.1f" % DUR + "s linear infinite}")
        x, y = OUT_X + bx, BAND_Y + by
        out.append('<g class="ob%d">' % bi)
        out.append("  " + _rr(x, y, bw, bh, 2, "none",
                              'stroke="%s" stroke-width="2"' % AEGEAN))
        tw = len(lab) * 5.4 + 26
        ly = max(BAND_Y, y - 13) if side == "above" else min(BAND_Y + IMG - 12, y + bh + 1)
        out.append("  " + _rr(x, ly, tw, 12, 2, AEGEAN))
        out.append("  " + _txt(x + 4, ly + 9, "%s %s" % (lab, score), 7.2,
                               CARD, "800", "start", "0.5"))
        out.append("</g>")

    out.append('<path d="M48,%d H%d" stroke="%s" stroke-width="1.4" fill="none"/>'
               % (H - 34, W - 48, RULE))
    out.append(_txt(48, H - 14, "THE KERNEL NEVER GROWS · THE RECEPTIVE FIELD DOES, "
                                "WHICH IS HOW A 3 x 3 WINDOW ENDS UP SEEING A WHOLE CAR",
                    10, FAINT, "600", "start", "1.4"))
    out.append("</svg>")

    svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote %s (%d layers, %d candidates → %d kept, %ds loop, %d KB)"
          % (path, len(LAYERS), len(CANDIDATES), len(TRUTH), int(DUR), len(svg) // 1024))
    return path


if __name__ == "__main__":
    build()
