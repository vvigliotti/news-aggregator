import feedparser
from jinja2 import Template

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

headlines = {}

for source, url in feeds.items():
    parsed = feedparser.parse(url)
    items = parsed.entries[:8]
    headlines[source] = [
        f'<div class="headline"><a href="{entry.link}" target="_blank">{entry.title}</a></div>'
        for entry in items
    ]

with open("index.html", "r") as f:
    html = f.read()

start = html.find("<!-- START HEADLINES -->")
end = html.find("<!-- END HEADLINES -->")

if start != -1 and end != -1:
    content = '<!-- START HEADLINES -->\n'
    for source, items in headlines.items():
        content += f'<div class="feed-section"><h2>{source}</h2>\n' + "\n".join(items) + "\n</div>\n"
    content += '<!-- END HEADLINES -->'

    updated_html = html[:start] + content + html[end + len("<!-- END HEADLINES -->"):]
    
    with open("index.html", "w") as f:
        f.write(updated_html)
