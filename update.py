import datetime
from pathlib import Path

# Define the columns and articles (REPLACE WITH YOUR LIVE HEADLINE FETCHING)
columns = {
    "media": {
        "Air & Space Forces Magazine": [
            {"title": "Space Force Looks to Commercial Tech", "url": "#", "time": "14m ago", "breaking": True},
            {"title": "Multi-Orbit SATCOM Resilience", "url": "#", "time": "3h ago"},
        ],
        "Breaking Defense": [
            {"title": "New Space-Based Interceptor Role", "url": "#", "time": "12m ago", "breaking": True},
            {"title": "Jam-Resistant SATCOM Awards", "url": "#", "time": "1h ago"},
        ],
    },
    "gov": {
        "USSF": [
            {"title": "NATO Follows USSF", "url": "#", "time": "27m ago"},
        ],
    },
    "intl": {
        "ESA – European Space Agency": [
            {"title": "Webb Traces Planetary Nebula", "url": "#", "time": "6h ago"},
        ],
        "Phys.org – Space": [
            {"title": "ISRO Lifts Off for Earth Surface Study", "url": "#", "time": "3h ago"},
        ],
    }
}

# Select the top breaking headline
breaking_headline = None
for section in columns.values():
    for source, articles in section.items():
        for article in articles:
            if article.get("breaking"):
                breaking_headline = article
                break
        if breaking_headline:
            break
    if breaking_headline:
        break

def build_column_html(column_data):
    html = ""
    for source, articles in column_data.items():
        html += f"<h3><a href='#' target='_blank'>{source}</a></h3>\n<hr>\n"
        for article in articles:
            title = article["title"]
            url = article["url"]
            time = article["time"]
            is_breaking = 'breaking' if article.get("breaking") else ''
            html += f"<div class='headline'><a href='{url}' class='{is_breaking}'>{title}</a><br><span class='meta'>{source} · {time}</span></div>\n"
    return html

# Read base HTML
index_template = Path("index.html").read_text()

# Inject content
final_html = index_template
final_html = final_html.replace(
    "Loading breaking headline...",
    f"<a href='{breaking_headline['url']}' class='breaking'>{breaking_headline['title']}</a>" if breaking_headline else "No breaking headline."
)
final_html = final_html.replace("<!-- Headlines will go here -->", build_column_html(columns["media"]), 1)
final_html = final_html.replace("<!-- Headlines will go here -->", build_column_html(columns["gov"]), 1)
final_html = final_html.replace("<!-- Headlines will go here -->", build_column_html(columns["intl"]), 1)

# Write to file
Path("index.html").write_text(final_html)
