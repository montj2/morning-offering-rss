import os, re, html, hashlib, datetime as dt, argparse
import pytz, requests
from bs4 import BeautifulSoup

# --- Settings ---
TZ = "America/New_York"
BASE_URL = "https://www.morningoffering.com"
DAILY_PATH_FMT = "/offering/{mm}-{dd}/"
FEED_TITLE = "Morning Offering (Unofficial RSS)"
FEED_LINK = f"{BASE_URL}/offering/"
FEED_DESCRIPTION = "Unofficial, personal-use RSS feed created from morningoffering.com daily page."
FEED_FILE = "feed.xml"
MAX_ITEMS = 60
USER_AGENT = "Personal-RSS-Generator/1.1 (+https://github.com/your-username/morning-offering-rss)"

def today_et():
    return dt.datetime.now(pytz.timezone(TZ))

def build_daily_url(d):
    return BASE_URL + DAILY_PATH_FMT.format(mm=f"{d.month:02d}", dd=f"{d.day:02d}")

def fetch_html(url):
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.text

def extract_main_content(html_text, url):
    soup = BeautifulSoup(html_text, "html.parser")
    content_parts = []
    
    # 1. The Morning Offering prayer
    offering_text = soup.find(string=lambda text: text and "O Jesus, through the Immaculate Heart of Mary" in text)
    if offering_text:
        content_parts.append("<h2>The Morning Offering</h2>")
        content_parts.append(f"<p>{offering_text.strip()}</p>")
    
    # 2. Saint quote (#saint-quote)
    saint_quote = soup.find(id='saint-quote')
    if saint_quote:
        content_parts.append("<h2>Saint Quote</h2>")
        # Clean up promotional content within the section
        clean_quote = clean_section(saint_quote)
        content_parts.append(str(clean_quote))
    
    # 3. Today's Meditation (#meditation)
    meditation = soup.find(id='meditation')
    if meditation:
        clean_meditation = clean_section(meditation)
        content_parts.append(str(clean_meditation))
    
    # 4. Daily Verse (#daily-verse)
    daily_verse = soup.find(id='daily-verse')
    if daily_verse:
        clean_verse = clean_section(daily_verse)
        content_parts.append(str(clean_verse))
    
    # 5. Saint of the day (.daily-saint)
    daily_saint = soup.select('.daily-saint')
    if daily_saint:
        content_parts.append("<h2>Saint of the Day</h2>")
        
        # Saint image
        saint_img = soup.select('.daily-saint > div:nth-child(1) > img:nth-child(1)')
        if saint_img:
            content_parts.append(str(saint_img[0]))
        
        # Saint text (clean up promotional content)
        saint_text = soup.select('.daily-saint > div:nth-child(2)')
        if saint_text:
            clean_saint_text = clean_section(saint_text[0])
            content_parts.append(str(clean_saint_text))
    
    # 6. Devotion of the month (.order-lg-1 for text, .order-lg-2 for image)
    devotion_text = soup.select('.order-lg-1')
    devotion_img = soup.select('.order-lg-2')
    if devotion_text:
        content_parts.append("<h2>Devotion of the Month</h2>")
        clean_devotion = clean_section(devotion_text[0])
        content_parts.append(str(clean_devotion))
        if devotion_img:
            content_parts.append(str(devotion_img[0]))
    
    # 7. Daily Prayers (.order-sm-1)
    daily_prayers = soup.select('.order-sm-1')
    if daily_prayers:
        clean_prayers = clean_section(daily_prayers[0])
        content_parts.append(str(clean_prayers))
    
    # Combine all content
    if content_parts:
        final_html = '\n'.join(content_parts)
        
        # Clean up and fix URLs
        final_soup = BeautifulSoup(final_html, 'html.parser')
        
        # Fix relative URLs
        for a in final_soup.find_all("a", href=True):
            if a["href"].startswith("/"):
                a["href"] = BASE_URL + a["href"]
        
        for img in final_soup.find_all("img", src=True):
            if img["src"].startswith("/"):
                img["src"] = BASE_URL + img["src"]
        
        return str(final_soup)
    
    # Fallback if no content found
    return f"<p>See original page:</p><p><a href='{html.escape(url)}'>{html.escape(url)}</a></p>"

