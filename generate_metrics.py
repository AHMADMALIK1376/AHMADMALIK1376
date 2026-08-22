import os
import requests
import json

USERNAME = "AHMADMALIK1376"
TOKEN = os.environ.get("GH_TOKEN")

def fetch_data():
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    
    # 1. Fetch user profile stats
    user_resp = requests.get(f"https://api.github.com/users/{USERNAME}", headers=headers)
    user_data = user_resp.json() if user_resp.status_code == 200 else {}
    public_repos = user_data.get("public_repos", 0)
    followers = user_data.get("followers", 0)

    # 2. Fetch language distribution
    repos_resp = requests.get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100", headers=headers)
    repos = repos_resp.json() if repos_resp.status_code == 200 else []
    
    lang_bytes = {}
    stars = 0
    for repo in repos:
        if type(repo) is dict and not repo.get("fork"):
            stars += repo.get("stargazers_count", 0)
            lang_url = repo.get("languages_url")
            if lang_url:
                l_resp = requests.get(lang_url, headers=headers)
                if l_resp.status_code == 200:
                    for lang, bytes_count in l_resp.json().items():
                        lang_bytes[lang] = lang_bytes.get(lang, 0) + bytes_count

    # Sort and calculate percentages
    total_bytes = sum(lang_bytes.values()) or 1
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {"repos": public_repos, "stars": stars, "followers": followers}, sorted_langs, total_bytes

def generate_svg():
    stats, langs, total_bytes = fetch_data()
    
    # Theme colors mapping
    color_map = ["#0077C8", "#F88379", "#F2D24B", "#D4A373", "#D41F26"]
    
    # Generate Language Bars
    lang_svg = ""
    y_offset = 65
    for i, (lang, bytes_cnt) in enumerate(langs):
        pct = (bytes_cnt / total_bytes) * 100
        bar_width = max(int((pct / 100) * 200), 5)
        color = color_map[i % len(color_map)]
        
        lang_svg += f'''
        <text x="440" y="{y_offset}" font-family="ui-monospace, monospace" font-size="9" font-weight="700" fill="#5E5349">{lang}</text>
        <text x="650" y="{y_offset}" font-family="ui-monospace, monospace" font-size="9" fill="#8C7A6B" text-anchor="end">{pct:.1f}%</text>
        <rect x="440" y="{y_offset + 5}" width="210" height="6" fill="#E6DBCA" rx="3"/>
        <rect x="440" y="{y_offset + 5}" width="{bar_width}" height="6" fill="{color}" rx="3"/>
        '''
        y_offset += 28

    svg_content = f"""<svg viewBox="0 0 760 220" xmlns="http://www.w3.org/2000/svg" width="760" height="220">
    <defs>
      <style>
        .bg-grid {{ fill: #F2EDE6; }}
        .panel {{ fill: #F2EDE6; stroke: #CDBEA6; stroke-width: 1.5; rx: 8; }}
        .stat-val {{ font-family: ui-monospace, monospace; font-size: 32px; font-weight: 800; fill: #0077C8; }}
        .stat-label {{ font-family: ui-monospace, monospace; font-size: 9px; font-weight: 700; fill: #8C7A6B; letter-spacing: 1px; }}
        .title {{ font-family: ui-monospace, monospace; font-size: 11px; font-weight: 700; fill: #5E5349; letter-spacing: 2px; }}
      </style>
      <pattern id="dg" width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="#E6DBCA"/></pattern>
    </defs>

    <rect width="760" height="220" class="bg-grid"/>
    <rect width="760" height="220" fill="url(#dg)"/>

    <!-- Left Panel: Core Stats -->
    <rect x="40" y="30" width="360" height="160" class="panel"/>
    <text x="220" y="55" text-anchor="middle" class="title">◈ CORE TELEMETRY ◈</text>
    
    <text x="100" y="110" text-anchor="middle" class="stat-val">{stats['repos']}</text>
    <text x="100" y="130" text-anchor="middle" class="stat-label">REPOSITORIES</text>

    <text x="220" y="110" text-anchor="middle" class="stat-val">{stats['stars']}</text>
    <text x="220" y="130" text-anchor="middle" class="stat-label">TOTAL STARS</text>

    <text x="340" y="110" text-anchor="middle" class="stat-val">{stats['followers']}</text>
    <text x="340" y="130" text-anchor="middle" class="stat-label">FOLLOWERS</text>

    <!-- Right Panel: Languages -->
    <rect x="420" y="30" width="250" height="160" class="panel"/>
    <text x="545" y="50" text-anchor="middle" class="title">LANGUAGES</text>
    {lang_svg}
    </svg>
    """
    
    os.makedirs("assets", exist_ok=True)
    with open("assets/system-metrics.svg", "w") as f:
        f.write(svg_content)

if __name__ == "__main__":
    generate_svg()
    print("Metrics SVG generated successfully!")
