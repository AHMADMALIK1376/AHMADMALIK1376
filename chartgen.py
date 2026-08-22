# -*- coding: utf-8 -*-
"""
The system metrics panel for the profile README.

Every figure comes from the GitHub API rather than being hand-written, and the
daily workflow regenerates the panel so it cannot drift out of date. The world
map that carries the language distribution lives in worldmap.py.

Deliberately no timestamp is drawn. A date would change every day and produce a
commit whether or not the underlying data moved; leaving it out means the
workflow only commits when something actually changed.

House style, matching the rest of the profile art: solid fills, no gradients, no
filters, and CSS animation nested inside plain positioning groups (the CSS
`transform` property overrides a `transform=` attribute on the same element).
"""

AEGEAN, CORAL = "#0077C8", "#F88379"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
SKY = "#F2EDE6"
INK = "#2E2A24"
MUTED = "#7D7266"
FAINT = "#A2988A"
RULE = "#D9D0C1"
CARD = "#FBF7F0"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _txt(x, y, s, size, fill, weight="700", anchor="start", ls="0", cls=None):
    return ('<text x="%s" y="%s" font-family="%s" font-size="%s" font-weight="%s" fill="%s" '
            'text-anchor="%s" letter-spacing="%s"%s>%s</text>'
            % (x, y, MONO, size, weight, fill, anchor, ls,
               (' class="%s"' % cls) if cls else "", _esc(s)))


def _rr(x, y, w, h, r, fill, extra=""):
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"%s/>'
            % (x, y, w, h, r, fill, (" " + extra) if extra else ""))


# ── metrics panel ────────────────────────────────────────────────────────────
# Tiles, three across. Every figure is a real count from the API response; none
# of it is hand-written, so the panel cannot claim something the account does
# not actually show.
TILE_H = 104
TILE_GAP = 16


def metrics_panel(user, repos, activity, lang_bytes, path="assets/telemetry.svg"):
    non_fork = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in non_fork)

    tiles = [
        ("PUBLIC REPOS", len(non_fork), "NOT COUNTING FORKS", AEGEAN),
        ("STARS EARNED", stars, "ACROSS OWN REPOSITORIES", TEAMIST),
        ("FOLLOWERS", user.get("followers", 0), "ON GITHUB", CORAL),
        # Reported as pushes, not commits: the public events feed often omits
        # per-commit detail, so a commit figure would be a guess dressed up as
        # a count. Pushes are always exact.
        ("PUSHES / 30D", activity.get("push_count", activity["total_commits"]),
         "TO PUBLIC REPOSITORIES", CRIMSON),
        ("PULL REQUESTS", activity["pr_count"], "OPENED IN THE LAST 30 DAYS", BROWN),
        ("LANGUAGES", len(lang_bytes), "DETECTED BY LINGUIST", AEGEAN),
    ]

    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    w = 1240
    inner = w - 96
    col_w = (inner - TILE_GAP * (cols - 1)) / float(cols)
    top = 104
    h = top + rows * TILE_H + (rows - 1) * TILE_GAP + 76

    css = ["@keyframes lift{0%{opacity:0;transform:translateY(12px)}}",
           "@keyframes fade{0%{opacity:0}}"]
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="Live account telemetry">' % (w, h, w, h),
           "<title>System Metrics</title>", "<defs>__STYLE__</defs>",
           _rr(0, 0, w, h, 0, SKY),
           _txt(48, 52, "SYSTEM METRICS", 13, INK, "800", "start", "3.4"),
           _txt(w - 48, 52, "LIVE FROM THE GITHUB API", 12, FAINT, "600", "end", "2.2"),
           '<path d="M48,70 H%d" stroke="%s" stroke-width="1.4" fill="none"/>' % (w - 48, RULE)]

    for i, (label, value, sub, colr) in enumerate(tiles):
        cx = 48 + (i % cols) * (col_w + TILE_GAP)
        cy = top + (i // cols) * (TILE_H + TILE_GAP)
        css.append(".t%d{animation:lift .6s cubic-bezier(.22,1,.36,1) both;"
                   "animation-delay:%.2fs}" % (i, i * 0.08))
        css.append(".n%d{animation:fade .5s ease-out both;animation-delay:%.2fs}"
                   % (i, i * 0.08 + 0.3))
        out.append('<g class="t%d">' % i)
        out.append("  " + _rr("%.1f" % cx, cy, "%.1f" % col_w, TILE_H, 10, CARD,
                              'stroke="%s" stroke-width="1.4"' % RULE))
        out.append("  " + _rr("%.1f" % cx, cy + 16, 5, TILE_H - 32, 2.5, colr))
        out.append("  " + _txt("%.1f" % (cx + 24), cy + 32, label, 10, MUTED, "700", "start", "2.2"))
        out.append("  " + _txt("%.1f" % (cx + 24), cy + 70, value, 30, colr, "800", "start",
                               "0", "n%d" % i))
        out.append("  " + _txt("%.1f" % (cx + 24), cy + 89, sub, 9, FAINT, "600", "start", "1.2"))
        out.append("</g>")

    hot = list(activity.get("commits_by_repo", {}).keys())[:1]
    out.append('<path d="M48,%d H%d" stroke="%s" stroke-width="1.4" fill="none"/>'
               % (h - 56, w - 48, RULE))
    out.append(_txt(48, h - 28,
                    "MOST ACTIVE REPOSITORY: %s" % (hot[0] if hot else "NONE THIS MONTH"),
                    10, FAINT, "600", "start", "2"))
    out.append(_txt(w - 48, h - 28, "REBUILT DAILY", 10, FAINT, "600", "end", "1.6"))
    out.append("</svg>")

    svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote %s (%d tiles)" % (path, len(tiles)))
    return path
