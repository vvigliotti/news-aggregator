import feedparser
import json

# RSS feed mapping
FEEDS = {
    "media": [
        "https://breakingdefense.com/feed/",
        "https://spacenews.com/feed/",
        "https://www.airandspaceforces.com/feed/",
        "https://defensescoop.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://www.military.com/rss.xml"
    ],
    "gov": [
        "https://www.spaceforce.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1264",
        "https://ssc.spaceforce.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1276",
        "https://www.starcom.spaceforce.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1271",
        "https://www.spoc.spaceforce.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1270",
        "https://www.spacecom.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1275",
        "https://www.nasa.gov/news-release/feed/",
        "https://www.sda.mil/feed.xml"
    ],
    "international": [
        "https://www.esa.int/rssfeed/Our_Activities",
        "https://phys.org/rss-feed/space-news/",
    ]
}

MAX_ITEMS_PER_FEED = 4

def clean_title(title):
    return title.replace("&#8217;", "'").replace("&quot;", '"').strip()

def fetch_feed(url):
    parsed = feedparser.parse(url)
    items = []
    for entry in parsed.entries[:MAX_ITEMS_PER_FEED]:
        title = clean_title(entry.title)
        link = entry.link
        items.append({"title": title, "link": link})
    return items

def main():
    all_items = {}
    for category, urls in FEEDS.items():
        items = []
        for url in urls:
            try:
                items.extend(fetch_feed(url))
            except Exception as e:
                print(f"Error fetching {url}: {e}")
        # Sort by most recent if date available
        all_items[category] = items[:12]

    with open("headlines.json", "w") as f:
        json.dump(all_items, f, indent=2)

if __name__ == "__main__":
    main()
