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

import worldmap
import arsenal
import metrics
 
# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
USERNAME      = "AHMADMALIK1376"
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
def fetch_contributions() -> tuple:
    """A year of contributions, scraped from the profile calendar endpoint.

    The REST API does not expose contributions at all, and the GraphQL query
    that does needs a user scope the workflow's built-in token has no reason
    to carry. This endpoint is the one that renders the calendar on a profile
    page, it is public, and it needs no token.

    Returns (days, total) where days is [(iso_date, count, level)] oldest
    first. On any failure it returns an empty year rather than raising, so a
    change at GitHub's end cannot take the whole rebuild down with it.
    """
    url = "https://github.com/users/%s/contributions" % USERNAME
    try:
        html = requests.get(url, headers={"User-Agent": "readme-bot"},
                            timeout=20).text
    except Exception as exc:                       # noqa: BLE001
        print("  contributions unavailable: %s" % exc)
        return [], 0

    cells = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*?data-level="(\d)"', html)
    counts = {}
    for cid, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]+)</tool-tip>', html):
        m = re.match(r"(No|[\d,]+) contribution", text)
        if m:
            counts[cid] = 0 if m.group(1) == "No" else int(m.group(1).replace(",", ""))
    ordered = [counts[k] for k in sorted(counts, key=_cell_key)]
    days = [(d, ordered[i] if i < len(ordered) else 0, int(lv))
            for i, (d, lv) in enumerate(cells)]
    days.sort(key=lambda t: t[0])
    return days, sum(c for _, c, _ in days)


def _cell_key(cid: str):
    """Sort calendar cell ids by their week and weekday numbers."""
    nums = [int(x) for x in re.findall(r"\d+", cid)]
    return tuple(nums[-2:]) if len(nums) >= 2 else (0, 0)


def analyse_events(events: list) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    commits_by_repo: dict = {}
    total_commits = pr_count = issue_count = star_count = 0
    push_count = 0
 
    for ev in events:
        ts = datetime.fromisoformat(ev["created_at"].replace("Z", "+00:00"))
        if ts < cutoff:
            continue
        repo_label = ev["repo"]["name"].split("/")[-1]
        etype = ev["type"]
 
        if etype == "PushEvent":
            # The public events feed does not carry commit details on every
            # push, so prefer the counts when they are there and fall back to
            # counting the push itself rather than silently reporting zero.
            payload = ev["payload"]
            n = payload.get("size")
            if n is None:
                n = len(payload.get("commits", [])) or 1
            commits_by_repo[repo_label] = commits_by_repo.get(repo_label, 0) + n
            total_commits += n
            push_count += 1
        elif etype == "PullRequestEvent":
            # This fires for opened, merged and closed alike; count only the
            # opens so a single pull request is not tallied several times.
            if ev["payload"].get("action") == "opened":
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
        "push_count": push_count,
    }
 
 
def main():
    print("\n🤖 AHMAD MALIK — README asset builder")
    print("=" * 52)
 
    if not GITHUB_TOKEN:
        raise EnvironmentError("GITHUB_TOKEN env var is not set!")
 
    # Fetch
    user         = fetch_user()
    events       = fetch_events()
    repos        = fetch_repos()
    lang_bytes   = fetch_language_bytes(repos)

    # Charts, drawn from the data just fetched so they cannot drift out of date
    print("\n[charts] Rendering from live API data...")
    non_fork = [r for r in repos if not r.get("fork")]
    worldmap.language_map(lang_bytes, repo_count=len(non_fork))
    # the arsenal folds in any language the API reports that is not
    # already declared, so the section keeps up on its own
    arsenal.arsenal(lang_bytes=lang_bytes)

    days, contributions = fetch_contributions()
    print("  contributions: %d over %d days" % (contributions, len(days)))

    # Analyse
    print("\n📊 Analysing activity...")
    activity = analyse_events(events)

    # The dial needs the activity counts, so it is drawn here rather than
    # alongside the language map above.
    own = [r for r in repos if not r.get("fork")]
    metrics.year_dial(days, contributions, [
        ("PUBLIC REPOS", len(own), "NOT COUNTING FORKS"),
        ("STARS EARNED", sum(r.get("stargazers_count", 0) for r in own),
         "ACROSS OWN REPOSITORIES"),
        ("FOLLOWERS", user.get("followers", 0), "ON GITHUB"),
        ("PUSHES / 30D", activity.get("push_count", 0), "TO PUBLIC REPOSITORIES"),
        ("PULL REQUESTS", activity["pr_count"], "OPENED IN THE LAST 30 DAYS"),
        ("LANGUAGES", len(lang_bytes), "DETECTED BY LINGUIST"),
    ])
    print("[done] every asset regenerated from live data")


if __name__ == "__main__":
    main()
 
