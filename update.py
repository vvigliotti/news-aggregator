import feedparser
import re
from datetime import datetime, timezone, timedelta
from time import mktime
from random import randint
import os
import html as html_lib
from google import genai

# NEW: stdlib for API call (no YAML changes needed)
import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode

# FEED SOURCES
feeds = {
    # 📰 Top 3 Media
    "SpaceNews": "https://spacenews.com/feed/",
    "Breaking Defense": "https://breakingdefense.com/feed/",
    "Air & Space Forces": "https://www.airandspaceforces.com/feed/",

    # 🛰️ Government & Military
    "USSF – Headlines": "https://www.spaceforce.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1060&Category=23812&isdashboardselected=0&max=20",
    "USSF – Field News": "https://www.spaceforce.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1060&Category=23813&isdashboardselected=0&max=20",
    "USSF – Units":     "https://www.spaceforce.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1060&Category=23814&isdashboardselected=0&max=20",
    "NASA News Releases": "https://www.nasa.gov/news-release/feed/",
    "NASA Breaking News": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "DARPA News": "https://www.darpa.mil/rss",
    "NOAA Space Weather": "https://www.swpc.noaa.gov/news/rss.xml",

    # 🔬 Scientific & Commercial
    "Phys.org - Space": "https://phys.org/rss-feed/space-news/",
    "Space.com": "https://www.space.com/feeds/all",
    "Ars Technica – Space": "https://feeds.arstechnica.com/arstechnica/space",
    "NASA Tech Briefs": "https://www.techbriefs.com/rss-feeds",

    # 📰 Other Media
    "Defense News - Space": "https://www.defensenews.com/arc/outboundfeeds/rss/category/space/?outputType=xml",
    "NASA Watch": "https://nasawatch.com/feed/",
}

# HOMEPAGE LINKS FOR SOURCES
source_links = {
    # 📰 Top 3 Media
    "SpaceNews": "https://spacenews.com",
    "Breaking Defense": "https://breakingdefense.com",
    "Air & Space Forces": "https://www.airandspaceforces.com",

    # 🛰️ Government & Military
    "USSF – Headlines": "https://www.spaceforce.mil/News",
    "USSF – Field News": "https://www.spaceforce.mil/News/Field-News",
    "USSF – Units": "https://www.spaceforce.mil/News/Space-Force-Units",
    "NASA News Releases": "https://www.nasa.gov/news-release/",
    "NASA Breaking News": "https://www.nasa.gov/news/releases/latest/index.html",
    "DARPA News": "https://www.darpa.mil/news",
    "NOAA Space Weather": "https://www.swpc.noaa.gov/news",

    # 🔬 Scientific & Commercial
    "Phys.org - Space": "https://phys.org/space-news/",
    "Space.com": "https://www.space.com/news",
    "Ars Technica – Space": "https://arstechnica.com/science/space/",
    "NASA Tech Briefs": "https://www.techbriefs.com/component/content/category/34-ntb/news/space",

    # 📰 Other Media
    "Defense News - Space": "https://www.defensenews.com/space/",
    "NASA Watch": "https://nasawatch.com/",
}

# ---------- TEMPLATED IMAGE SELECTION (NO SCRAPING) ----------
IMAGE_DIR = "images/"
IMAGE_MAP = {
    "default": IMAGE_DIR + "HeadlineLogo.png",
    "breaking": IMAGE_DIR + "breaking.png",
    "government": IMAGE_DIR + "government.png",
    "launch": IMAGE_DIR + "launch.png",
    "satellite": IMAGE_DIR + "satellite.png",
    "science": IMAGE_DIR + "science.png",
}

# keyword sets (case-insensitive). order = priority
PATTERNS = {
    "breaking": re.compile(r"\b(breaking|urgent|alert)\b", re.I),
    "government": re.compile(
        r"\b(ussf|space\s*force|air\s*force|secretary\s+of|dod|department\s+of\s+defense|government|military|guardian[s]?)\b",
        re.I,
    ),
    "launch": re.compile(r"\b(launch|launched|rocket|spacex|blue\s*origin|booster|falcon|starship)\b", re.I),
    "satellite": re.compile(r"\b(satellite|payload|constellation|satcom|earth\s*observation)\b", re.I),
    "science": re.compile(r"\b(science|scientist|discovered|discovery|nasa|research|telescope|observatory)\b", re.I),
}

