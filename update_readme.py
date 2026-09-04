"""
██████████████████████████████████████████████████████████████
  AHMAD MALIK — Self-Evolving README Engine
  Runs daily via GitHub Actions. Fetches live GitHub data and
  rewrites dynamic sections of README.md automatically.
██████████████████████████████████████████████████████████████
"""
 
import os
import re
import functools
import requests
import datetime

import worldmap
import arsenal
import constellation as skychart
 
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
@functools.lru_cache(maxsize=1)
def fetch_user() -> dict:
    """Cached: main() and the all-time contribution walk both want this,
    and one profile lookup per run is enough."""
    print("  → Fetching user profile...")
    return gh_get(f"https://api.github.com/users/{USERNAME}")
 
 
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
def _parse_calendar(html: str) -> list:
    """Days out of one rendered contributions calendar."""
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
    return days


def fetch_contributions_all() -> tuple:
    """Every day since the account opened, not just the rolling year.

    The calendar endpoint answers one year at a time, so this walks from the
    year the account was created to the current one and stitches the days
    together. Days before the account existed and any the endpoint pads the
    last week with are dropped, so the span starts and ends on real dates.
    """
    try:
        created = fetch_user().get("created_at", "")[:10]
    except Exception:                              # noqa: BLE001
        created = ""
    today = datetime.date.today().isoformat()
    first_year = int(created[:4]) if created else datetime.date.today().year
    out = []
    for yr in range(first_year, datetime.date.today().year + 1):
        url = ("https://github.com/users/%s/contributions?from=%d-01-01&to=%d-12-31"
               % (USERNAME, yr, yr))
        try:
            html = requests.get(url, headers={"User-Agent": "readme-bot"},
                                timeout=25).text
        except Exception as exc:                   # noqa: BLE001
            print("  %d unavailable: %s" % (yr, exc))
            continue
        out += _parse_calendar(html)
    out = [d for d in sorted(set(out)) if (not created or d[0] >= created)
           and d[0] <= today]
    return out, sum(c for _d, c, _l in out)


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


def main():
    print("\n🤖 AHMAD MALIK — README asset builder")
    print("=" * 52)
 
    if not GITHUB_TOKEN:
        raise EnvironmentError("GITHUB_TOKEN env var is not set!")
 
    # Fetch
    repos        = fetch_repos()
    lang_bytes   = fetch_language_bytes(repos)

    # Charts, drawn from the data just fetched so they cannot drift out of date
    print("\n[charts] Rendering from live API data...")
    non_fork = [r for r in repos if not r.get("fork")]
    worldmap.language_map(lang_bytes, repo_count=len(non_fork))
    # the arsenal folds in any language the API reports that is not
    # already declared, so the section keeps up on its own
    arsenal.arsenal(lang_bytes=lang_bytes)

    # the whole history, so the recorder strip covers every day rather than a
    # window on the end of it; the dial still takes the last 365 off the tail
    days, contributions = fetch_contributions_all()
    if not days:                                   # every year failed to load
        days, contributions = fetch_contributions()
    print("  contributions: %d over %d days (%s .. %s)"
          % (contributions, len(days), days[0][0] if days else "?",
             days[-1][0] if days else "?"))
    skychart.build(days, "assets/constellation.svg")

    print("[done] every asset regenerated from live data")


if __name__ == "__main__":
    main()
 
