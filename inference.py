# -*- coding: utf-8 -*-
"""
What actually happens when someone asks a model a question.

The prompt is split into tokens, the tokens become vectors, attention decides
which earlier tokens matter, the network turns that into a score for every word
it knows, one is sampled, and then the whole thing runs again with that word
added to the input. The loop is the point: a model does not write an answer, it
predicts one token and then re-reads everything including what it just said.

Three details here are the real mechanics rather than decoration:

  - the attention grid is lower-triangular, because a token can only attend to
    itself and what came before it. That mask is what makes generation causal.
  - the context strip grows by one token per step, and the new token is the one
    just sampled, which is what the feedback arc is showing.
  - the logits are a distribution over candidates, not a single answer. The bar
    that wins is the one that gets sampled; the others were genuinely in the
    running.

This describes language models in general. Nothing here is specific to any
particular system.

House style: solid fills, no gradients, no filters.
"""
import math

AEGEAN, CORAL = "#0077C8", "#F88379"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
VIOLET = "#7E6BC4"
SKY = "#F2EDE6"
GRID = "#E6DBCA"
TRACK = "#E0D6C4"
INK = "#2E2A24"
INK_2 = "#5E5349"
MUTED = "#7D7266"
FAINT = "#A2988A"
RULE = "#D9D0C1"
CARD = "#FBF7F0"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

W, H = 1240, 600
DUR = 18.0
LEAD = 8.0                       # settling in before the first token is produced
STEPS = 4
SPAN = (100.0 - LEAD) / STEPS    # one generated token

PROMPT = "how does a model answer?"
CTX = ["how", "does", "a", "model", "answer", "?"]

# candidates the model weighs at each step, most likely first
CANDIDATES = [
    [("It", .42), ("The", .21), ("A", .13), ("Each", .09), ("One", .06)],
    [("predicts", .51), ("generates", .19), ("outputs", .11), ("writes", .08), ("reads", .05)],
    [("one", .38), ("the", .24), ("each", .16), ("a", .11), ("every", .06)],
    [("token", .62), ("word", .17), ("step", .09), ("piece", .06), ("unit", .04)],
]

PROMPT_X, TOK_X, EMB_X = 44, 208, 372
ATT_X, NET_X, LOG_X, OUT_X = 452, 640, 858, 1044
BAND_Y = 150


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
            + "".join("%.3f" % p + "%{" + css + "}" for p, css in stops) + "}")


def _stage(out, x, w, title, sub):
    out.append(_rr(x, BAND_Y - 34, w, 22, 6, _mix(SKY, INK, 0.05)))
    out.append(_txt(x + 9, BAND_Y - 19, title, 9.5, INK, "800", "start", "1.8"))
    out.append(_txt(x, BAND_Y + 306, sub, 8.5, FAINT, "600", "start", "1.2"))