# source “hints” if the title is ambiguous
SOURCE_HINTS = {
    "government": re.compile(r"(USSF|Space Force|Air & Space Forces|Defense News|Breaking Defense|DARPA)", re.I),
    "science": re.compile(r"(NASA|Phys\.org|Tech Briefs|Ars Technica)", re.I),
}

def pick_image_for(title: str, source: str) -> str:
    t = title or ""
    s = source or ""
    # 1) keyword priority
    for key in ["breaking", "government", "launch", "satellite", "science"]:
        if PATTERNS[key].search(t):
            return IMAGE_MAP[key]
    # 2) source hints
    for key in ["government", "science"]:
        if SOURCE_HINTS[key].search(source):
            return IMAGE_MAP[key]
    # 3) default
    return IMAGE_MAP["default"]
# -------------------------------------------------------------

# NEW: Upcoming Launches fetcher (Launch Library 2 – The Space Devs)
def fetch_upcoming_launches(limit=8, days_ahead=7):
    base = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/"
    params = {
        "limit": limit,
        "hide_recent_previous": "true",
        "ordering": "window_start",
    }
    url = base + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "SpaceHeadlinesBot/1.0"})
    with urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days_ahead)

    launches = []
    for L in data.get("results", []):
        start = L.get("window_start")
        dt = None
        if start:
            try:
                dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            except Exception:
                dt = None
        if not dt or dt > cutoff:
            continue

        name = L.get("name") or "TBD"
        when = dt.strftime("%b %d, %Y %H:%M UTC") if dt else "TBD"
        provider = (L.get("launch_service_provider") or {}).get("name") or "—"
        pad = ((L.get("pad") or {}).get("name") or "—")
        loc = ((L.get("pad") or {}).get("location") or {}).get("name") or ""

        launches.append({
            "name": name,
            "when": when,
            "provider": provider,
            "pad": pad,
            "loc": loc
        })

    return launches[:limit]

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

        all_items.append({
            "source": source,
            "title": entry.title,
            "link": entry.link,
            "timestamp": timestamp,
            # 👇 image chosen purely from keywords/source (no scraping)
            "image": pick_image_for(entry.title, source),
            "age": get_age_string(timestamp)
        })

# SORT + SELECT
latest = sorted(all_items, key=lambda x: x["timestamp"], reverse=True)
top_story = latest[0] if latest else None
remaining = latest[1:] if len(latest) > 1 else []

# ============================================================
# AI DAILY SUMMARY — GEMINI
# Generates at most one new summary per UTC calendar day.
# If Gemini fails, headlines continue updating normally.
# ============================================================

SUMMARY_CACHE_FILE = "daily_summary.json"
SUMMARY_MODEL = "gemini-3.6-flash"

