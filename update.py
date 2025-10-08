import feedparser
import re
from datetime import datetime, timezone, timedelta
from time import mktime
from random import randint

# NEW: stdlib for API call (no YAML changes needed)
import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode

# FEED SOURCES
feeds = {
    # 📰 Top 3 Media
    "SpaceNews": "https://spacenews.com/feed/",
    "Breaking Defense": "https://breakingdefense.com/feed/",
    "Air & Space Forces": "https://www.airandspaceforces.com/feed/",

    # 🛰️ Government & Military
    "USSF – Headlines": "https://www.spaceforce.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1060&Category=23812&isdashboardselected=0&max=20",
    "USSF – Field News": "https://www.spaceforce.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1060&Category=23813&isdashboardselected=0&max=20",
    "USSF – Units":     "https://www.spaceforce.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1060&Category=23814&isdashboardselected=0&max=20",
    "NASA News Releases": "https://www.nasa.gov/news-release/feed/",
    "NASA Breaking News": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "DARPA News": "https://www.darpa.mil/rss",
    "NOAA Space Weather": "https://www.swpc.noaa.gov/news/rss.xml",

    # 🔬 Scientific & Commercial
    "Phys.org - Space": "https://phys.org/rss-feed/space-news/",
    "Space.com": "https://www.space.com/feeds/all",
    "Ars Technica – Space": "https://feeds.arstechnica.com/arstechnica/space",
    "NASA Tech Briefs": "https://www.techbriefs.com/rss-feeds",

    # 📰 Other Media
    "Defense News - Space": "https://www.defensenews.com/arc/outboundfeeds/rss/category/space/?outputType=xml"
}

# HOMEPAGE LINKS FOR SOURCES
source_links = {
    # 📰 Top 3 Media
    "SpaceNews": "https://spacenews.com",
    "Breaking Defense": "https://breakingdefense.com",
    "Air & Space Forces": "https://www.airandspaceforces.com",

    # 🛰️ Government & Military
    "USSF – Headlines": "https://www.spaceforce.mil/News",
    "USSF – Field News": "https://www.spaceforce.mil/News/Field-News",
    "USSF – Units": "https://www.spaceforce.mil/News/Space-Force-Units",
    "NASA News Releases": "https://www.nasa.gov/news-release/",
    "NASA Breaking News": "https://www.nasa.gov/news/releases/latest/index.html",
    "DARPA News": "https://www.darpa.mil/news",
    "NOAA Space Weather": "https://www.swpc.noaa.gov/news",

    # 🔬 Scientific & Commercial
    "Phys.org - Space": "https://phys.org/space-news/",
    "Space.com": "https://www.space.com/news",
    "Ars Technica – Space": "https://arstechnica.com/science/space/",
    "NASA Tech Briefs": "https://www.techbriefs.com/component/content/category/34-ntb/news/space",

    # 📰 Other Media
    "Defense News - Space": "https://www.defensenews.com/space/"
}

# ---------- TEMPLATED IMAGE SELECTION (NO SCRAPING) ----------
IMAGE_DIR = "images/"
IMAGE_MAP = {
    "default": IMAGE_DIR + "HeadlineLogo.png",
    "breaking": IMAGE_DIR + "breaking.png",
    "government": IMAGE_DIR + "government.png",
    "launch": IMAGE_DIR + "launch.png",
    "satellite": IMAGE_DIR + "satellite.png",
    "science": IMAGE_DIR + "science.png",
}

# keyword sets (case-insensitive). order = priority
PATTERNS = {
    "breaking": re.compile(r"\b(breaking|urgent|alert)\b", re.I),
    "government": re.compile(
        r"\b(ussf|space\s*force|air\s*force|secretary\s+of|dod|department\s+of\s+defense|government|military|guardian[s]?)\b",
        re.I,
    ),
    "launch": re.compile(r"\b(launch|launched|rocket|spacex|blue\s*origin|booster|falcon|starship)\b", re.I),
    "satellite": re.compile(r"\b(satellite|payload|constellation|satcom|earth\s*observation)\b", re.I),
    "science": re.compile(r"\b(science|scientist|discovered|discovery|nasa|research|telescope|observatory)\b", re.I),
}