def build(path="assets/inference.svg"):
    css = ["@keyframes fade{0%{opacity:0}}",
           "@keyframes glow{0%,100%{opacity:.18}50%{opacity:1}}",
           ".fd{animation:fade .7s ease-out backwards}"]
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="How a language model answers a question: the prompt is '
           'tokenised, attention weighs earlier tokens, the network scores every candidate '
           'word, one is sampled, and the loop repeats with that word added to the input">'
           % (W, H, W, H),
           "<title>How AI Works</title>",
           '<defs><pattern id="ig" width="26" height="26" patternUnits="userSpaceOnUse">'
           '<circle cx="1.5" cy="1.5" r="1" fill="%s"/></pattern>__STYLE__</defs>' % GRID,
           '<rect width="%d" height="%d" fill="%s"/>' % (W, H, SKY),
           '<rect width="%d" height="%d" fill="url(#ig)"/>' % (W, H)]

    out.append(_txt(48, 46, "HOW AI WORKS", 14, INK, "800", "start", "3.4"))
    out.append(_txt(W - 48, 46, "ONE TOKEN AT A TIME", 12.5, FAINT, "600", "end", "2.2"))
    out.append('<path d="M48,60 H%d" stroke="%s" stroke-width="1.4" fill="none"/>' % (W - 48, RULE))
    out.append(_txt(48, 80, "PROMPT → TOKENS → ATTENTION → NETWORK → SCORES → SAMPLE → BACK "
                            "IN AGAIN", 10.5, MUTED, "600", "start", "1.5"))

    # ── the question ─────────────────────────────────────────────────────
    _stage(out, PROMPT_X, 140, "PROMPT", "what was asked")
    out.append(_rr(PROMPT_X, BAND_Y + 40, 140, 74, 10, CARD,
                   'stroke="%s" stroke-width="1.5"' % RULE))
    out.append('<path d="M%d,%d l0,16 l16,-4 Z" fill="%s"/>'
               % (PROMPT_X + 16, BAND_Y + 114, CARD))
    for i, line in enumerate(("how does a", "model answer?")):
        out.append(_txt(PROMPT_X + 14, BAND_Y + 68 + i * 20, line, 11.5, INK, "600", "start", "0"))
    out.append(ci(PROMPT_X + 122, BAND_Y + 56, 5, TEAMIST, 'class="pulse"'))
    css.append(".pulse{animation:glow 2.2s ease-in-out infinite}")

    # ── context strip: the prompt, growing by one token per step ─────────
    _stage(out, TOK_X, 148, "TOKENS", "context, growing")
    ty = BAND_Y + 6
    for i, t in enumerate(CTX):
        wd = len(t) * 7.4 + 14
        out.append(_rr(TOK_X, ty, wd, 22, 6, _mix(CARD, AEGEAN, 0.16),
                       'stroke="%s" stroke-width="1.3"' % _mix(RULE, AEGEAN, 0.4)))
        out.append(_txt(TOK_X + wd / 2, ty + 15, t, 10, INK, "700", "middle", "0"))
        ty += 28
    # the tokens the model itself adds
    for s in range(STEPS):
        word = CANDIDATES[s][0][0]
        wd = len(word) * 7.4 + 14
        appear = LEAD + s * SPAN + SPAN * 0.86
        css.append(_kf("ctx%d" % s, [(0.0, "opacity:0"), (max(0.0, appear - 0.01), "opacity:0"),
                                     (appear, "opacity:1"), (100.0, "opacity:1")]))
        css.append(".ctx%d{animation:ctx%d " % (s, s) + "%.1f" % DUR + "s linear infinite}")
        out.append('<g class="ctx%d">' % s)
        out.append("  " + _rr(TOK_X, ty, wd, 22, 6, _mix(CARD, TEAMIST, 0.22),
                              'stroke="%s" stroke-width="1.3"' % _mix(RULE, TEAMIST, 0.5)))
        out.append("  " + _txt(TOK_X + wd / 2, ty + 15, word, 10, INK, "700", "middle", "0"))
        out.append("</g>")
        ty += 28

    # ── embedding: each token becomes a column of numbers ────────────────
    _stage(out, EMB_X, 62, "EMBED", "as vectors")
    for i in range(len(CTX) + STEPS):
        for j in range(4):
            shade = 0.12 + ((i * 7 + j * 5) % 9) / 14.0
            out.append(_rr(EMB_X + j * 14, BAND_Y + 6 + i * 28, 11, 22, 3,
                           _mix(CARD, VIOLET, shade)))

    # ── attention: lower-triangular, because it has to be ────────────────
    _stage(out, ATT_X, 168, "ATTENTION", "who looks at whom")
    n = len(CTX) + STEPS
    cell = 16
    for r in range(n):
        row = []
        for c in range(n):
            if c > r:
                continue                    # a token cannot see the future
            w = (1.0 - (r - c) / float(n)) * 0.85 + 0.15
            row.append(_rr(ATT_X + c * cell, BAND_Y + 6 + r * cell, cell - 3, cell - 3, 2,
                           _mix(CARD, CORAL, w * 0.8)))
        if r < len(CTX):
            out.extend(row)
        else:
            # a generated token has no row until it has been sampled
            out.append('<g class="ctx%d">%s</g>' % (r - len(CTX), "".join(row)))
    out.append(_txt(ATT_X, BAND_Y + 6 + n * cell + 16, "CAUSAL MASK · NO TOKEN SEES AHEAD",
                    8, FAINT, "600", "start", "0.8"))

    # ── the network itself ───────────────────────────────────────────────
    # A transformer block, in the order the data actually goes through it:
    # multi-head attention, add and norm, feed-forward, add and norm. The two
    # arcs down the left are the residual connections, which carry the input
    # around each sublayer and are added back on the far side. Without them a
    # stack this deep does not train, so leaving them out would have been the
    # kind of tidy diagram that teaches the wrong thing.
    _stage(out, NET_X, 208, "NETWORK", "weights, learned")
    NW = 200

    def norm_bar(y, label):
        out.append(_rr(NET_X, y, NW, 17, 5, _mix(CARD, BROWN, 0.30),
                       'stroke="%s" stroke-width="1.1"' % _mix(RULE, BROWN, 0.5)))
        out.append(_txt(NET_X + NW / 2, y + 12, label, 8, INK, "800", "middle", "1.4"))

    def residual(y0, y1, tag):
        rx = NET_X - 13
        out.append('<path d="M%d,%d H%d V%d H%d" fill="none" stroke="%s" '
                   'stroke-width="1.6" stroke-linecap="round"/>'
                   % (NET_X + 6, y0, rx, y1, NET_X + 6, _mix(RULE, TEAMIST, 0.6)))
        out.append('<circle cx="%d" cy="%d" r="6.5" fill="%s" stroke="%s" '
                   'stroke-width="1.4"/>' % (NET_X + 6, y1, CARD, _mix(RULE, TEAMIST, 0.7)))
        out.append(_txt(NET_X + 6, y1 + 3.4, "+", 10, _mix(MUTED, TEAMIST, .5), "800", "middle"))
        out.append(_txt(rx - 4, (y0 + y1) / 2, tag, 7.5, FAINT, "700", "end", "0.6"))

    # multi-head attention, drawn as four planes because there are many heads
    head_y = BAND_Y + 8
    for h in range(4):
        out.append(_rr(NET_X + 26 + h * 9, head_y + (3 - h) * 7, 118, 40, 5,
                       _mix(CARD, CORAL, 0.20 + h * 0.10),
                       'stroke="%s" stroke-width="1.1"' % _mix(RULE, CORAL, 0.55)))
    for qkv, dx in (("Q", 8), ("K", 40), ("V", 72)):
        out.append(_rr(NET_X + 57 + dx, head_y + 30, 22, 15, 3, _mix(CARD, CORAL, 0.62)))
        out.append(_txt(NET_X + 68 + dx, head_y + 41, qkv, 8.5, INK, "800", "middle"))
    out.append(_txt(NET_X + NW, head_y - 2, "4 HEADS", 7.5, FAINT, "700", "end", "0.8"))
    residual(BAND_Y + 4, head_y + 60, "SKIP")
    norm_bar(head_y + 68, "ADD & NORM")

    # feed-forward: wide in the middle, back down on the way out
    ff_top = head_y + 96
    layers = [(0, 6, AEGEAN), (74, 9, VIOLET), (148, 6, TEAMIST)]
    cols = []
    for dx, cnt, colr in layers:
        ys = [ff_top + 8 + k * (112.0 / max(1, cnt - 1)) for k in range(cnt)]
        cols.append((NET_X + 26 + dx, ys, colr))
    for li in range(len(cols) - 1):
        x0, ys0, _ = cols[li]
        x1, ys1, _ = cols[li + 1]
        for ai, a in enumerate(ys0):
            for bi, b in enumerate(ys1):
                # a weight is a number, so the lines carry different strengths
                wgt = 0.10 + ((ai * 5 + bi * 3) % 7) / 9.0
                out.append('<path d="M%.1f,%.1f L%.1f,%.1f" stroke="%s" '
                           'stroke-width="%.2f" opacity="%.2f" fill="none"/>'
                           % (x0 + 6, a, x1 - 6, b, _mix(RULE, INK, 0.25),
                              0.5 + wgt * 1.4, 0.20 + wgt * 0.5))
    for li, (x, ys, colr) in enumerate(cols):
        for y in ys:
            out.append('<circle cx="%.1f" cy="%.1f" r="6" fill="%s" stroke="%s" '
                       'stroke-width="1.2"/>' % (x, y, _mix(CARD, colr, 0.72),
                                                 _mix(RULE, colr, 0.6)))
    out.append(_txt(NET_X + 26, ff_top + 136, "FEED FORWARD · 4x WIDE", 7.5,
                    FAINT, "700", "start", "0.6"))
    residual(head_y + 88, ff_top + 148, "SKIP")
    norm_bar(ff_top + 156, "ADD & NORM")
    out.append(_txt(NET_X + NW / 2, ff_top + 190, "× N BLOCKS, STACKED", 8.5,
                    _mix(MUTED, VIOLET, 0.35), "800", "middle", "1.4"))

    # a wave of activation crossing the block, once per generated token
    waves = [(NET_X + 88, head_y + 20, 46)] + [(c[0], sum(c[1]) / len(c[1]), 0) for c in cols]
    for li, (wx, wy, _sp) in enumerate(waves):
        stops = [(0.0, "opacity:0")]
        for st in range(STEPS):
            t0 = LEAD + st * SPAN + SPAN * (0.08 + li * 0.06)
            stops += [(max(0.0, t0 - 0.01), "opacity:0"), (t0, "opacity:1"),
                      (min(100.0, t0 + SPAN * 0.14), "opacity:0")]
        stops.append((100.0, "opacity:0"))
        css.append(_kf("wv%d" % li, stops))
        css.append(".wv%d{animation:wv%d " % (li, li) + "%.1f" % DUR + "s linear infinite}")
        if li == 0:
            out.append('<rect class="wv%d" x="%.1f" y="%.1f" width="118" height="40" rx="5" '
                       'fill="none" stroke="%s" stroke-width="2.4"/>'
                       % (li, NET_X + 53, head_y, TEAMIST))
        else:
            for y in cols[li - 1][1]:
                out.append('<circle class="wv%d" cx="%.1f" cy="%.1f" r="10" fill="none" '
                           'stroke="%s" stroke-width="2.2"/>' % (li, cols[li - 1][0], y, TEAMIST))

    # ── logits: a score for every candidate, then one is sampled ─────────
    _stage(out, LOG_X, 170, "SCORES", "a distribution, not an answer")
    bar_w = 150
    for s in range(STEPS):
        show = LEAD + s * SPAN + SPAN * 0.30
        hide = LEAD + s * SPAN + SPAN * 0.94
        css.append(_kf("lg%d" % s, [(0.0, "opacity:0"), (max(0.0, show - 0.01), "opacity:0"),
                                    (show, "opacity:1"), (hide, "opacity:1"),
                                    (min(100.0, hide + 0.4), "opacity:0"), (100.0, "opacity:0")]))
        css.append(".lg%d{animation:lg%d " % (s, s) + "%.1f" % DUR + "s linear infinite}")
        out.append('<g class="lg%d">' % s)
        for c, (word, prob) in enumerate(CANDIDATES[s]):
            y = BAND_Y + 10 + c * 44
            win = c == 0
            col = TEAMIST if win else _mix(TRACK, AEGEAN, 0.35)
            out.append("  " + _rr(LOG_X, y, bar_w, 16, 8, TRACK))
            out.append("  " + _rr(LOG_X, y, bar_w * prob, 16, 8, col))
            out.append("  " + _txt(LOG_X, y - 5, word, 10, INK if win else MUTED,
                                   "800" if win else "600", "start", "0.3"))
            out.append("  " + _txt(LOG_X + bar_w + 8, y + 13, "%.0f%%" % (prob * 100), 9.5,
                                   INK if win else FAINT, "700", "start", "0"))
            if win:
                out.append("  " + _txt(LOG_X + bar_w, y - 5, "SAMPLED", 8, TEAMIST,
                                       "800", "end", "1.2"))
        out.append("</g>")

    # ── the answer, assembled one token at a time ────────────────────────
    _stage(out, OUT_X, 152, "OUTPUT", "streamed back")
    out.append(_rr(OUT_X, BAND_Y + 6, 152, 120, 10, CARD,
                   'stroke="%s" stroke-width="1.5"' % RULE))
    oy = BAND_Y + 34
    for s in range(STEPS):
        word = CANDIDATES[s][0][0]
        appear = LEAD + s * SPAN + SPAN * 0.86
        css.append(_kf("ot%d" % s, [(0.0, "opacity:0"),
                                    (max(0.0, appear - 0.01), "opacity:0"),
                                    (appear, "opacity:1"), (100.0, "opacity:1")]))
        css.append(".ot%d{animation:ot%d " % (s, s) + "%.1f" % DUR + "s linear infinite}")
        out.append('<g class="ot%d">%s</g>'
                   % (s, _txt(OUT_X + 14, oy + s * 24, word, 13, INK, "700", "start", "0.2")))
    out.append(_txt(OUT_X + 14, BAND_Y + 148, "…and round again", 9.5, FAINT, "600", "start", "0.8"))

    # ── the loop: the sampled token becomes input ────────────────────────
    arc_y = BAND_Y + 340
    d = ("M%d,%d V%d Q%d,%d %d,%d H%d Q%d,%d %d,%d V%d"
         % (OUT_X + 60, BAND_Y + 132, arc_y - 22, OUT_X + 60, arc_y, OUT_X + 36, arc_y,
            TOK_X + 60, TOK_X + 36, arc_y, TOK_X + 36, arc_y - 22, BAND_Y + 300))
    out.append('<path d="%s" fill="none" stroke="%s" stroke-width="2" stroke-linecap="round"/>'
               % (d, _mix(RULE, TEAMIST, 0.55)))
    out.append('<path d="M%d,%d l6,10 l-12,0 Z" fill="%s"/>'
               % (TOK_X + 36, BAND_Y + 298, _mix(RULE, TEAMIST, 0.7)))
    out.append(_txt((TOK_X + OUT_X) / 2 + 40, arc_y - 8,
                    "THE SAMPLED TOKEN IS APPENDED AND THE WHOLE THING RUNS AGAIN",
                    9.5, _mix(MUTED, TEAMIST, 0.4), "700", "middle", "1.2"))
    # a pulse riding the loop each time a token is produced
    stops = [(0.0, "opacity:0")]
    for s in range(STEPS):
        t0 = LEAD + s * SPAN + SPAN * 0.88
        stops += [(max(0.0, t0 - 0.01), "opacity:0"), (t0, "opacity:1"),
                  (min(100.0, t0 + SPAN * 0.10), "opacity:0")]
    stops.append((100.0, "opacity:0"))
    css.append(_kf("fbp", stops))
    css.append(".fbp{animation:fbp " + "%.1f" % DUR + "s linear infinite}")
    out.append('<path class="fbp" d="%s" fill="none" stroke="%s" stroke-width="3" '
               'stroke-linecap="round" stroke-dasharray="10 4000"/>' % (d, TEAMIST))

    out.append('<path d="M48,%d H%d" stroke="%s" stroke-width="1.4" fill="none"/>'
               % (H - 32, W - 48, RULE))
    out.append(_txt(48, H - 12, "HOW LANGUAGE MODELS WORK IN GENERAL · NOT ANY ONE SYSTEM",
                    10, FAINT, "600", "start", "1.5"))
    out.append(_txt(W - 48, H - 12, "GITHUB.COM/AHMADMALIK1376", 10, FAINT, "600", "end", "1.5"))
    out.append("</svg>")

    svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote %s (%d steps, %.0fs loop, %d KB)" % (path, STEPS, DUR, len(svg) // 1024))
    return path


def ci(cx, cy, r, fill, extra=""):
    return ('<circle cx="%.1f" cy="%.1f" r="%s" fill="%s"%s/>'
            % (cx, cy, r, fill, (" " + extra) if extra else ""))


if __name__ == "__main__":
    build()
