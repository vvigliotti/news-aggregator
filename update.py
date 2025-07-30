
import feedparser
import re
from datetime import datetime, timezone
from time import mktime

source_links = {
    "NASA News Releases": "https://www.nasa.gov",
    "Air & Space Forces Magazine": "https://www.airandspaceforces.com",
    "Breaking Defense": "https://breakingdefense.com",
    "SpaceNews": "https://spacenews.com",
    "SpaceRef": "https://spaceref.com",
    "Ars Technica (Space)": "https://arstechnica.com/space",
    "The Verge – Space": "https://www.theverge.com/space",
    "Military.com – Space": "https://www.military.com/space",
    "ESA – European Space Agency": "https://www.esa.int",
    "Phys.org – Space": "https://phys.org/space-news/",
    "Space Force – Headlines": "https://www.spaceforce.mil",
    "Space Force – Lines of Effort": "https://www.spaceforce.mil",
    "Space Force – Field News": "https://www.spaceforce.mil",
    "Space Force – US Forces": "https://www.spaceforce.mil"
}

columns = {
    "media": {
        "Air & Space Forces Magazine": "https://www.airandspaceforces.com/feed/",
        "Breaking Defense": "https://breakingdefense.com/feed/",
        "SpaceNews": "https://spacenews.com/feed/",
        "SpaceRef": "https://spaceref.com/rss/",
        "Ars Technica (Space)": "https://feeds.arstechnica.com/arstechnica/space/",
        "The Verge – Space": "https://www.theverge.com/rss/space/index.xml",
        "Military.com – Space": "https://www.military.com/rss/subject/19456/feed.xml"
    },
    "gov": {
        "Space Force – Headlines": "https://www.spaceforce.mil/RSS/headlines.xml",
        "Space Force – Lines of Effort": "https://www.spaceforce.mil/RSS/lines-of-effort.xml",
        "Space Force – Field News": "https://www.spaceforce.mil/RSS/field-news.xml",
        "Space Force – US Forces": "https://www.spaceforce.mil/RSS/us-space-forces-space.xml",
        "NASA News Releases": "https://www.nasa.gov/news-release/feed/"
    },
    "intl": {
        "ESA – European Space Agency": "https://www.esa.int/rssfeed/Our_Activities",
        "Phys.org – Space": "https://phys.org/rss-feed/space-news/"
    }
}

now = datetime.now(timezone.utc)
structured = {"media": {}, "gov": {}, "intl": {}}
all_articles = []

for section, feeds in columns.items():
    for source, url in feeds.items():
        parsed = feedparser.parse(url)
        for entry in parsed.entries:
            pub = entry.get("published_parsed") or entry.get("updated_parsed")
            if not pub:
                continue
            timestamp = datetime.fromtimestamp(mktime(pub), tz=timezone.utc)
            delta = now - timestamp
            age_str = f"{int(delta.total_seconds() / 60)}m ago" if delta.total_seconds() < 3600 else f"{int(delta.total_seconds() / 3600)}h ago"
            is_new = delta.total_seconds() < 3600

            article = {
                "title": entry.title,
                "link": entry.link,
                "source": source,
                "timestamp": timestamp,
                "age": age_str,
                "is_new": is_new
            }

            structured[section].setdefault(source, []).append(article)
            all_articles.append(article)

for section in structured:
    for source in structured[section]:
        structured[section][source] = sorted(structured[section][source], key=lambda x: x["timestamp"], reverse=True)[:6]

breaking_article = max([a for a in all_articles if a["is_new"]], key=lambda x: x["timestamp"], default=None)

def build_column(section_dict):
    html = ""
    for source, articles in section_dict.items():
        link = source_links.get(source, "#")
        html += f'<h3><a href="{link}" target="_blank">{source}</a></h3>\n'
        for article in articles:
            color = "red" if article["is_new"] else "black"
            html += f'<div class="headline"><a href="{article["link"]}" target="_blank" style="color:{color}">{article["title"]}</a><div class="meta">{article["source"]} · {article["age"]}</div></div>\n'
    return html

media_html = build_column(structured["media"])
gov_html = build_column(structured["gov"])
intl_html = build_column(structured["intl"])
breaking_html = f'<a href="{breaking_article["link"]}" target="_blank">{breaking_article["title"]}</a> · {breaking_article["source"]} · {breaking_article["age"]}' if breaking_article else ""

with open("index.html", "r") as f:
    html = f.read()

def inject_after_tag(html, tag_id, content):
    marker = f'<div class="column" id="{tag_id}">'
    start = html.find(marker)
    if start == -1:
        return html
    insert_point = html.find("</h2>", start)
    return html[:insert_point+5] + content + html[insert_point+5:]

html = inject_after_tag(html, "media-column", media_html)
html = inject_after_tag(html, "gov-column", gov_html)
html = inject_after_tag(html, "intl-column", intl_html)

# Replace breaking headline
start = html.find('<div class="breaking-banner" id="breaking-headline">')
end = html.find("</div>", start)
if start != -1 and end != -1:
    html = html[:start] + f'<div class="breaking-banner" id="breaking-headline">{breaking_html}' + html[end:]

with open("index.html", "w") as f:
    f.write(html)