# source “hints” if the title is ambiguous
SOURCE_HINTS = {
    "government": re.compile(r"(USSF|Space Force|Air & Space Forces|Defense News|Breaking Defense|DARPA)", re.I),
    "science": re.compile(r"(NASA|Phys\.org|Tech Briefs|Ars Technica)", re.I),
}

def pick_image_for(title: str, source: str) -> str:
    t = title or ""
    s = source or ""
    # 1) keyword priority
    for key in ["breaking", "government", "launch", "satellite", "science"]:
        if PATTERNS[key].search(t):
            return IMAGE_MAP[key]
    # 2) source hints
    for key in ["government", "science"]:
        if SOURCE_HINTS[key].search(source):
            return IMAGE_MAP[key]
    # 3) default
    return IMAGE_MAP["default"]
# -------------------------------------------------------------

# NEW: Upcoming Launches fetcher (Launch Library 2 – The Space Devs)
def fetch_upcoming_launches(limit=8, days_ahead=7):
    base = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/"
    params = {
        "limit": limit,
        "hide_recent_previous": "true",
        "ordering": "window_start",
    }
    url = base + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "SpaceHeadlinesBot/1.0"})
    with urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days_ahead)

    launches = []
    for L in data.get("results", []):
        start = L.get("window_start")
        dt = None
        if start:
            try:
                dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            except Exception:
                dt = None
        if not dt or dt > cutoff:
            continue

        name = L.get("name") or "TBD"
        when = dt.strftime("%b %d, %Y %H:%M UTC") if dt else "TBD"
        provider = (L.get("launch_service_provider") or {}).get("name") or "—"
        pad = ((L.get("pad") or {}).get("name") or "—")
        loc = ((L.get("pad") or {}).get("location") or {}).get("name") or ""

        launches.append({
            "name": name,
            "when": when,
            "provider": provider,
            "pad": pad,
            "loc": loc
        })

    return launches[:limit]

# CONVERT TIMESTAMP TO "Xh ago" or "Xm ago"
def get_age_string(timestamp):
    now = datetime.now(timezone.utc)
    delta = now - timestamp
    minutes = int(delta.total_seconds() / 60)
    if minutes < 1:
        return "just now"
    elif minutes < 60:
        return f"about {minutes}m ago"
    elif minutes < 1440:
        hours = minutes // 60
        return f"about {hours}h ago"
    else:
        days = minutes // 1440
        return f"about {days}d ago"

# ⏱️ Allow articles from the past 48 hours
cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
all_items = []

# PARSE EACH FEED
for source, url in feeds.items():
    parsed = feedparser.parse(url)
    for entry in parsed.entries:
        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        if not pub:
            continue
        timestamp = datetime.fromtimestamp(mktime(pub), tz=timezone.utc)
        if timestamp < cutoff:
            continue

        all_items.append({
            "source": source,
            "title": entry.title,
            "link": entry.link,
            "timestamp": timestamp,
            # 👇 image chosen purely from keywords/source (no scraping)
            "image": pick_image_for(entry.title, source),
            "age": get_age_string(timestamp)
        })

# SORT + SELECT
latest = sorted(all_items, key=lambda x: x["timestamp"], reverse=True)
top_story = latest[0] if latest else None
remaining = latest[1:] if len(latest) > 1 else []

# ORGANIZE BY SOURCE
sources = {}
for item in remaining:
    sources.setdefault(item["source"], []).append(item)

# 🔁 Top image (already selected by picker)
fallback_image = IMAGE_MAP["default"]
image_url = top_story["image"] if (top_story and top_story["image"]) else fallback_image