def clean_section(element):
    """Remove promotional content from a section while preserving the main content"""
    if not element:
        return element
    
    # Make a copy to avoid modifying the original
    clean_el = BeautifulSoup(str(element), 'html.parser')
    
    # Remove promotional subsections
    for unwanted in clean_el.select('.recommended-reads, .excerpt-from'):
        unwanted.decompose()
    
    # Remove promotional buttons and links
    for button in clean_el.find_all(['a'], class_=['button']):
        button.decompose()
    
    # Remove promotional links with specific patterns
    for link in clean_el.find_all('a'):
        href = link.get('href', '').lower()
        text = link.get_text(" ", strip=True).lower()
        if any(bad in href for bad in ['catholiccompany', 'referral']) or \
           any(bad in text for bad in ['≻', 'recommended for you', 'find a devotional']):
            link.decompose()
    
    # Remove promotional list items
    for li in clean_el.find_all('li'):
        text = li.get_text(" ", strip=True).lower()
        if '≻' in text or 'recommended for you' in text:
            li.decompose()
    
    # Remove promotional divs and sections
    for div in clean_el.find_all(['div', 'ul']):
        if not div.get_text(strip=True):  # Empty after cleaning
            div.decompose()
    
    return clean_el.find() if clean_el.find() else element

def get_title(soup):
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    if soup.title and soup.title.get_text(strip=True):
        return soup.title.get_text(strip=True)
    return "Morning Offering"

def make_guid(url, date_str):
    return hashlib.sha1(f"{url}|{date_str}".encode("utf-8")).hexdigest()

def load_existing_items(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        xml = f.read()
    return re.findall(r"(<item>.*?</item>)", xml, flags=re.DOTALL)

def build_item_xml(title, link, description_html, pubdate_rfc822, guid):
    return f"""<item>
  <title>{html.escape(title)}</title>
  <link>{html.escape(link)}</link>
  <guid isPermaLink="false">{guid}</guid>
  <pubDate>{pubdate_rfc822}</pubDate>
  <description><![CDATA[
{description_html}
  ]]></description>
</item>
"""

def rfc822(dt_et):
    return dt_et.strftime("%a, %d %b %Y %H:%M:%S %z")

def write_feed(path, items_xml, last_build_dt):
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>{html.escape(FEED_TITLE)}</title>
  <link>{html.escape(FEED_LINK)}</link>
  <description>{html.escape(FEED_DESCRIPTION)}</description>
  <language>en-us</language>
  <lastBuildDate>{rfc822(last_build_dt)}</lastBuildDate>
  {''.join(items_xml)}
</channel>
</rss>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(feed)

def upsert_item(items, item_xml, guid, url):
    exists = any(guid in it or url in it for it in items)
    if not exists:
        items.insert(0, item_xml)
    return items

def build_one_day_items(d, items):
    url = build_daily_url(d)
    html_text = fetch_html(url)
    if html_text is None:
        # No page for that day (or not available yet); skip silently
        return items
    soup = BeautifulSoup(html_text, "html.parser")
    title = get_title(soup)
    description_html = extract_main_content(html_text, url)

    # Publish time: 6:00am ET for that day
    pub_dt = pytz.timezone(TZ).localize(dt.datetime(d.year, d.month, d.day, 6, 0, 0))
    guid = make_guid(url, d.strftime("%Y-%m-%d"))
    item_xml = build_item_xml(title, url, description_html, rfc822(pub_dt), guid)

    return upsert_item(items, item_xml, guid, url)

def main():
    parser = argparse.ArgumentParser(description="Generate or backfill Morning Offering RSS feed.")
    parser.add_argument("--days", type=int, default=1, help="Number of days to fetch (1=today only). Includes today and goes backward.")
    args = parser.parse_args()

    now = today_et()
    existing = load_existing_items(FEED_FILE)

    # Iterate from today backwards N-1 days
    for i in range(args.days):
        d = (now - dt.timedelta(days=i)).date()
        existing = build_one_day_items(d, existing)
        existing = existing[:MAX_ITEMS]

    write_feed(FEED_FILE, existing, now)

if __name__ == "__main__":
    main()
