"""
██████████████████████████████████████████████████████████████
  AHMAD MALIK — Self-Evolving README Engine
  Runs daily via GitHub Actions. Fetches live GitHub data and
  rewrites dynamic sections of README.md automatically.
██████████████████████████████████████████████████████████████
"""

import os
import re
import json
import requests
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
USERNAME      = "AHMADMALIK1376"
README_PATH   = "README.md"
GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
LOOKBACK_DAYS = 30   # activity window

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

# Friendly display names for your 4 active PIDs.
# Map actual repo names (lowercase) to display labels.
# Edit this dict to pin specific repos to specific PIDs.
PID_OVERRIDES = {
    # "your-repo-name": "AI Detection Engine",
}

# ─────────────────────────────────────────────
#  GITHUB API HELPERS
# ─────────────────────────────────────────────
def gh_get(url: str, params: dict = None) -> list | dict:
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def paginate(url: str, max_pages: int = 5, **params) -> list:
    results = []
    for page in range(1, max_pages + 1):
        data = gh_get(url, {**params, "per_page": 100, "page": page})
        if not data:
            break
        results.extend(data)
        if len(data) < 100:
            break
    return results


# ─────────────────────────────────────────────
#  DATA FETCHING
# ─────────────────────────────────────────────
def fetch_user() -> dict:
    print("  → Fetching user profile...")
    return gh_get(f"https://api.github.com/users/{USERNAME}")


def fetch_events() -> list:
    print("  → Fetching recent events...")
    return paginate(
        f"https://api.github.com/users/{USERNAME}/events/public",
        max_pages=3,
    )


def fetch_repos() -> list:
    print("  → Fetching repositories...")
    return paginate(
        f"https://api.github.com/users/{USERNAME}/repos",
        max_pages=4,
        sort="updated",
    )


def fetch_language_bytes(repos: list) -> dict:
    """Aggregate language bytes across all non-fork repos (cap at 25 to avoid rate-limit)."""
    print("  → Fetching language breakdown...")
    lang_bytes: dict = {}
    checked = 0
    for repo in repos:
        if repo.get("fork"):
            continue
        if checked >= 25:
            break
        try:
            langs = gh_get(repo["languages_url"])
            for lang, nbytes in langs.items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + nbytes
            checked += 1
        except Exception as exc:
            print(f"    ⚠ Skipped {repo['name']}: {exc}")
    return lang_bytes


# ─────────────────────────────────────────────
#  ANALYSIS
# ─────────────────────────────────────────────
def analyse_events(events: list) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    commits_by_repo: dict = {}
    total_commits = pr_count = issue_count = star_count = 0

    for ev in events:
        ts = datetime.fromisoformat(ev["created_at"].replace("Z", "+00:00"))
        if ts < cutoff:
            continue
        repo_label = ev["repo"]["name"].split("/")[-1]
        etype = ev["type"]

        if etype == "PushEvent":
            n = len(ev["payload"].get("commits", []))
            commits_by_repo[repo_label] = commits_by_repo.get(repo_label, 0) + n
            total_commits += n
        elif etype == "PullRequestEvent":
            pr_count += 1
        elif etype in ("IssuesEvent", "IssueCommentEvent"):
            issue_count += 1
        elif etype == "WatchEvent":
            star_count += 1

    # sort repos by commit count descending
    commits_by_repo = dict(
        sorted(commits_by_repo.items(), key=lambda x: x[1], reverse=True)
    )
    return {
        "commits_by_repo": commits_by_repo,
        "total_commits": total_commits,
        "pr_count": pr_count,
        "issue_count": issue_count,
        "star_count": star_count,
    }


def derive_pids(commits_by_repo: dict) -> list[tuple[str, int]]:
    """
    Returns list of (display_name, progress_pct) for the 4 PIDs.
    Progress is relative to the most-active repo (= 100%).
    Falls back to sane defaults if no activity detected.
    """
    defaults = [
        ("AI Detection Engine",      87),
        ("Browser Automation Suite", 100),
        ("VS Code Neural Extension",  65),
        ("Cloud-Native SaaS Platform", 55),
    ]

    if not commits_by_repo:
        return defaults

    top4 = list(commits_by_repo.items())[:4]
    max_commits = max(c for _, c in top4) or 1

    pids = []
    for repo, commits in top4:
        label = PID_OVERRIDES.get(repo.lower(), repo.replace("-", " ").replace("_", " ").title())
        pct   = max(10, min(100, round(commits / max_commits * 100)))
        pids.append((label, pct))

    # pad to exactly 4
    while len(pids) < 4:
        pids.append(defaults[len(pids)])

    return pids