# ⏱️ Recent class = < 2 hours
is_recent = (datetime.now(timezone.utc) - top_story["timestamp"]).total_seconds() < 7200 if top_story else False
top_class = "recent" if is_recent else ""

# 📌 Top Story Block
top_html = ""
if top_story:
    top_html = f'''
<div class="top-story {top_class}" style="text-align: center;">
  <a href="{top_story["link"]}" target="_blank" style="display: inline-block;">
    <img src="{image_url}" alt="Top image"
         style="display: block; max-width: 720px; width: 100%; height: auto; max-height: 300px; object-fit: cover; border-radius: 6px;">
  </a>
  <div style="margin-top: 0.5rem;">
    <a href="{top_story["link"]}" target="_blank" style="text-decoration: none;">
      {top_story["title"]}
    </a>
  </div>
  <div class="source">{top_story["source"]} – {top_story["age"]}</div>
</div>
'''

# NEW: fetch upcoming launches (safe fail)
try:
    upcoming_launches = fetch_upcoming_launches(limit=8, days_ahead=7)
except Exception:
    upcoming_launches = []

# 📚 Section Columns
sections = ['<div class="columns">']
for source in feeds.keys():
    if source in sources:
        source_url = source_links.get(source, "#")
        section_html = f'<div class="column"><div class="section"><h2><a href="{source_url}" target="_blank">{source}</a></h2>'
        for a in sources[source][:8]:
            is_recent = (datetime.now(timezone.utc) - a["timestamp"]).total_seconds() < 7200
            recent_class = "recent" if is_recent else ""
            section_html += f'''
            <div class="headline {recent_class}">
              <a href="{a["link"]}" target="_blank">{a["title"]}</a>
              <span>({a["age"]})</span>
            </div>
            '''
        section_html += '</div></div>'
        sections.append(section_html)

# NEW: Append right-most column for Upcoming Launches
if upcoming_launches:
    rows = []
    for l in upcoming_launches:
        rows.append(f'''
        <div class="headline">
          <strong>{l["when"]}</strong> — {l["name"]}
          <div class="source" style="margin-top:2px;">{l["provider"]} • {l["pad"]}{(" — " + l["loc"]) if l["loc"] else ""}</div>
        </div>
        ''')
    credit = '<div class="source" style="margin-top:6px;">Data: <a href="https://thespacedevs.com/" target="_blank">Launch Library 2 (The Space Devs)</a></div>'
    launches_column_html = f'''
    <div class="column">
      <div class="section">
        <h2><a href="https://thespacedevs.com/" target="_blank">Upcoming Launches (next 7 days)</a></h2>
        {''.join(rows)}
        {credit}
      </div>
    </div>
    '''
    sections.append(launches_column_html)

sections.append('</div>')

# 🔧 Inject into index.html
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()
    
# --- Ensure Google Analytics tag exists in index.html (outside headline block) ---
GA_ID = "G-F0ZJXSLFMH"
ga_snippet = f"""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_ID}');
</script>
"""

# Only add it once
if GA_ID not in html:
    if "</head>" in html:
        # Insert right before </head> so it sits safely in the head section
        html = html.replace("</head>", ga_snippet + "\n</head>")
    else:
        # Fallback: if no <head> tag exists, add it at the very top
        html = ga_snippet + "\n" + html
# --- end GA ensure ---

start = html.find("<!-- START HEADLINES -->")
end = html.find("<!-- END HEADLINES -->")

if start != -1 and end != -1:
    new_content = '<!-- START HEADLINES -->\n' + top_html + "\n".join(sections) + '\n<!-- END HEADLINES -->'
    updated_html = html[:start] + new_content + html[end + len("<!-- END HEADLINES -->"):]
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(updated_html)
    print("✅ Headlines updated successfully.")
    # always trigger commit
    with open("index.html", "a", encoding="utf-8") as f:
        f.write(f"\n<!-- build-id: {randint(10000, 99999)} -->\n")
else:
    print("❌ Injection markers not found in index.html.")