def load_summary_cache():
    """Load the most recently saved daily summary."""
    try:
        with open(SUMMARY_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    return {}


def save_summary_cache(summary_date, summary_text, article_count):
    """Overwrite the same cache file instead of creating daily files."""
    data = {
        "date": summary_date,
        "summary": summary_text,
        "article_count": article_count
    }

    temporary_file = SUMMARY_CACHE_FILE + ".tmp"

    with open(temporary_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    os.replace(temporary_file, SUMMARY_CACHE_FILE)


def generate_daily_summary(items):
    """Generate a briefing using the most recent collected headlines."""
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    # Limit the request so it stays small, fast, and inexpensive.
    selected_items = items[:80]

    headline_lines = []

    for number, item in enumerate(selected_items, start=1):
        headline_lines.append(
            f'{number}. [{item["source"]}] {item["title"]}'
        )

    headline_text = "\n".join(headline_lines)

    prompt = f"""
You are the editor of SpaceHeadlines.com.

Using only the supplied headlines, write a concise daily space-news
briefing for a general but informed audience.

Requirements:

- Write 1 paragraph.
- Begin with the most consequential development.
- Cover military, civil government, commercial, launch, science,
  and international developments when the headlines support them.
- Combine duplicate or closely related stories.
- Do not invent facts or details beyond the headlines.
- Do not include URLs.
- Do not use bullet points.
- Do not use markdown headings.
- Do not mention being an AI.
- Use neutral, professional news language.
- End with one short sentence about what readers should watch next.
- Keep the entire briefing below 500 words.

Collected headlines:

{headline_text}
""".strip()

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=SUMMARY_MODEL,
        contents=prompt
    )

    summary_text = (response.text or "").strip()

    if not summary_text:
        raise RuntimeError("Gemini returned an empty summary.")

    return summary_text, len(selected_items)


def build_summary_html(summary_text, summary_date):
    """Safely turn the summary text into an HTML section."""
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", summary_text)
        if paragraph.strip()
    ]

    paragraphs_html = "\n".join(
        f"<p>{html_lib.escape(paragraph)}</p>"
        for paragraph in paragraphs
    )

    try:
        displayed_date = datetime.strptime(
            summary_date,
            "%Y-%m-%d"
        ).strftime("%B %d, %Y")
    except ValueError:
        displayed_date = summary_date

    return f'''
<section style="
    max-width:900px;
    margin:30px auto;
    padding:24px;
    background:#f8f9fb;
    border:1px solid #d9e2ec;
    border-left:6px solid #1f4e79;
    border-radius:8px;
    text-align:center;
">

<div style="
    font-size:12px;
    font-weight:bold;
    color:#666;
    letter-spacing:2px;
">
AI DAILY BRIEFING
</div>

<h2 style="margin:8px 0 5px 0; color:#222;">
Today in Space
</h2>

<div style="
    color:#777;
    margin-bottom:18px;
">
{displayed_date}
</div>

<div style="
    text-align:left;
    line-height:1.7;
    font-size:17px;
    color:#222;
">
{paragraphs_html}
</div>

<hr style="margin:20px 0;">

<div style="
    font-size:12px;
    color:#777;
">
AI-generated summary of today's collected headlines. Read the original articles below for complete reporting.
</div>

</section>
'''


today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
summary_cache = load_summary_cache()

cached_date = summary_cache.get("date")
cached_summary = summary_cache.get("summary", "").strip()

# Gemini is called only when today's summary is not already cached.
if cached_date != today_utc and latest:
    try:
        new_summary, summarized_article_count = generate_daily_summary(latest)

        save_summary_cache(
            today_utc,
            new_summary,
            summarized_article_count
        )

        cached_date = today_utc
        cached_summary = new_summary

        print(
            f"✅ Gemini summary generated from "
            f"{summarized_article_count} headlines."
        )

    except Exception as error:
        # This does not stop the normal headline update.
        print(f"⚠️ Gemini summary skipped: {error}")

elif cached_date == today_utc:
    print("ℹ️ Today's Gemini summary already exists. Reusing it.")


daily_summary_html = ""

if cached_summary:
    daily_summary_html = build_summary_html(
        cached_summary,
        cached_date
    )

# ============================================================
# END AI DAILY SUMMARY
# ============================================================

# ORGANIZE BY SOURCE
sources = {}
for item in remaining:
    sources.setdefault(item["source"], []).append(item)

# 🔁 Top image (already selected by picker)
fallback_image = IMAGE_MAP["default"]
image_url = top_story["image"] if (top_story and top_story["image"]) else fallback_image

# ⏱️ Recent class = < 2 hours
is_recent = (datetime.now(timezone.utc) - top_story["timestamp"]).total_seconds() < 7200 if top_story else False
top_class = "recent" if is_recent else ""

# 📌 Top Story Block
top_html = ""
if top_story:
    top_html = f'''
<div class="top-story {top_class}" style="text-align: center;">
  <a href="{top_story["link"]}" target="_blank" style="display: inline-block;">
    <img src="{image_url}" alt="Top image"
         style="display: block; max-width: 720px; width: 100%; height: auto; max-height: 300px; object-fit: cover; border-radius: 6px;">
  </a>
  <div style="margin-top: 0.5rem;">
    <a href="{top_story["link"]}" target="_blank" style="text-decoration: none;">
      {top_story["title"]}
    </a>
  </div>
  <div class="source">{top_story["source"]} – {top_story["age"]}</div>
</div>
'''

