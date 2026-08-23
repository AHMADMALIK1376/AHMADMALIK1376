# -*- coding: utf-8 -*-
"""
Static art for the README: section headings and the primary-stack strip.

Run by hand when the wording changes; not part of the daily workflow, because
none of it is data-driven.

GitHub strips style attributes and <style> blocks from rendered markdown, so a
markdown heading cannot be coloured. Headings are therefore drawn as images,
which also lets each one carry its own caption instead of needing a separate
<sub> line underneath.
"""
import os

import logos


AEGEAN, CORAL = "#0077C8", "#F88379"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
SKY = "#F2EDE6"
INK = "#2E2A24"
MUTED = "#7D7266"
FAINT = "#A2988A"
RULE = "#D9D0C1"
CARD = "#FBF7F0"
CREAM = "#FAF5EC"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

W = 1240
HEAD_H = 82

# slug, title, caption, accent
HEADINGS = [
    ("system-design", "SYSTEM DESIGN",
     "CLIENT → LOAD BALANCER → WEB TIER → FANOUT → QUEUE → WORKERS", AEGEAN),
    ("llm-training", "HOW AI ANSWERS",
     "PROMPT → TOKENS → ATTENTION → NEXT TOKEN → REPEAT", CORAL),
    ("language-distribution", "LANGUAGE DISTRIBUTION",
     "TERRITORY SIZED BY SHARE · LIVE FROM THE GITHUB API", TEAMIST),
    ("commit-activity", "COMMIT ACTIVITY",
     "LAST 30 DAYS · ALL PUBLIC REPOSITORIES", CRIMSON),
    ("tech-arsenal", "TECH ARSENAL",
     "LANGUAGES · FRAMEWORKS · INFRASTRUCTURE", BROWN),
    ("system-metrics", "SYSTEM METRICS",
     "LIVE TELEMETRY", AEGEAN),
    ("build-deploy", "BUILD &amp; DEPLOY PIPELINE",
     "SOURCE → BUILD → SHIP", TEAMIST),
    ("open-channel", "OPEN CHANNEL",
     "GET IN TOUCH", CORAL),
]

STACK = [
    ("LANGUAGES", ["JavaScript", "TypeScript", "Python", "SQL"], AEGEAN),
    ("FRAMEWORKS", ["React", "Node.js", "Express", "FastAPI"], TEAMIST),
    ("AI / LLM", ["Claude API", "Prompt Eng", "Vision"], CORAL),
    ("INFRA", ["Docker", "GCP", "AWS", "MongoDB"], BROWN),
]


def _rr(x, y, w, h, r, fill, extra=""):
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"%s/>'
            % (x, y, w, h, r, fill, (" " + extra) if extra else ""))


def _txt(x, y, s, size, fill, weight="700", anchor="start", ls="0"):
    return ('<text x="%s" y="%s" font-family="%s" font-size="%s" font-weight="%s" fill="%s" '
            'text-anchor="%s" letter-spacing="%s">%s</text>'
            % (x, y, MONO, size, weight, fill, anchor, ls, s))


def heading(slug, title, caption, accent, outdir="assets"):
    """A slim banner: accent block, title, caption, hairline."""
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="%s">' % (W, HEAD_H, W, HEAD_H, title.replace("&amp;", "and")),
           "<title>%s</title>" % title,
           "<style>.p{transform-origin:0 0;animation:sweep 1s cubic-bezier(.22,1,.36,1) both}"
           "@keyframes sweep{0%{transform:scaleX(0)}}"
           ".f{animation:fin .7s ease-out both;animation-delay:.25s}"
           "@keyframes fin{0%{opacity:0;transform:translateX(-8px)}}</style>",
           _rr(0, 0, W, HEAD_H, 0, SKY)]
    # accent block with three stepped bars, so it reads as a mark not a rule
    out.append('<g class="f">')
    for k, wdt in enumerate((26, 16, 9)):
        out.append("  " + _rr(48, 22 + k * 13, wdt, 8, 4, accent))
    out.append("</g>")
    out.append('<g class="f">' + _txt(92, 46, title, 21, INK, "800", "start", "3.6") + "</g>")
    out.append('<g class="f">' + _txt(92, 66, caption, 10.5, MUTED, "600", "start", "2") + "</g>")
    out.append('<g transform="translate(48,%d)"><rect class="p" width="%d" height="2" '
               'fill="%s"/></g>' % (HEAD_H - 8, W - 96, RULE))
    out.append('<g transform="translate(48,%d)"><rect class="p" width="150" height="2" '
               'fill="%s"/></g>' % (HEAD_H - 8, accent))
    out.append("</svg>")
    path = os.path.join(outdir, "h-%s.svg" % slug)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    return path


