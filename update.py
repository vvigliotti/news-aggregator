import feedparser
import re
from datetime import datetime, timezone, timedelta
from time import mktime

# RSS feed sources
feeds = {
    "Breaking Defense": "https://breakingdefense.com/feed/",
    "SpaceNews": "https://spacenews.com/feed/",
    "Air & Space Forces": "https://www.airandspaceforces.com/feed/",
    "NASA News Releases": "https://www.nasa.gov/news-release/feed/",
    "USSF – Headlines": "https://www.spaceforce.mil/RSS/headlines.xml",
    "USSF – Lines of Effort": "https://www.spaceforce.mil/RSS/lines-of-effort.xml",
    "USSF – Field News": "https://www.spaceforce.mil/RSS/field-news.xml",
    "USSF – US Space Forces": "https://www.spaceforce.mil/RSS/us-space-forces-space.xml"
}

# Helper to get time delta string (e.g., 2h ago)
def get_age_string(timestamp):
    now = datetime.now(timezone.utc)
    delta = now - timestamp
    minutes = int(delta.total_seconds() / 60)
    if minutes < 60:
        return f"{minutes}m ago"
    else:
        return f"{minutes // 60}h ago"

# Time threshold: last 36 hours only
cutoff = datetime.now(timezone.utc) - timedelta(hours=36)
all_items = []

for source, url in feeds.items():
    parsed = feedparser.parse(url)
    for entry in parsed.entries:
        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        if not pub:
            continue
        timestamp = datetime.fromtimestamp(mktime(pub), tz=timezone.utc)
        if timestamp < cutoff:
            continue  # Skip old articles

        # Try to extract image
        image = ""
        if "media_content" in entry and entry.media_content:
            image = entry.media_content[0].get("url", "")
        elif "media_thumbnail" in entry and entry.media_thumbnail:
            image = entry.media_thumbnail[0].get("url", "")
        elif "content" in entry:
            html_content = entry.content[0].value
            match = re.search(r'<img[^>]+src="([^">]+)"', html_content)
            if match:
                image = match.group(1)
        elif "image" in entry:
            image = entry.image.get("href", "")

        all_items.append({
            "source": source,
            "title": entry.title,
            "link": entry.link,
            "timestamp": timestamp,
            "image": image,
            "age": get_age_string(timestamp)
        })

# Sort by freshness
latest = sorted(all_items, key=lambda x: x["timestamp"], reverse=True)

# Top story: freshest single article
top_story = latest[0] if latest else None
remaining = latest[1:] if len(latest) > 1 else []

# Group remaining by source
sources = {}
for item in remaining:
    sources.setdefault(item["source"], []).append(item)

# Build top story block
top_html = ""
if top_story:
    top_html = f'''
<div class="top-story" style="font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">
  <a href="{top_story["link"]}" target="_blank" style="color: red; text-decoration: none;">
    {'<img src="' + top_story["image"] + '" alt="Top image" style="max-width: 100%;"><br>' if top_story["image"] else ''}
    {top_story["title"]}
  </a>
  <div style="font-size: 0.9rem; color: gray; font-weight: normal;">{top_story["source"]} – {top_story["age"]}</div>
</div>
'''

# Build all sections by source
sections = []
for source, articles in sources.items():
    section_html = f'<div class="section"><h2>{source}</h2>'
    for a in articles[:5]:  # Max 5 per source
        # Highlight articles under 1 hour old
        is_recent = (datetime.now(timezone.utc) - a["timestamp"]).total_seconds() < 3600
        recent_class = "recent" if is_recent else ""
        
        section_html += f'''
        <div class="headline {recent_class}">
          <a href="{a["link"]}" target="_blank">{a["title"]}</a>
          <span style="font-size: 0.8rem; color: gray;">({a["age"]})</span>
        </div>
        '''
    section_html += '</div>'
    sections.append(section_html)

# Inject new content between markers
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

start = html.find("<!-- START HEADLINES -->")
end = html.find("<!-- END HEADLINES -->")

if start != -1 and end != -1:
    new_content = '<!-- START HEADLINES -->\n' + top_html + "\n".join(sections) + '\n<!-- END HEADLINES -->'
    updated_html = html[:start] + new_content + html[end + len("<!-- END HEADLINES -->"):]
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(updated_html)
