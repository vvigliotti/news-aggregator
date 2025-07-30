import feedparser
import re
from datetime import datetime, timezone
from time import mktime

# Feeds grouped by category
columns = {
    "gov": {
        "Space Force – Headlines": "https://www.spaceforce.mil/RSS/headlines.xml",
        "Space Force – Lines of Effort": "https://www.spaceforce.mil/RSS/lines-of-effort.xml",
        "Space Force – Field News": "https://www.spaceforce.mil/RSS/field-news.xml",
        "Space Force – US Forces": "https://www.spaceforce.mil/RSS/us-space-forces-space.xml",
        "NASA News Releases": "https://www.nasa.gov/news-release/feed/"
    },
    "media": {
        "Air & Space Forces Magazine": "https://www.airandspaceforces.com/feed/",
        "Breaking Defense": "https://breakingdefense.com/feed/",
        "SpaceNews": "https://spacenews.com/feed/",
        "SpaceRef": "https://spaceref.com/rss/",
        "Ars Technica (Space)": "https://feeds.arstechnica.com/arstechnica/space/",
        "The Verge – Space": "https://www.theverge.com/rss/space/index.xml",
        "Military.com – Space": "https://www.military.com/rss/subject/19456/feed.xml"
    },
    "intl": {
        "ESA – European Space Agency": "https://www.esa.int/rssfeed/Our_Activities",
        "Phys.org – Space": "https://phys.org/rss-feed/space-news/"
    }
}

# Parse and collect articles
now = datetime.now(timezone.utc)
structured = {"gov": [], "media": [], "intl": []}

for group, feeds in columns.items():
    for source, url in feeds.items():
        parsed = feedparser.parse(url)
        for entry in parsed.entries:
            pub = entry.get("published_parsed") or entry.get("updated_parsed")
            if not pub:
                continue
            timestamp = datetime.fromtimestamp(mktime(pub), tz=timezone.utc)
            delta = now - timestamp
            minutes = int(delta.total_seconds() / 60)
            age_str = f"{minutes}m ago" if minutes < 60 else f"{minutes//60}h ago"

            # Try to extract an image
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

            structured[group].append({
                "title": entry.title,
                "link": entry.link,
                "source": source,
                "image": image,
                "timestamp": timestamp,
                "age": age_str,
                "is_new": delta.total_seconds() < 3600  # mark breaking headlines
            })

# Sort each group by time and trim
for key in structured:
    structured[key] = sorted(structured[key], key=lambda x: x["timestamp"], reverse=True)[:15]

# Build HTML block
def build_column(articles):
    html = ""
    for item in articles:
        color = "red" if item["is_new"] else "black"
        html += f'<div class="headline"><a href="{item["link"]}" target="_blank" style="color:{color}">{item["title"]}</a><div class="meta">{item["source"]} · {item["age"]}</div></div>\n'
    return html

gov_html = build_column(structured["gov"])
media_html = build_column(structured["media"])
intl_html = build_column(structured["intl"])

# Inject into index.html
with open("index.html", "r") as f:
    html = f.read()

start = html.find("<!-- START HEADLINES -->")
end = html.find("<!-- END HEADLINES -->")

if start != -1 and end != -1:
    new_content = f'''<!-- START HEADLINES -->
<div class="columns">
  <div class="column">{gov_html}</div>
  <div class="column">{media_html}</div>
  <div class="column">{intl_html}</div>
</div>
<!-- END HEADLINES -->'''
    updated_html = html[:start] + new_content + html[end + len("<!-- END HEADLINES -->"):]
    with open("index.html", "w") as f:
        f.write(updated_html)
