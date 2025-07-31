import feedparser
import re
import random
from datetime import datetime, timezone, timedelta
from time import mktime

# FEED SOURCES
feeds = {
    # 📰 Top 3 Media
    "SpaceNews": "https://spacenews.com/feed/",
    "Breaking Defense": "https://breakingdefense.com/feed/",
    "Air & Space Forces": "https://www.airandspaceforces.com/feed/",

    # 🛰️ Government & Military
    "USSF - Headlines": "https://www.spaceforce.mil/RSS/headlines.xml",
    "USSF - Lines of Effort": "https://www.spaceforce.mil/RSS/lines-of-effort.xml",
    "USSF - Field News": "https://www.spaceforce.mil/RSS/field-news.xml",
    "USSF - US Space Forces": "https://www.spaceforce.mil/RSS/us-space-forces-space.xml",
    "NASA News Releases": "https://www.nasa.gov/news-release/feed/",
    "NASA Breaking News": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "DARPA News": "https://www.darpa.mil/rss",
    "NOAA Space Weather": "https://www.swpc.noaa.gov/news/rss.xml",

    # 🔬 Scientific & Commercial
    "Phys.org - Space": "https://phys.org/rss-feed/space-news/",
    "Space.com": "https://www.space.com/feeds/all",
    "Ars Technica - Space": "https://feeds.arstechnica.com/arstechnica/space",
    "NASA Tech Briefs": "https://www.techbriefs.com/rss-feeds",

    # 📰 Other Media
    "Defense News - Space": "https://www.defensenews.com/arc/outboundfeeds/rss/category/space/?outputType=xml"
}

# HOMEPAGE LINKS FOR SOURCES
source_links = {
    # 📰 Top 3 Media
    "SpaceNews": "https://spacenews.com",
    "Breaking Defense": "https://breakingdefense.com",
    "Air & Space Forces": "https://www.airandspaceforces.com",

    # 🛰️ Government & Military
    "USSF - Headlines": "https://www.spaceforce.mil/News",
    "USSF - Lines of Effort": "https://www.spaceforce.mil/About-Us/Lines-of-Effort",
    "USSF - Field News": "https://www.spaceforce.mil/News/Field-News",
    "USSF - US Space Forces": "https://www.spaceforce.mil/News/Space-Force-Units",
    "NASA News Releases": "https://www.nasa.gov/news-release/",
    "NASA Breaking News": "https://www.nasa.gov/news/releases/latest/index.html",
    "DARPA News": "https://www.darpa.mil/news",
    "NOAA Space Weather": "https://www.swpc.noaa.gov/news",

    # 🔬 Scientific & Commercial
    "Phys.org - Space": "https://phys.org/space-news/",
    "Space.com": "https://www.space.com/news",
    "Ars Technica - Space": "https://arstechnica.com/science/space/",
    "NASA Tech Briefs": "https://www.techbriefs.com/component/content/category/34-ntb/news/space",

    # 📰 Other Media
    "Defense News - Space": "https://www.defensenews.com/space/"
}

# CONVERT TIMESTAMP TO "Xh ago" or "Xm ago"
def get_age_string(timestamp):
    now = datetime.now(timezone.utc)
    delta = now - timestamp
    minutes = int(delta.total_seconds() / 60)
    if minutes < 1:
        return "just now"
    elif minutes < 60:
        return f"about {minutes}m ago"
    elif minutes < 1440:
        hours = minutes // 60
        return f"about {hours}h ago"
    else:
        days = minutes // 1440
        return f"about {days}d ago"

# ⏱️ Allow articles from the past 48 hours
cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
all_items = []

