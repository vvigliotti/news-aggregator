import feedparser
from jinja2 import Template
from datetime import datetime
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

all_items = []

# Parse feeds
for source, url in feeds.items():
    parsed = feedparser.parse(url)
    for entry in parsed.entries:
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        if not published:
            continue
        timestamp = datetime.fromtimestamp(mktime(published))
        image = ""

        # Try to grab image
        if "media_content" in entry:
            image = entry.media_content[0].get("url", "")
        elif "media_thumbnail" in entry:
            image = entry.media_thumbnail[0].get("url", "")

        all_items.append({
            "source": source,
            "title": entry.title,
            "link": entry.link,
            "timestamp": timestamp,
            "image": image
        })

# Sort by date
latest = sorted(all_items, key=lambda x: x["timestamp"], reverse=True)[:20]

# Separate top story
top_story = latest[0]
remaining = latest[1:]

# Organize by source
sources = {}
for item in remaining:
    sources.setdefault(item["source"], []).append(item)

# Build HTML output
top_html = f'''
<div class="top-story">
  <a href="{top_story["link"]}" target="_blank">
    {'<img src="' + top_story["image"] + '" alt="top image"><br>' if top_story["image"] else ''}
    {top_story["title"]}
  </a>
  <div class="source">{top_story["source"]}</div>
</div>
'''

sections = []
for source, articles in sources.items():
    section_html = f'<div class="section"><h2>{source}</h2>'
    for a in articles[:5]:
        section_html += f'<div class="headline"><a href="{a["link"]}" target="_blank">{a["title"]}</a></div>'
    section_html += '</div>'
    sections.append(section_html)

# Inject into HTML
with open("index.html", "r") as f:
    html = f.read()

start = html.find("<!-- START HEADLINES -->")
end = html.find("<!-- END HEADLINES -->")

if start != -1 and end != -1:
    new_content = '<!-- START HEADLINES -->\n' + top_html + "\n".join(sections) + '\n<!-- END HEADLINES -->'
    updated_html = html[:start] + new_content + html[end + len("<!-- END HEADLINES -->"):]
    with open("index.html", "w") as f:
        f.write(updated_html)
