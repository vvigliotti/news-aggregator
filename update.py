import feedparser
from datetime import datetime, timezone
from time import mktime
from bs4 import BeautifulSoup
import pytz
from jinja2 import Environment, FileSystemLoader

sources = {
    "media": {
        "Breaking Defense": {
            "url": "https://breakingdefense.com/feed/",
            "homepage": "https://breakingdefense.com/"
        },
        "SpaceNews": {
            "url": "https://spacenews.com/feed/",
            "homepage": "https://spacenews.com/"
        },
        "Air & Space Forces Magazine": {
            "url": "https://www.airandspaceforces.com/feed/",
            "homepage": "https://www.airandspaceforces.com/"
        },
        "The Verge – Space": {
            "url": "https://www.theverge.com/rss/space/index.xml",
            "homepage": "https://www.theverge.com/space"
        },
        "Ars Technica (Space)": {
            "url": "https://feeds.arstechnica.com/arstechnica/space/",
            "homepage": "https://arstechnica.com/space/"
        },
        "Military.com – Space": {
            "url": "https://www.military.com/rss/subject/19456/feed.xml",
            "homepage": "https://www.military.com/"
        }
    },
    "gov": {
        "Space Force – Headlines": {
            "url": "https://www.spaceforce.mil/RSS/headlines.xml",
            "homepage": "https://www.spaceforce.mil/"
        },
        "NASA News Releases": {
            "url": "https://www.nasa.gov/news-release/feed/",
            "homepage": "https://www.nasa.gov/"
        }
    },
    "intl": {
        "ESA – European Space Agency": {
            "url": "https://www.esa.int/rssfeed/Our_Activities",
            "homepage": "https://www.esa.int/"
        },
        "Phys.org – Space": {
            "url": "https://phys.org/rss-feed/space-news/",
            "homepage": "https://phys.org/space-news/"
        }
    }
}

now = datetime.now(timezone.utc)
max_articles = 8

structured = {cat: {} for cat in sources}
breaking_article = None
most_recent_time = None

for category, feeds in sources.items():
    for source, info in feeds.items():
        parsed = feedparser.parse(info["url"])
        entries = parsed.entries[:max_articles]
        articles = []

        for entry in entries:
            pub = entry.get("published_parsed") or entry.get("updated_parsed")
            if not pub:
                continue

            timestamp = datetime.fromtimestamp(mktime(pub), tz=timezone.utc)
            delta = now - timestamp
            minutes = int(delta.total_seconds() / 60)
            age_str = f"{minutes}m ago" if minutes < 60 else f"{minutes // 60}h ago"

            html = entry.get("content", [{}])[0].get("value", "") or entry.get("summary", "")
            soup = BeautifulSoup(html, "html.parser")
            image = ""
            img = soup.find("img")
            if img and img.has_attr("src"):
                image = img["src"]

            article = {
                "title": entry.title,
                "link": entry.link,
                "source": source,
                "homepage": info["homepage"],
                "timestamp": timestamp,
                "age": age_str,
                "is_new": delta.total_seconds() < 3600,
                "image": image
            }
            articles.append(article)

            if not most_recent_time or timestamp > most_recent_time:
                most_recent_time = timestamp
                breaking_article = article

        structured[category][source] = articles

# Render HTML
env = Environment(loader=FileSystemLoader("."))
template = env.get_template("template.html")
html = template.render(structured=structured, breaking=breaking_article, generated=now)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
