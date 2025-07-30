import feedparser
from datetime import datetime

feeds = {
    "media": [
        {"name": "SpaceNews", "url": "https://spacenews.com/feed/"},
        {"name": "Breaking Defense", "url": "https://breakingdefense.com/feed/"},
        {"name": "Air & Space Forces Magazine", "url": "https://www.airandspaceforces.com/feed/"},
        {"name": "DefenseScoop", "url": "https://defensescoop.com/feed/"},
        {"name": "Ars Technica (Space)", "url": "https://feeds.arstechnica.com/arstechnica/space"},
        {"name": "The Verge (Space)", "url": "https://www.theverge.com/rss/index.xml"},
        {"name": "Military.com", "url": "https://www.military.com/rss-feeds"}
    ],
    "gov": [
        {"name": "USSF", "url": "https://www.spaceforce.mil/DesktopModules/ArticleCS/rss.ashx?ContentType=1&Site=496"},
        {"name": "SSC", "url": "https://www.ssc.spaceforce.mil/Portals/3/rss/ssc-news.xml"},
        {"name": "STARCOM", "url": "https://www.starcom.spaceforce.mil/DesktopModules/ArticleCS/rss.ashx?ContentType=1&Site=492"},
        {"name": "SpOC", "url": "https://www.spoc.spaceforce.mil/DesktopModules/ArticleCS/rss.ashx?ContentType=1&Site=494"},
        {"name": "USSPACECOM", "url": "https://www.spacecom.mil/DesktopModules/ArticleCS/rss.ashx?ContentType=1&Site=513"},
        {"name": "NASA", "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss"},
        {"name": "Space Development Agency", "url": "https://www.sda.mil/feed.xml"}
    ],
    "international": [
        {"name": "ESA", "url": "https://www.esa.int/rssfeed/Our_Activities"},
        {"name": "Phys.org (Space)", "url": "https://phys.org/rss-feed/space-news/"}
    ]
}

def fetch_articles(feed_info, limit=5):
    feed = feedparser.parse(feed_info["url"])
    articles = []
    for entry in feed.entries[:limit]:
        articles.append(f'<li><a href="{entry.link}" target="_blank">{entry.title}</a></li>')
    return articles

def build_column(title, links):
    return f'<div class="column"><h2>{title}</h2><ul>{"".join(links)}</ul></div>'

columns_html = {"media": [], "gov": [], "international": []}
top_story = None

for section in feeds:
    for source in feeds[section]:
        entries = fetch_articles(source)
        if not top_story and entries:
            top_story = entries[0]
        columns_html[section].extend(entries)

timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Space Headlines</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    body {{
      font-family: Arial, sans-serif;
      background: #111;
      color: white;
      margin: 0;
      padding: 20px;
    }}
    h1 {{
      text-align: center;
    }}
    .banner {{
      background: red;
      color: white;
      padding: 10px;
      text-align: center;
      font-weight: bold;
    }}
    .columns {{
      display: flex;
      flex-wrap: wrap;
      gap: 20px;
      margin-top: 20px;
    }}
    .column {{
      flex: 1;
      min-width: 280px;
      border-left: 1px solid gray;
      padding-left: 15px;
    }}
    .column:first-child {{
      border-left: none;
      padding-left: 0;
    }}
    ul {{
      padding-left: 0;
      list-style: none;
    }}
    li {{
      margin-bottom: 10px;
    }}
    a {{
      color: white;
      text-decoration: none;
    }}
    a:hover {{
      color: red;
    }}
    footer {{
      margin-top: 40px;
      text-align: center;
      font-size: 0.8em;
      color: gray;
    }}
  </style>
</head>
<body>
  <div class="banner">🚨 Breaking: {top_story if top_story else "No stories available"}</div>
  <h1>Space Headlines</h1>
  <div class="columns">
    {build_column("Media", columns_html['media'])}
    {build_column("Government & Military", columns_html['gov'])}
    {build_column("International & Science", columns_html['international'])}
  </div>
  <footer>
    Last updated: {timestamp}<br>
    <a href="mailto:vigliottivictor@gmail.com">Contact</a>
  </footer>
</body>
</html>
"""

with open("index.html", "w") as f:
    f.write(html)
