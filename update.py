import feedparser
import re
from datetime import datetime, timezone
from time import mktime

# Source homepages for hyperlinking
source_links = {
    "USSF – Headlines": "https://www.spaceforce.mil/News/",
    "USSF – Lines of Effort": "https://www.spaceforce.mil/About-Us/Lines-of-Effort/",
    "USSF – Field News": "https://www.spaceforce.mil/News/Field-News/",
    "USSF – US Forces": "https://www.spaceforce.mil/News/US-Space-Forces/",
    "NASA News Releases": "https://www.nasa.gov/news/",
    "Space Development Agency": "https://www.sda.mil/news.html",
    "Air & Space Forces Magazine": "https://www.airandspaceforces.com/",
    "Breaking Defense": "https://breakingdefense.com/",
    "SpaceNews": "https://spacenews.com/",
    "DefenseScoop": "https://defensescoop.com/",
    "Ars Technica (Space)": "https://arstechnica.com/science/space/",
    "The Verge – Space": "https://www.theverge.com/space",
    "Military.com – Space": "https://www.military.com/space",
    "ESA – European Space Agency": "https://www.esa.int/",
    "Phys.org – Space": "https://phys.org/space-news/"
}

# Column layout
columns = {
    "gov": {
        "USSF – Headlines": "https://www.spaceforce.mil/RSS/headlines.xml",
        "USSF – Lines of Effort": "https://www.spaceforce.mil/RSS/lines-of-effort.xml",
        "USSF – Field News": "https://www.spaceforce.mil/RSS/field-news.xml",
        "USSF – US Forces": "https://www.spaceforce.mil/RSS/us-space-forces-space.xml",
        "NASA News Releases": "https://www.nasa.gov/news-release/feed/",
        "Space Development Agency": "https://www.dvidshub.net/rss/unit/6071"  # SDA on DVIDS
    },
    "media": {
        "Air & Space Forces Magazine": "https://www.airandspaceforces.com/feed/",
        "Breaking Defense": "https://breakingdefense.com/feed/",
        "SpaceNews": "https://spacenews.com/feed/",
        "DefenseScoop": "https://preprod.defensescoop.com/feed/",
        "Ars Technica (Space)": "https://feeds.arstechnica.com/arstechnica/space/",
        "The Verge – Space": "https://www.theverge.com/rss/space/index.xml",
        "Military.com – Space": "https://www.military.com/rss/subject/19456/feed.xml"
    },
    "intl": {
        "ESA – European Space Agency": "https://www.esa.int/rssfeed/Our_Activities",
        "Phys.org – Space": "https://phys.org/rss-feed/space-news/"
    }
}

now = datetime.now(timezone.utc)
structured = {"gov": {}, "media": {}, "intl": {}}
all_items = []

# Parse feeds
for column, feeds in columns.items():
    for source, url in feeds.items():
        parsed = feedparser.parse(url)
        for entry in parsed.entries:
            pub = entry.get("published_parsed") or entry.get("updated_parsed")
            if not pub:
                continue
            timestamp = datetime.fromtimestamp(mktime(pub), tz=timezone.utc)
            delta = now - timestamp
            minutes = int(delta.total_seconds() / 60)
            age = f"{minutes}m ago" if minutes < 60 else f"{minutes // 60}h ago"

            # Flag recency
            tag = "breaking" if minutes < 60 else "recent" if minutes < 180 else ""

            # Extract image
            image = ""
            if "media_content" in entry and entry.media_content:
                image = entry.media_content[0].get("url", "")
            elif "media_thumbnail" in entry and entry.media_thumbnail:
                image = entry.media_thumbnail[0].get("url", "")
            elif "content" in entry:
                match = re.search(r'<img[^>]+src="([^">]+)"', entry.content[0].value)
                if match:
                    image = match.group(1)

            item = {
                "title": entry.title,
                "link": entry.link,
                "source": source,
                "timestamp": timestamp,
                "age": age,
                "tag": tag,
                "image": image
            }

            all_items.append(item)
            structured[column].setdefault(source, []).append(item)

# Get top headline
top_story = sorted(all_items, key=lambda x: x["timestamp"], reverse=True)[0]
banner_html = f'<a href="{top_story["link"]}" target="_blank">{top_story["title"]}</a>'

# Collect up to 6 unique image headlines
image_items = [i for i in all_items if i["image"]][:6]
image_html = ""
for i in image_items:
    image_html += f'''
    <div class="thumb">
      <a href="{i["link"]}" target="_blank">
        <img src="{i["image"]}" alt="headline image">
        <div class="caption">{i["title"]}</div>
      </a>
    </div>
    '''

# Build columns
def build_column(col_data):
    html = ""
    for source, items in col_data.items():
        link = source_links.get(source, "#")
        html += f'<div class="source-block"><h3><a href="{link}" target="_blank">{source}</a></h3>\n'
        for item in sorted(items, key=lambda x: x["timestamp"], reverse=True)[:5]:
            css = f'class="{item["tag"]}"' if item["tag"] else ""
            html += f'<div class="headline"><a {css} href="{item["link"]}" target="_blank">{item["title"]}</a><div class="meta">{item["age"]}</div></div>\n'
        html += '<hr></div>\n'
    return html

gov_html = build_column(structured["gov"])
media_html = build_column(structured["media"])
intl_html = build_column(structured["intl"])

# Inject into HTML
with open("index.html", "r") as f:
    html = f.read()

# Top banner headline
html = re.sub(r'<!-- TOP BANNER START -->(.*?)<!-- TOP BANNER END -->', f'<!-- TOP BANNER START -->{banner_html}<!-- TOP BANNER END -->', html, flags=re.DOTALL)

# Thumbnail block
html = re.sub(r'<!-- IMAGES START -->(.*?)<!-- IMAGES END -->', f'<!-- IMAGES START -->{image_html}<!-- IMAGES END -->', html, flags=re.DOTALL)

# Column content
start = html.find("<!-- START HEADLINES -->")
end = html.find("<!-- END HEADLINES -->")
if start != -1 and end != -1:
    final = f'''<!-- START HEADLINES -->
    <div class="columns">
      <div class="column"><h2>🚀 GOVERNMENT</h2>{gov_html}</div>
      <div class="column"><h2>📰 MEDIA</h2>{media_html}</div>
      <div class="column"><h2>🌍 INTERNATIONAL</h2>{intl_html}</div>
    </div>
    <!-- END HEADLINES -->'''
    html = html[:start] + final + html[end + len("<!-- END HEADLINES -->"):]

with open("index.html", "w") as f:
    f.write(html)