# NEW: fetch upcoming launches (safe fail)
try:
    upcoming_launches = fetch_upcoming_launches(limit=8, days_ahead=7)
except Exception:
    upcoming_launches = []

# 📚 Section Columns
sections = ['<div class="columns">']
for source in feeds.keys():
    if source in sources:
        source_url = source_links.get(source, "#")
        section_html = f'<div class="column"><div class="section"><h2><a href="{source_url}" target="_blank">{source}</a></h2>'
        for a in sources[source][:8]:
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

# NEW: Append right-most column for Upcoming Launches
if upcoming_launches:
    rows = []
    for l in upcoming_launches:
        rows.append(f'''
        <div class="headline">
          <strong>{l["when"]}</strong> — {l["name"]}
          <div class="source" style="margin-top:2px;">{l["provider"]} • {l["pad"]}{(" — " + l["loc"]) if l["loc"] else ""}</div>
        </div>
        ''')
    credit = '<div class="source" style="margin-top:6px;">Data: <a href="https://thespacedevs.com/" target="_blank">Launch Library 2 (The Space Devs)</a></div>'
    launches_column_html = f'''
    <div class="column">
      <div class="section">
        <h2><a href="https://thespacedevs.com/" target="_blank">Upcoming Launches (next 7 days)</a></h2>
        {''.join(rows)}
        {credit}
      </div>
    </div>
    '''
    sections.append(launches_column_html)

sections.append('</div>')

# 🔧 Inject into index.html
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# --- Safe SEO title + description insert (invisible to visitors) ---

import re

# 1️⃣ Set tab title
title_text = "Space Headlines: Breaking Space News, NASA, Space Force & Launches"

# Ensure <head> exists
if "</head>" not in html:
    html = "<head>\n</head>\n" + html

# Replace existing <title> or insert new one before </head>
if re.search(r"<title\b[^>]*>.*?</title>", html, flags=re.I | re.S):
    html = re.sub(
        r"<title\b[^>]*>.*?</title>",
        f"<title>{title_text}</title>",
        html,
        count=1,
        flags=re.I | re.S
    )
else:
    html = html.replace("</head>", f"<title>{title_text}</title>\n</head>", 1)

# 2️⃣ Add meta description if missing
meta_desc = (
    "Space Headlines delivers real-time space news, NASA and Space Force updates, rocket launches, satellites, "
    "astronomy, and commercial space stories — refreshed every 5 minutes."
)
if '<meta name="description"' not in html:
    html = html.replace(
        "</head>",
        f'<meta name="description" content="{meta_desc}">\n</head>',
        1
    )

# --- end SEO insert ---


# ---------------- SAFE HEAD + GA + SEO (NON-DESTRUCTIVE) ----------------
def _ensure_head(doc: str) -> str:
    """Guarantee a <head>...</head> exists so inserts never leak into visible body."""
    if "</head>" in doc:
        return doc
    # If a <head ...> exists but not closed, close it before <body> or at end
    if "<head" in doc and "</head>" not in doc:
        body_i = doc.find("<body")
        return (doc[:body_i] + "</head>\n" + doc[body_i:]) if body_i != -1 else (doc + "\n</head>")
    # No head at all: create it before <body> or prepend
    body_i = doc.find("<body")
    head_block = "<head>\n</head>\n"
    return (doc[:body_i] + head_block + doc[body_i:]) if body_i != -1 else (head_block + doc)

def _has_tag(doc: str, pattern: str) -> bool:
    return re.search(pattern, doc, flags=re.I | re.S) is not None

def _insert_before_head_close(doc: str, block: str) -> str:
    return doc.replace("</head>", block + "\n</head>", 1)

html = _ensure_head(html)

# --- GA (add once, head-only) ---
GA_ID = "G-F0ZJXSLFMH"
ga_snippet = f"""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_ID}');
</script>
"""
if GA_ID not in html:
    html = _insert_before_head_close(html, ga_snippet)
