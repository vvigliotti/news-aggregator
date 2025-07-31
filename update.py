import feedparser
import re
from datetime import datetime, timezone, timedelta
from time import mktime

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

source_links = {
    "Breaking Defense": "https://breakingdefense.com",
    "SpaceNews": "https://spacenews.com",
    "Air & Space Forces": "https://www.airandspaceforces.com",
    "NASA News Releases": "https://www.nasa.gov/news-release/",
    "USSF – Headlines": "https://www.spaceforce.mil/News",
    "USSF – Lines of Effort": "https://www.spaceforce.mil/About-Us/Lines-of-Effort",
    "USSF – Field News": "https://www.spaceforce.mil/News/Field-News",
    "USSF – US Space Forces": "https://www.spaceforce.mil/News/Space-Force-Units"
}

def get_age_string(timestamp):
    now = datetime.now(timezone.utc)
    delta = now - timestamp
    minutes = int(delta.total_seconds() / 60)
    if minutes < 60:
        return f"{minutes}m ago"
    else:
        return f"{minutes // 60}h ago"

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
            continue

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

        all_items.append({
            "source": source,
            "title": entry.title,
            "link": entry.link,
            "timestamp": timestamp,
            "image": image,
            "age": get_age_string(timestamp)
        })

latest = sorted(all_items, key=lambda x: x["timestamp"], reverse=True)
top_story = latest[0] if latest else None
remaining = latest[1:] if len(latest) > 1 else []

sources = {}
for item in remaining:
    sources.setdefault(item["source"], []).append(item)

top_html = ""
if top_story:
    is_recent = (datetime.now(timezone.utc) - top_story["timestamp"]).total_seconds() < 7200
    top_class = "recent" if is_recent else ""
    top_html = f'''
<div class="top-story {top_class}">
  <a href="{top_story["link"]}" target="_blank" style="text-decoration:none;">
    {'<img src="' + top_story["image"] + '" alt="Top image"><br>' if top_story["image"] else ''}
    {top_story["title"]}
  </a>
  <div class="source">{top_story["source"]} – {top_story["age"]}</div>
</div>
'''

sections = ['<div class="columns">']
for source, articles in sources.items():
    source_url = source_links.get(source, "#")
    section_html = f'<div class="column"><div class="section"><h2><a href="{source_url}" target="_blank">{source}</a></h2>'
    for a in articles[:5]:
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
sections.append('</div>')

# Inject into HTML file
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

start = html.find("<!-- START HEADLINES -->")
end = html.find("<!-- END HEADLINES -->")

if start != -1 and end != -1:
    new_content = '<!-- START HEADLINES -->\n' + top_html + "\n".join(sections) + '\n<!-- END HEADLINES -->'
    updated_html = html[:start] + new_content + html[end + len("<!-- END HEADLINES -->"):]
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(updated_html)
    print("✅ Headlines updated successfully.")
else:
    print("❌ Injection markers not found in index.html.")
