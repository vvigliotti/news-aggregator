import feedparser
from datetime import datetime, timezone
from bs4 import BeautifulSoup

# Source homepages
source_homepages = {
    "Air & Space Forces Magazine": "https://www.airandspaceforces.com",
    "Breaking Defense": "https://breakingdefense.com",
    "SpaceNews": "https://spacenews.com",
    "DefenseScoop": "https://defensescoop.com",
    "Ars Technica – Space": "https://arstechnica.com/science/space/",
    "The Verge – Space": "https://www.theverge.com/space",
    "Military.com – Space": "https://www.military.com",

    "USSF": "https://www.spaceforce.mil",
    "SSC": "https://www.ssc.spaceforce.mil",
    "STARCOM": "https://www.starcom.spaceforce.mil",
    "SpOC": "https://www.spoc.spaceforce.mil",
    "USSPACECOM": "https://www.spacecom.mil",
    "NASA": "https://www.nasa.gov",
    "Space Development Agency": "https://www.sda.mil",

    "ESA – European Space Agency": "https://www.esa.int",
    "Phys.org – Space": "https://phys.org/space-news/"
}

# RSS feed URLs by section
sources = {
    "Media": {
        "Air & Space Forces Magazine": "https://www.airandspaceforces.com/feed/",
        "Breaking Defense": "https://breakingdefense.com/feed/",
        "SpaceNews": "https://spacenews.com/feed/",
        "DefenseScoop": "https://defensescoop.com/feed/",
        "Ars Technica – Space": "https://arstechnica.com/science/space/feed/",
        "The Verge – Space": "https://www.theverge.com/space/rss/index.xml",
        "Military.com – Space": "https://www.military.com/rss-feeds/military-space.xml"
    },
    "Government & Military": {
        "USSF": "https://www.spaceforce.mil/DesktopModules/ArticleCS/rss.ashx?ContentType=1&Site=1470",
        "SSC": "https://www.ssc.spaceforce.mil/Portals/3/rss.xml",
        "STARCOM": "https://www.starcom.spaceforce.mil/DesktopModules/ArticleCS/rss.ashx?ContentType=1&Site=1264",
        "SpOC": "https://www.spoc.spaceforce.mil/DesktopModules/ArticleCS/rss.ashx?ContentType=1&Site=1399",
        "USSPACECOM": "https://www.spacecom.mil/DesktopModules/ArticleCS/rss.ashx?ContentType=1&Site=1236",
        "NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "Space Development Agency": "https://www.sda.mil/rss"
    },
    "International & Science": {
        "ESA – European Space Agency": "https://www.esa.int/rssfeed/Our_Activities",
        "Phys.org – Space": "https://phys.org/rss-feed/breaking/space-news/"
    }
}

# Parse and collect all headlines
all_headlines = []

for category, feeds in sources.items():
    for source_name, feed_url in feeds.items():
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            published = None
            if 'published_parsed' in entry and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif 'updated_parsed' in entry and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            else:
                continue
            all_headlines.append({
                'title': entry.title,
                'link': entry.link,
                'published': published,
                'source': source_name,
                'category': category
            })

# Sort all headlines by time
all_headlines.sort(key=lambda x: x['published'], reverse=True)

# Choose breaking headline
breaking_headline = all_headlines[0]

# Group headlines by category then source
grouped = {}
for headline in all_headlines:
    cat = headline['category']
    src = headline['source']
    grouped.setdefault(cat, {}).setdefault(src, []).append(headline)

# HTML generation
def escape_html(text):
    return BeautifulSoup(text, "html.parser").text

def generate_html():
    now = datetime.now().strftime("%-m/%-d/%Y, %-I:%M:%S %p")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Space Headlines</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, sans-serif;
      margin: 0; padding: 1rem;
      background-color: white;
      color: black;
      transition: background 0.2s, color 0.2s;
    }}
    .dark-mode {{
      background-color: #121212;
      color: white;
    }}
    h1 {{ text-align: center; margin-bottom: 0; }}
    h2 {{ border-bottom: 2px solid #000; }}
    .section {{ display: flex; flex-direction: column; gap: 2rem; }}
    .columns {{
      display: flex;
      flex-direction: column;
    }}
    @media (min-width: 768px) {{
      .columns {{ flex-direction: row; gap: 1rem; }}
      .column {{ flex: 1; }}
    }}
    .source-block {{
      border-bottom: 1px solid gray;
      margin-bottom: 1rem;
    }}
    .source-block:last-child {{ border: none; }}
    .headline a {{
      text-decoration: none;
      display: block;
      margin: 0.2rem 0;
    }}
    .breaking {{
      text-align: center;
      font-weight: bold;
      color: red;
      font-size: 1.1rem;
    }}
    .breaking-source {{
      text-align: center;
      font-style: italic;
      font-size: 0.9rem;
      margin-bottom: 1rem;
    }}
    a {{ color: inherit; }}
    .red {{ color: red; }}
    .form-footer {{ margin-top: 2rem; text-align: center; }}
    .form-footer textarea {{ width: 80%; max-width: 600px; height: 100px; }}
    .form-footer input[type="submit"] {{
      margin-top: 10px;
      padding: 5px 15px;
      font-size: 1rem;
    }}
  </style>
</head>
<body>
  <button onclick="document.body.classList.toggle('dark-mode')" style="float:right">Toggle Dark Mode</button>
  <h1>SPACE HEADLINES</h1>
  <p style="text-align:center">{now}</p>
  <p class="breaking">{escape_html(breaking_headline['title']).upper()}</p>
  <p class="breaking-source"><em>{escape_html(breaking_headline['source'])}</em></p>
  <div class="columns">
"""

    for category in ["Media", "Government & Military", "International & Science"]:
        html += f'<div class="column"><h2>{category}</h2>'
        for source, articles in grouped.get(category, {}).items():
            homepage = source_homepages.get(source, "#")
            html += f'<div class="source-block"><h3><a href="{homepage}">{source}</a></h3>'
            for article in articles:
                time_str = article['published'].strftime('%-I:%M %p · %b %d') if article['published'] else ''
                is_breaking = article['link'] == breaking_headline['link']
                red_class = 'red' if is_breaking else ''
                html += f'<div class="headline"><a href="{article["link"]}" class="{red_class}">{escape_html(article["title"])}</a>'
                html += f'<div style="font-size: 0.85rem; color: gray;">{escape_html(article["source"])} · {time_str}</div></div>'
            html += '</div>'
        html += '</div>'

    html += f"""
  </div>
  <div class="form-footer">
    <h3>Submit a Question</h3>
    <form action="https://formspree.io/f/xnnzzdjz" method="POST">
      <label for="question">Your Question:</label><br>
      <textarea name="question" required></textarea><br>
      <input type="submit" value="Submit">
    </form>
    <h3>Daily Visitors</h3>
    <iframe src="https://www.freevisitorcounters.com/en/home/counter/1371441/t/0" frameborder="0" scrolling="no" style="border:none; height:70px; width:150px;"></iframe>
  </div>
</body>
</html>"""
    return html

# Write output
with open("index.html", "w", encoding="utf-8") as f:
    f.write(generate_html())
