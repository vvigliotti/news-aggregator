import feedparser
from datetime import datetime, timezone
from time import mktime
import re

# ---- FEED CONFIGURATION ----

columns = {
    "gov": {
        "US Space Force": "https://www.spaceforce.mil/RSS/headlines.xml",
        "NASA": "https://www.nasa.gov/news-release/feed/",
        "Space Development Agency": "https://www.dvidshub.net/rss/unit/7456",
    },
    "media": {
        "Breaking Defense": "https://breakingdefense.com/feed/",
        "Air & Space Forces Magazine": "https://www.airandspaceforces.com/feed/",
        "SpaceNews": "https://spacenews.com/feed/",
        "DefenseScoop": "https://preprod.defensescoop.com/feed/",
        "The Verge – Space": "https://www.theverge.com/space/rss/index.xml",
        "Ars Technica – Space": "https://feeds.arstechnica.com/arstechnica/space",
        "Military.com": "https://www.military.com/rss-feeds",
    },
    "intl": {
        "European Space Agency": "https://www.esa.int/rssfeed/Our_Activities",
        "Phys.org – Space": "https://phys.org/rss-feed/space-news/",
    }
}

source_links = {
    "US Space Force": "https://www.spaceforce.mil",
    "NASA": "https://www.nasa.gov",
    "Space Development Agency": "https://www.sda.mil",
    "Breaking Defense": "https://breakingdefense.com",
    "Air & Space Forces Magazine": "https://www.airandspaceforces.com",
    "SpaceNews": "https://spacenews.com",
    "DefenseScoop": "https://defensescoop.com",
    "The Verge – Space": "https://www.theverge.com/space",
    "Ars Technica – Space": "https://arstechnica.com/science/space",
    "Military.com": "https://www.military.com",
    "European Space Agency": "https://www.esa.int",
    "Phys.org – Space": "https://phys.org"
}

# ---- PARSE AND ORGANIZE FEEDS ----

def get_entries(feed_url, max_items=5):
    feed = feedparser.parse(feed_url)
    entries = []
    for entry in feed.entries[:max_items]:
        title = entry.title
        link = entry.link
        try:
            published = datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
        except:
            published = datetime.now(tz=timezone.utc)
        entries.append({
            "title": title,
            "link": link,
            "published": published
        })
    return entries

data = {col: {} for col in columns}
all_items = []

for col in columns:
    for source, url in columns[col].items():
        items = get_entries(url)
        for i in items:
            i["source"] = source
        data[col][source] = items
        all_items.extend(items)

# ---- SORT + IDENTIFY TOP HEADLINE ----

all_items.sort(key=lambda x: x["published"], reverse=True)
top_story = all_items[0]

banner_html = f'<strong>Breaking from {top_story["source"]}:</strong> <a href="{top_story["link"]}" target="_blank">{top_story["title"]}</a>'

# ---- BUILD FINAL HTML BLOCK ----

def build_column(col_data):
    html = '<div class="columns">\n'
    for col, feeds in col_data.items():
        html += '<div class="column">\n'
        html += f'<h2>{col.upper()}</h2>\n'
        for source, items in feeds.items():
            html += f'<div class="source-block"><h3><a href="{source_links.get(source, "#")}" target="_blank">{source}</a></h3>\n'
            for item in items:
                minutes_ago = int((datetime.now(timezone.utc) - item["published"]).total_seconds() / 60)
                if minutes_ago < 60:
                    cls = "breaking"
                elif minutes_ago < 180:
                    cls = "recent"
                else:
                    cls = ""
                html += f'<div class="headline {cls}"><a href="{item["link"]}" target="_blank">{item["title"]}</a></div>\n'
            html += '</div>\n'
        html += '</div>\n'
    html += '</div>\n'
    return html

column_html = build_column(data)

# ---- WRITE TO index.html ----

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

html = re.sub(r"<!-- TOP BANNER START -->(.*?)<!-- TOP BANNER END -->", f"<!-- TOP BANNER START -->\n{banner_html}\n<!-- TOP BANNER END -->", html, flags=re.DOTALL)
html = re.sub(r"<!-- START HEADLINES -->(.*?)<!-- END HEADLINES -->", f"<!-- START HEADLINES -->\n{column_html}\n<!-- END HEADLINES -->", html, flags=re.DOTALL)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Update complete.")