# PARSE EACH FEED
for source, url in feeds.items():
    parsed = feedparser.parse(url)
    for entry in parsed.entries:
        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        if not pub:
            continue
        timestamp = datetime.fromtimestamp(mktime(pub), tz=timezone.utc)
        if timestamp < cutoff:
            continue

        # IMAGE SCRAPING LOGIC (IMPROVED)
        image = ""

        # 1. Try media_content
        if "media_content" in entry and entry.media_content:
            image = entry.media_content[0].get("url", "")

        # 2. Try media_thumbnail
        elif "media_thumbnail" in entry and entry.media_thumbnail:
            image = entry.media_thumbnail[0].get("url", "")

        # 3. Try parsing first <img> from content
        elif "content" in entry and entry.content:
            html_content = entry.content[0].value
            match = re.search(r'<img[^>]+src="([^">]+)"', html_content)
            if match:
                image = match.group(1)

        # 4. Try parsing first <img> from description
        elif "description" in entry:
            match = re.search(r'<img[^>]+src="([^">]+)"', entry.description)
            if match:
                image = match.group(1)

        # 5. Try enclosure (used by some RSS feeds)
        elif "enclosures" in entry and entry.enclosures:
            image = entry.enclosures[0].get("url", "")

        # 6. Optionally filter out non-image files
        if image and not image.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            image = ""

        all_items.append({
            "source": source,
            "title": entry.title,
            "link": entry.link,
            "timestamp": timestamp,
            "image": image,
            "age": get_age_string(timestamp)
        })

# SORT + SELECT
latest = sorted(all_items, key=lambda x: x["timestamp"], reverse=True)
top_story = latest[0] if latest else None
remaining = latest[1:] if len(latest) > 1 else []

# ORGANIZE BY SOURCE
sources = {}
for item in remaining:
    sources.setdefault(item["source"], []).append(item)

# 🔁 Fallback if no top image
fallback_image = "images/HeadlineLogo.png"
image_url = top_story["image"].strip() if top_story["image"] else fallback_image

# ⏱️ Recent class = < 2 hours
is_recent = (datetime.now(timezone.utc) - top_story["timestamp"]).total_seconds() < 7200
top_class = "recent" if is_recent else ""

# 📌 Top Story Block
top_html = f'''
<div class="top-story {top_class}">
  <a href="{top_story["link"]}" target="_blank">
    <img src="{image_url}" alt="Top image" style="width: 100%; max-height: 300px; object-fit: cover;">
  </a>
  <div style="margin-top: 0.5rem;">
    <a href="{top_story["link"]}" target="_blank" style="text-decoration: none;">
      {top_story["title"]}
    </a>
  </div>
  <div class="source">{top_story["source"]} – {top_story["age"]}</div>
</div>
'''

# 📚 Section Columns
sections = ['<div class="columns">']
for source in feeds.keys():  # 🔄 This guarantees order from the feeds dictionary
    if source in sources:
        source_url = source_links.get(source, "#")
        section_html = f'<div class="column"><div class="section"><h2><a href="{source_url}" target="_blank">{source}</a></h2>'
        for a in sources[source][:5]:  # Still limited to 5 articles per source
            is_recent = (datetime.now(timezone.utc) - a["timestamp"]).total_seconds() < 7200
            recent_class = "recent" if is_recent else ""
            section_html += f'''
            <div class="headline {recent_class}">
              <a href="{a["link"]}" target="_blank">{a["title"]}</a>
              <span>({a["age"]})</span>
            </div>
            '''
        section_html += '</div></div>'
        sections.append(section_html)
sections.append('</div>')

# 🔧 Inject into index.html
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

start = html.find("<!-- START HEADLINES -->")
end = html.find("<!-- END HEADLINES -->")

if start != -1 and end != -1:
    new_content = '<!-- START HEADLINES -->\n' + top_html + "\n".join(sections) + '\n<!-- END HEADLINES -->'
    updated_html = html[:start] + new_content + html[end + len("<!-- END HEADLINES -->"):]
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(updated_html)
    print("✅ Headlines updated successfully.")
else:
    print("❌ Injection markers not found in index.html.")