# --- end GA ---

# --- SEO (non-destructive: only add if missing; never duplicates) ---
def ensure_seo_non_destructive(doc: str) -> str:
    site_url = "https://spaceheadlines.com/"
    title_text = "Space Headlines: Breaking Space News, NASA, Space Force & Launches"
    description = (
        "Space news aggregator with upcoming launches, Space Force & NASA updates, "
        "rockets, satellites, astronomy, commercial space—refreshed every 5 minutes."
    )[:158]
    og_image = site_url.rstrip("/") + "/images/HeadlineLogo.png"

    # 1) title
    if not _has_tag(doc, r"<title\b[^>]*>.*?</title>"):
        doc = _insert_before_head_close(doc, f"<title>{title_text}</title>")

    # 2) meta description
    if not _has_tag(doc, r'<meta\s+name=["\']description["\']'):
        doc = _insert_before_head_close(doc, f'<meta name="description" content="{description}" />')

    # 2.5) google site verification
    if not _has_tag(doc, r'<meta\s+name=["\']google-site-verification["\']'):
        doc = _insert_before_head_close(
            doc,
            '<meta name="google-site-verification" content="p8rg-XOJM-gk3dIX2qP7DyD_ouNpPLKp933vq11RdME" />'
        )
    
    # 3) canonical
    if not _has_tag(doc, r'<link\s+rel=["\']canonical["\']'):
        doc = _insert_before_head_close(doc, f'<link rel="canonical" href="{site_url}" />')

    # 4) robots
    if not _has_tag(doc, r'<meta\s+name=["\']robots["\']'):
        doc = _insert_before_head_close(doc, '<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large,max-video-preview:-1" />')

    # 5) OG/Twitter (add block once if neither present)
    has_og = _has_tag(doc, r'<meta\s+property=["\']og:')
    has_tw = _has_tag(doc, r'<meta\s+name=["\']twitter:')
    if not (has_og or has_tw):
        og_tw_block = "\n".join([
            '<meta property="og:type" content="website" />',
            '<meta property="og:site_name" content="Space Headlines" />',
            f'<meta property="og:title" content="{title_text}" />',
            f'<meta property="og:description" content="{description}" />',
            f'<meta property="og:url" content="{site_url}" />',
            f'<meta property="og:image" content="{og_image}" />',
            '<meta name="twitter:card" content="summary_large_image" />',
            f'<meta name="twitter:title" content="{title_text}" />',
            f'<meta name="twitter:description" content="{description}" />',
            f'<meta name="twitter:image" content="{og_image}" />',
        ])
        doc = _insert_before_head_close(doc, og_tw_block)

    # 6) JSON-LD (add once)
    if not _has_tag(doc, r'<script\s+type=["\']application/ld\+json["\']'):
        json_ld = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "Space Headlines",
            "alternateName": ["SpaceHeadlines", "spaceheadlines.com"],
            "url": site_url,
            "potentialAction": {
                "@type": "SearchAction",
                "target": site_url + "?q={search_term_string}",
                "query-input": "required name=search_term_string"
            }
        }
        jsonld_tag = '<script type="application/ld+json">' + json.dumps(json_ld, ensure_ascii=False) + "</script>"
        doc = _insert_before_head_close(doc, jsonld_tag)

    return doc
html = ensure_seo_non_destructive(html)
# ---------------- END SAFE HEAD + GA + SEO --------------------

start = html.find("<!-- START HEADLINES -->")
end = html.find("<!-- END HEADLINES -->")

if start != -1 and end != -1:
    new_content = '<!-- START HEADLINES -->\n' + daily_summary_html + '\n' + top_html + "\n".join(sections) + '\n<!-- END HEADLINES -->'    
    updated_html = html[:start] + new_content + html[end + len("<!-- END HEADLINES -->"):]
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(updated_html)
    print("✅ Headlines updated successfully.")
else:
    # At least persist head updates so SEO/GA are kept even if markers are missing
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("❗ Injection markers not found. Wrote head (SEO/GA) updates only.")