def derive_skills(lang_bytes: dict) -> dict[str, int]:
    """
    Map raw language bytes → skill proficiency for the 12 radar/histogram items.
    Values always clamp to [50, 100] so nothing looks embarrassingly low.
    """
    total = sum(lang_bytes.values()) or 1

    def share(langs):
        return sum(lang_bytes.get(l, 0) for l in langs) / total

    py_s  = share(["Python", "Jupyter Notebook"])
    ts_s  = share(["TypeScript"])
    js_s  = share(["JavaScript", "TypeScript"])
    sh_s  = share(["Shell", "Dockerfile"])

    def scale(base, boost, factor=400):
        return min(100, max(base, round(base + boost * factor)))

    return {
        "Python":     scale(80, py_s),
        "TypeScript": scale(65, ts_s),
        "JavaScript": scale(65, js_s),
        "Node.js":    scale(80, js_s + ts_s),
        "Playwright": scale(85, 0),     # fixed — hard to detect from lang bytes
        "React":      scale(75, js_s + ts_s),
        "FastAPI":    scale(75, py_s),
        "LLM/AI":     scale(85, py_s),
        "Vision AI":  scale(75, py_s),
        "n8n":        scale(70, 0),
        "GCP/AWS":    scale(75, sh_s),
        "Docker":     scale(75, sh_s),
    }


# ─────────────────────────────────────────────
#  CHART URL BUILDERS  (quickchart.io)
# ─────────────────────────────────────────────
def build_pid_chart_url(pids: list[tuple[str, int]]) -> str:
    labels = [f"[PID {i+1:03d}] {name}" for i, (name, _) in enumerate(pids)]
    data   = [pct for _, pct in pids]
    colors = ["00ff88", "00ff88", "ffd700", "ff6b6b"]

    cfg = {
        "type": "horizontalBar",
        "data": {
            "labels": labels,
            "datasets": [{"label": "Progress %", "data": data,
                          "backgroundColor": colors}],
        },
        "options": {
            "scales": {
                "xAxes": [{"ticks": {"min": 0, "max": 100, "fontColor": "#aaa"},
                           "gridLines": {"color": "rgba(255,255,255,0.05)"}}],
                "yAxes": [{"ticks": {"fontColor": "#ffffff", "fontSize": 11},
                           "gridLines": {"display": False}}],
            },
            "plugins": {"legend": {"display": False}},
            "layout": {"padding": 10},
        },
        "backgroundColor": "0d1117",
    }

    encoded = quote(json.dumps(cfg, separators=(",", ":")))
    return f"https://quickchart.io/chart?c={encoded}&w=500&h=220&bkg=0d1117&f=monospace"


def build_radar_chart_url(skills: dict[str, int]) -> str:
    labels = list(skills.keys())
    data   = list(skills.values())

    cfg = {
        "type": "radar",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": "Skill Level",
                "data":  data,
                "backgroundColor": "rgba(0,255,136,0.15)",
                "borderColor": "00ff88",
                "borderWidth": 2,
                "pointBackgroundColor": "00ff88",
                "pointRadius": 4,
            }],
        },
        "options": {
            "scale": {
                "ticks": {"min": 0, "max": 100, "stepSize": 25,
                          "fontColor": "#555", "backdropColor": "transparent"},
                "gridLines":   {"color": "rgba(0,255,136,0.1)"},
                "angleLines":  {"color": "rgba(0,255,136,0.15)"},
                "pointLabels": {"fontColor": "#00ff88", "fontSize": 12},
            },
            "plugins": {"legend": {"display": False}},
        },
        "backgroundColor": "0d1117",
    }

    encoded = quote(json.dumps(cfg, separators=(",", ":")))
    return f"https://quickchart.io/chart?c={encoded}&w=600&h=420&bkg=0d1117"


