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

# Collect and time-stamp articles
for source, url in feeds.items():
    parsed = feedparser.parse(url)
    for entry in parsed.entries:
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        if not published:
            continue
        timestamp = datetime.fromtimestamp(mktime(published))
        image = ""

        # Try to grab thumbnail
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

# Sort and trim to most recent 20
latest = sorted(all_items, key=lambda x: x["timestamp"], reverse=True)[:20]

# Build HTML
headline_blocks = []
for i, item in enumerate(latest):
    block = ""
    if i < 5 and item["image"]:  # Show image for top 5 only
        block += f'<div class="headline featured">'
        block += f'<a href="{item["link"]}" target="_blank">'
        block += f'<img src="{item["image"]}" alt="thumbnail"><br>'
        block += f'{item["title"]}</a><div class="source">{item["source"]}</div></div>'
    else:
        block += f'<div class="headline"><a href="{item["link"]}" target="_blank">{item["title"]}</a><div class="source">{item["source"]}</div></div>'
    headline_blocks.append(block)

# Inject into HTML
with open("index.html", "r") as f:
    html = f.read()

start = html.find("<!-- START HEADLINES -->")
end = html.find("<!-- END HEADLINES -->")

if start != -1 and end != -1:
    new_content = '<!-- START HEADLINES -->\n' + "\n".join(headline_blocks) + '\n<!-- END HEADLINES -->'
    updated_html = html[:start] + new_content + html[end + len("<!-- END HEADLINES -->"):]
    with open("index.html", "w") as f:
        f.write(updated_html)