def stack_strip(outdir="assets"):
    """Replaces the S/A/B rank badges, which invented a ranking and listed
    languages that appear in none of the repositories."""
    col_w = (W - 96) / float(len(STACK))
    h = 200
    css = ["@keyframes rise{0%{opacity:0;transform:translateY(10px)}}"]
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="Primary stack by category">' % (W, h, W, h),
           "<title>Primary Stack</title>", "<defs>__STYLE__</defs>",
           _rr(0, 0, W, h, 0, SKY),
           _txt(48, 40, "PRIMARY STACK", 12, INK, "800", "start", "3.2"),
           _txt(W - 48, 40, "WHAT I ACTUALLY BUILD WITH", 10, FAINT, "600", "end", "2")]
    out.append('<path d="M48,54 H%d" stroke="%s" stroke-width="1.4" fill="none"/>' % (W - 48, RULE))
    n = 0
    for ci_, (cat, items, colr) in enumerate(STACK):
        x = 48 + ci_ * col_w
        css.append(".c%d{animation:rise .6s ease-out both;animation-delay:%.2fs}"
                   % (ci_, ci_ * 0.1))
        out.append('<g class="c%d">' % ci_)
        out.append("  " + _rr(x, 74, 26, 6, 3, colr))
        out.append("  " + _txt(x, 102, cat, 11, INK, "800", "start", "2.4"))
        # wrap onto a second row rather than silently dropping the overflow
        px, py = x, 118
        for item in items:
            cw = len(item) * 7.0 + 20
            if px + cw > x + col_w - 12:
                px, py = x, py + 32
            out.append("  " + _rr(px, py, cw, 26, 13, CARD,
                                  'stroke="%s" stroke-width="1.6"' % colr))
            out.append("  " + _txt(px + cw / 2, py + 17, item, 10.5, INK, "600", "middle", "0.3"))
            px += cw + 7
            n += 1
        out.append("</g>")
    out.append("</svg>")
    svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
    path = os.path.join(outdir, "primary-stack.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote %s (%d chips)" % (path, n))
    return path


# ── contact buttons ──────────────────────────────────────────────────────
# Drawn here rather than pulled from img.shields.io. They are the last two
# third-party images the README had, and a contact link that renders as a broken
# box because someone else's host is down is worse than useless.
#
# LinkedIn has no mark here on purpose: Simple Icons dropped it at the owner's
# request, as it did AWS and Oracle, so the button carries the name in type
# rather than an approximation of the logo.
CONTACTS = [
    ("email", "gmail", "#0A5FA0", "#0077C8", "ahmadmalik1376@gmail.com", "EMAIL"),
    ("linkedin", None, "#084E96", "#0A66C2", "/in/ahmadmalik1376", "LINKEDIN"),
]


def contact_button(slug, icon, cap_col, body_col, label, kicker, outdir="assets"):
    w, h, cap = 452, 62, 66
    ink = "#FBF7F0"
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="%s: %s">' % (w, h, w, h, kicker, label),
           "<title>%s</title>" % kicker,
           '<rect width="%d" height="%d" rx="13" fill="%s"/>' % (w, h, body_col),
           '<path d="M13,0 H%d V%d H13 A13,13 0 0 1 0,%d V13 A13,13 0 0 1 13,0 Z" fill="%s"/>'
           % (cap, h, h - 13, cap_col)]
    d = logos.ICONS.get(icon) if icon else None
    if d:
        s_ = 24.0 / 24.0
        out.append('<g transform="translate(%.1f,%.1f) scale(%.3f)"><path d="%s" fill="%s"/></g>'
                   % (cap / 2.0 - 12, h / 2.0 - 12, s_, d, ink))
    else:
        # a generic profile card, not anyone's logo
        out.append('<rect x="%.1f" y="%.1f" width="26" height="20" rx="4" fill="none" '
                   'stroke="%s" stroke-width="2.2"/>' % (cap / 2.0 - 13, h / 2.0 - 10, ink))
        out.append('<circle cx="%.1f" cy="%.1f" r="3.4" fill="%s"/>'
                   % (cap / 2.0 - 5, h / 2.0 - 2, ink))
        out.append('<path d="M%.1f,%.1f h9" stroke="%s" stroke-width="2.2" '
                   'stroke-linecap="round"/>' % (cap / 2.0 + 2, h / 2.0 - 4, ink))
        out.append('<path d="M%.1f,%.1f h9" stroke="%s" stroke-width="2.2" '
                   'stroke-linecap="round"/>' % (cap / 2.0 + 2, h / 2.0 + 2, ink))
    out.append(_txt(cap + 22, 26, kicker, 9, "#CFE4F5", "800", "start", "2.6"))
    out.append(_txt(cap + 22, 45, label, 15, ink, "700", "start", "0.4"))
    out.append("</svg>")
    path = os.path.join(outdir, "link-%s.svg" % slug)
    with open(path, "w", encoding="utf-8") as f:
        f.write(chr(10).join(out))
    print("  wrote %s" % path)
    return path


if __name__ == "__main__":
    for slug, title, caption, accent in HEADINGS:
        print("  wrote %s" % heading(slug, title, caption, accent))
    stack_strip()
    for c in CONTACTS:
        contact_button(*c)
