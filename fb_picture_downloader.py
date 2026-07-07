from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import requests
import time
import os
import json

# PAGE_URL = "https://www.facebook.com/bssjauharcampus/photos"
PAGE_URL = "https://www.facebook.com/bssjkg2/photos"
LINKS_FILE = "photo_links.json"
DOWNLOADS = "downloadsAyesha"
### Photo_linkMain mei main campus ki pics k links hei

# ----------------------------
# Setup
# ----------------------------

options = webdriver.ChromeOptions()

# Separate Selenium profile
options.add_argument(r"--user-data-dir=C:\selenium_profile")

options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

print("Chrome launched")

# ----------------------------
# Login
# ----------------------------

driver.get("https://facebook.com")

print("Login manually")

# ----------------------------
# Open Photos Page
# ----------------------------

driver.get(PAGE_URL)

print("Opened photos page")

# ----------------------------
# Load previously collected links (resume support)
# ----------------------------

if os.path.exists(LINKS_FILE):
    with open(LINKS_FILE, "r") as f:
        photo_links = set(json.load(f))
    print(f"Resumed with {len(photo_links)} previously collected links")
else:
    photo_links = set()


def save_links():
    with open(LINKS_FILE, "w") as f:
        json.dump(list(photo_links), f)


# ----------------------------
# Scroll and Collect Photo Links
# ----------------------------

same_height_count = 0
last_height = 0
scroll_round = 0

print("\nScrolling deeply into Facebook photos...\n")

while True:

    scroll_round += 1
    print(f"\nScroll Round {scroll_round}")

    for _ in range(20):
        driver.execute_script("window.scrollBy(0, 1200);")
        time.sleep(1.5)

    time.sleep(5)

    # Collect all hrefs in one JS call - returns plain strings,
    # so there is no WebElement handle that can go stale
    try:
        hrefs = driver.execute_script(
            "return Array.from(document.querySelectorAll('a')).map(a => a.href);"
        )
    except Exception as e:
        print(f"JS collection failed this round: {e}")
        hrefs = []

    added_this_round = 0

    for href in hrefs:
        if href and "fbid=" in href and "facebook.com/photo" in href:
            href = href.split("&")[0]
            if href not in photo_links:
                photo_links.add(href)
                added_this_round += 1

    print(f"Added this round: {added_this_round}")
    print(f"Total collected: {len(photo_links)}")

    # Checkpoint every round so a crash never loses progress again
    save_links()

    new_height = driver.execute_script("return document.body.scrollHeight")
    print(f"Current height: {new_height}")

    if new_height == last_height:
        same_height_count += 1
        print(f"No height increase ({same_height_count}/10)")
    else:
        same_height_count = 0

    last_height = new_height

    if same_height_count >= 10:
        print("\nReached probable absolute end")
        break

save_links()
print(f"\nFinished scrolling. {len(photo_links)} total links saved to {LINKS_FILE}")

# ----------------------------
# Prepare Download Folder
# ----------------------------

os.makedirs(DOWNLOADS, exist_ok=True)

downloaded_files = set(os.listdir(DOWNLOADS))

print(f"\nStarting download of {len(photo_links)} photos...")

# ----------------------------
# Open Each Photo Page
# ----------------------------

for idx, photo_url in enumerate(photo_links):

    try:

        print(f"\n[{idx+1}/{len(photo_links)}]")

        # Extract FBID
        fbid = photo_url.split("fbid=")[1].split("&")[0]

        filename = f"{fbid}.jpg"

        # Skip existing
        if filename in downloaded_files:

            print(f"Skipping existing: {filename}")
            continue

        # Open photo page
        driver.get(photo_url)

        time.sleep(4)

        # Find highest quality image via a single JS call - returns a
        # plain string, so there is no WebElement handle that can go stale
        try:
            best_url = driver.execute_script("""
                const imgs = Array.from(document.querySelectorAll('img'));
                let best = null;
                for (const img of imgs) {
                    if (img.src && img.src.includes('scontent')) {
                        if (!best || img.src.length > best.length) {
                            best = img.src;
                        }
                    }
                }
                return best;
            """)
        except Exception as e:
            print(f"Image extraction failed: {e}")
            best_url = None

        if not best_url:

            print("No valid image found")
            continue

        # Download image
        response = requests.get(best_url, timeout=20)

        if response.status_code == 200:

            filepath = os.path.join(DOWNLOADS, filename)

            with open(filepath, "wb") as f:

                f.write(response.content)
                downloaded_files.add(filename)
            print(f"Downloaded: {filename}")

        else:

            print(f"HTTP Error: {response.status_code}")

    except Exception as e:

        print(f"Failed: {e}")

# ----------------------------
# Cleanup
# ----------------------------

driver.quit()

print("\nDone.")
