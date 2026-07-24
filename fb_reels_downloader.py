"""
Facebook Reels / Video URL Scraper + Downloader
-------------------------------------------------
1. Launches Chrome with a persistent profile (so you only log in once).
2. Waits for you to log in manually — blocks until you press Enter.
3. Opens the target page and scrolls until no new content loads.
4. Collects, cleans, and de-duplicates reel/video URLs -> urls.txt.
5. Exports your logged-in session's cookies -> cookies.txt (Netscape
   format) so yt-dlp can authenticate as you, no browser extension needed.
6. Runs yt-dlp against urls.txt to download everything.
"""

import time
import subprocess
from urllib.parse import urlparse, parse_qs, unquote

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


# ----------------------------
# Config
# ----------------------------

PAGE_URL = "https://www.facebook.com/bssjauharcampus/reels"
PROFILE_DIR = r"C:\selenium_profile"

URLS_FILE = "D:/Scraper/urls.txt"
COOKIES_FILE = "cookies.txt"
DOWNLOAD_ARCHIVE = "downloaded.txt"

MAX_SCROLLS = 3000
SCROLL_PAUSE = 5        # seconds to wait after each scroll for content to load
MAX_STALE_ROUNDS = 10    # consecutive no-growth scrolls before we assume we're done


# ----------------------------
# Chrome setup
# ----------------------------

def build_driver():
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    print("Chrome launched")
    return driver


# ----------------------------
# Scrolling
# ----------------------------

# Facebook often renders reels/media grids inside a nested scrollable div
# rather than the page body, so `window.scrollTo` alone can silently do
# nothing. This finds whichever element is actually scrollable and scrolls
# that instead, falling back to the window. The helper is cached on
# `window` so repeated calls stay cheap and consistent.

SCROLL_JS = """
if (!window.__findScrollableContainer) {
    window.__findScrollableContainer = function() {
        const candidates = document.querySelectorAll('div, section, main');
        let best = null;
        let bestDiff = 0;
        for (const el of candidates) {
            const style = getComputedStyle(el);
            const diff = el.scrollHeight - el.clientHeight;
            if ((style.overflowY === 'auto' || style.overflowY === 'scroll') && diff > bestDiff + 50) {
                best = el;
                bestDiff = diff;
            }
        }
        return best;
    };
}
const container = window.__findScrollableContainer();
if (container) {
    container.scrollTop = container.scrollHeight;
} else {
    window.scrollTo(0, document.body.scrollHeight);
}
"""

MEASURE_HEIGHT_JS = """
const container = window.__findScrollableContainer ? window.__findScrollableContainer() : null;
return container ? container.scrollHeight : document.body.scrollHeight;
"""


def extract_video_url(href):
    """Unwrap Facebook redirect links and normalize reel/video/watch URLs.
    Returns None if href isn't a reel/video/watch link."""

    parsed = urlparse(href)

    # Unwrap l.facebook.com/l.php?u=... tracking redirect wrapper
    if parsed.netloc == "l.facebook.com" and parsed.path == "/l.php":
        target = parse_qs(parsed.query).get("u")
        if target:
            href = unquote(target[0])
            parsed = urlparse(href)

    if "/reel/" in parsed.path or "/videos/" in parsed.path:
        return f"https://www.facebook.com{parsed.path}"

    if "/watch" in parsed.path:
        v = parse_qs(parsed.query).get("v")
        if v:
            return f"https://www.facebook.com/watch/?v={v[0]}"

    return None


def scroll_and_collect(driver):
    links = set()
    last_height = None
    stale_rounds = 0

    for i in range(1, MAX_SCROLLS + 1):
        print(f"\nScroll {i}/{MAX_SCROLLS}")

        driver.execute_script(SCROLL_JS)
        time.sleep(SCROLL_PAUSE)
        new_height = driver.execute_script(MEASURE_HEIGHT_JS)

        elements = driver.find_elements(By.TAG_NAME, "a")
        print(f"  Found {len(elements)} anchors on page")

        before = len(links)
        for el in elements:
            try:
                href = el.get_attribute("href")
            except StaleElementReferenceException:
                continue

            if not href:
                continue

            cleaned = extract_video_url(href)
            if cleaned:
                links.add(cleaned)

        print(f"  Collected {len(links)} unique links (+{len(links) - before} new)")

        if last_height is not None and new_height == last_height:
            stale_rounds += 1
            print(f"  No new content ({stale_rounds}/{MAX_STALE_ROUNDS})")
            if stale_rounds >= MAX_STALE_ROUNDS:
                print("Reached end of page")
                break
        else:
            stale_rounds = 0

        last_height = new_height

    return links


# ----------------------------
# Cookie export (for yt-dlp)
# ----------------------------

def export_cookies_netscape(driver, filename=COOKIES_FILE):
    """Writes the logged-in session's cookies to a Netscape-format cookie
    file so yt-dlp can download as you — no separate browser-extension
    export needed. Treat this file like a password: anyone with it can
    use your session."""

    cookies = driver.get_cookies()
    lines = ["# Netscape HTTP Cookie File", ""]

    for c in cookies:
        domain = c.get("domain", "")
        flag = "TRUE" if domain.startswith(".") else "FALSE"
        path = c.get("path", "/")
        secure = "TRUE" if c.get("secure") else "FALSE"
        expiry = (
            str(int(c["expiry"]))
            if "expiry" in c
            else str(int(time.time()) + 60 * 60 * 24 * 30)
        )
        name = c.get("name", "")
        value = c.get("value", "")
        lines.append("\t".join([domain, flag, path, secure, expiry, name, value]))

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Saved {len(cookies)} cookies to {filename}")


# ----------------------------
# Download
# ----------------------------

def download_videos(user_agent=None):
    command = [
        "python", "-m", "yt_dlp",
        "--cookies", COOKIES_FILE,
        "-a", URLS_FILE,
        "--ignore-errors",
        "--download-archive", DOWNLOAD_ARCHIVE,
        "-o", "downloads/%(uploader)s/%(upload_date)s-%(title)s.%(ext)s",
    ]
    if user_agent:
        command += ["--user-agent", user_agent]

    subprocess.run(command)


# ----------------------------
# Main
# ----------------------------

def main():
    driver = build_driver()
    links = set()
    user_agent = None

    try:
        driver.get("https://facebook.com")
        print("Log in manually in the opened Chrome window, then press Enter here to continue...")

        driver.get(PAGE_URL)
        print("Opened target page")

        try:
            WebDriverWait(driver, 30).until(
                lambda d: len(d.find_elements(By.TAG_NAME, "a")) > 5
            )
        except TimeoutException:
            print("Warning: page didn't show much content after 30s — continuing anyway.")

        links = scroll_and_collect(driver)

        with open(URLS_FILE, "w", encoding="utf-8") as f:
            for url in links:
                f.write(url + "\n")
        print(f"\nSaved {len(links)} URLs to {URLS_FILE}")

        export_cookies_netscape(driver)
        user_agent = driver.execute_script("return navigator.userAgent;")

    finally:
        driver.quit()

    if not links:
        print("No video URLs found — skipping download.")
        return

    print("\nStarting downloads...")
    download_videos(user_agent)


if __name__ == "__main__":
    main()