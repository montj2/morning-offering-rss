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
    main = soup.find("main") or soup.find("article") or soup.body or soup
    keep_tags = ("h1","h2","h3","h4","p","blockquote","ul","ol","li","a","em","strong","figure","figcaption","img","hr")
    frag = []
    for el in main.find_all(keep_tags, recursive=True):
        text = el.get_text(" ", strip=True).lower()
        if any(k in text for k in ["recommended products", "subscribe", "follow us", "promotions"]):
            continue
        for a in el.find_all("a", href=True):
            if a["href"].startswith("/"):
                a["href"] = BASE_URL + a["href"]
        for img in el.find_all("img", src=True):
            if img["src"].startswith("/"):
                img["src"] = BASE_URL + img["src"]
        frag.append(str(el))
    if not frag:
        return f"<p>See original page:</p><p><a href='{html.escape(url)}'>{html.escape(url)}</a></p>"
    return "\n".join(frag).strip()

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