# ─────────────────────────────────────────────
#  DYNAMIC STATS BLOCK (injected into README)
# ─────────────────────────────────────────────
def build_stats_block(activity: dict, user: dict, lang_bytes: dict,
                      pids: list[tuple[str, int]]) -> str:
    now       = datetime.now(timezone.utc)
    total     = sum(lang_bytes.values()) or 1
    top_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:4]
    lang_str  = " &nbsp;·&nbsp; ".join(
        f"`{l}` **{round(b/total*100)}%**" for l, b in top_langs
    ) or "`Python` **50%** &nbsp;·&nbsp; `TypeScript` **30%**"

    # Compute a simple "health score" out of 100 based on recent activity
    score = min(100, activity["total_commits"] * 3
                      + activity["pr_count"] * 5
                      + activity["issue_count"] * 2)
    score_bar = "█" * (score // 10) + "░" * (10 - score // 10)

    most_active = list(activity["commits_by_repo"].keys())[:1]
    hot_repo = most_active[0] if most_active else "—"

    pid_rows = "\n".join(
        f"| 🔵 **PID {i+1:03d}** `{name}` | {pct}% |"
        for i, (name, pct) in enumerate(pids)
    )

    return f"""<!-- DYNAMIC_STATS:START — auto-generated, do not edit manually -->
<div align="center">

## ◈ LIVE SYSTEM TELEMETRY ◈

<sub>🤖 Auto-synced every 24 h via GitHub Actions · Last sync: **{now.strftime('%b %d, %Y — %H:%M UTC')}**</sub>

<br/>

<table>
<tr>
<td>

| Metric | Value |
|:--|:--|
| 🔥 **30-Day Commits** | **{activity["total_commits"]}** |
| 🔀 **Pull Requests** | **{activity["pr_count"]}** |
| 🐛 **Issues / Comments** | **{activity["issue_count"]}** |
| ⭐ **Stars Received** | **{activity["star_count"]}** |
| 📦 **Public Repos** | **{user.get("public_repos", "—")}** |
| 👥 **Followers** | **{user.get("followers", "—")}** |
| 🔥 **Hottest Repo** | `{hot_repo}` |
| 💻 **Top Stack** | {lang_str} |

</td>
<td>

| Activity Score |  |
|:--|:--|
| **{score}/100** | `{score_bar}` |

**Active Processes**

{pid_rows}

</td>
</tr>
</table>

</div>
<!-- DYNAMIC_STATS:END -->"""


# ─────────────────────────────────────────────
#  README PATCHER
# ─────────────────────────────────────────────
def patch_readme(pid_url: str, radar_url: str, stats_block: str) -> None:
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # ── 1. Swap the horizontal-bar PID chart URL ──────────────────
    # Match the full quickchart URL used in the PID block
    pid_pattern = (
        r"(https://quickchart\.io/chart\?c=)"           # base
        r"[^\"'\s]+"                                     # encoded config
        r"(&w=500&h=220[^\"'\s]*)"                       # size params
    )
    if re.search(pid_pattern, content):
        content = re.sub(pid_pattern, pid_url, content, count=1)
        print("  ✓ PID chart URL updated")
    else:
        print("  ⚠ PID chart URL pattern not found — skipping")

    # ── 2. Swap the radar chart URL ───────────────────────────────
    radar_pattern = (
        r"(https://quickchart\.io/chart\?c=)"
        r"[^\"'\s]+"
        r"(&w=600&h=420[^\"'\s]*)"
    )
    if re.search(radar_pattern, content):
        content = re.sub(radar_pattern, radar_url, content, count=1)
        print("  ✓ Radar chart URL updated")
    else:
        print("  ⚠ Radar chart URL pattern not found — skipping")

    # ── 3. Inject / replace the dynamic stats block ───────────────
    dynamic_pattern = r"<!-- DYNAMIC_STATS:START.*?<!-- DYNAMIC_STATS:END -->"
    if re.search(dynamic_pattern, content, re.DOTALL):
        content = re.sub(dynamic_pattern, stats_block, content, flags=re.DOTALL)
        print("  ✓ Dynamic stats block replaced")
    else:
        # First run — append just before the OPEN CHANNEL section
        anchor = "<!-- ══════════════════════════════════════════════════════════ -->\n<!--                     OPEN CHANNEL"
        if anchor in content:
            content = content.replace(
                anchor,
                stats_block + "\n\n<br/>\n\n---\n\n<br/>\n\n" + anchor,
            )
            print("  ✓ Dynamic stats block injected (first run)")
        else:
            # Fallback: append at end before footer
            content = content.rstrip() + "\n\n" + stats_block + "\n"
            print("  ✓ Dynamic stats block appended (fallback)")

    if content == original:
        print("  ℹ README unchanged — nothing to commit")
    else:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print("  ✓ README.md written successfully")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def main():
    print("\n🤖 AHMAD MALIK — README Auto-Evolution Engine")
    print("=" * 52)

    if not GITHUB_TOKEN:
        raise EnvironmentError("GITHUB_TOKEN env var is not set!")

    # Fetch
    user         = fetch_user()
    events       = fetch_events()
    repos        = fetch_repos()
    lang_bytes   = fetch_language_bytes(repos)

    # Analyse
    print("\n📊 Analysing activity...")
    activity = analyse_events(events)
    pids     = derive_pids(activity["commits_by_repo"])
    skills   = derive_skills(lang_bytes)

    print(f"  Commits (30d): {activity['total_commits']}")
    print(f"  PRs: {activity['pr_count']}  |  Issues: {activity['issue_count']}")
    print(f"  Active repos: {list(activity['commits_by_repo'].keys())[:4]}")

    # Build chart URLs
    print("\n🔗 Building chart URLs...")
    pid_url   = build_pid_chart_url(pids)
    radar_url = build_radar_chart_url(skills)

    # Build stats block
    stats_block = build_stats_block(activity, user, lang_bytes, pids)

    # Patch README
    print("\n📝 Patching README.md...")
    patch_readme(pid_url, radar_url, stats_block)

    print("\n✅ All done!\n")
    for name, pct in pids:
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        print(f"  {name:<35} [{bar}] {pct}%")


if __name__ == "__main__":
    main()
