from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import requests
import time
import os

PAGE_URL = "https://www.facebook.com/bssjauharcampus/photos"

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
time.sleep(7)

# ----------------------------
# Open Photos Page
# ----------------------------

driver.get(PAGE_URL)

print("Opened photos page")

time.sleep(10)

# ----------------------------
# Scroll and Collect Photo Links
# ----------------------------

photo_links = set()

same_height_count = 0

last_height = 0

scroll_round = 0

print("\nScrolling deeply into Facebook photos...\n")

while True:

    scroll_round += 1

    print(f"\nScroll Round {scroll_round}")

    # gradual scrolling
    for _ in range(20):

        driver.execute_script(
            "window.scrollBy(0, 1200);"
        )

        time.sleep(1.5)

    # extra wait for FB lazy loading
    time.sleep(5)

    # collect links
    anchors = driver.find_elements(By.TAG_NAME, "a")

    added_this_round = 0

    for a in anchors:

        href = a.get_attribute("href")

        if (
            href and
            "fbid=" in href and
            "facebook.com/photo" in href
        ):

            href = href.split("&")[0]

            if href not in photo_links:

                photo_links.add(href)
                added_this_round += 1

    print(f"Added this round: {added_this_round}")
    print(f"Total collected: {len(photo_links)}")

    # get new height
    new_height = driver.execute_script(
        "return document.body.scrollHeight"
    )

    print(f"Current height: {new_height}")

    # Facebook often pauses height growth temporarily
    if new_height == last_height:

        same_height_count += 1

        print(
            f"No height increase "
            f"({same_height_count}/10)"
        )

    else:

        same_height_count = 0

    last_height = new_height

    # only stop after MANY stagnant checks
    if same_height_count >= 10:

        print("\nReached probable absolute end")
        break
# ----------------------------
# Prepare Download Folder
# ----------------------------

os.makedirs("downloads", exist_ok=True)

downloaded_files = set(os.listdir("downloads"))

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

        images = driver.find_elements(By.TAG_NAME, "img")

        best_url = None

        # Find highest quality image
        for img in images:

            src = img.get_attribute("src")

            if src and "scontent" in src:

                # choose longest URL (usually highest quality)
                if not best_url or len(src) > len(best_url):

                    best_url = src

        if not best_url:

            print("No valid image found")
            continue

        # Download image
        response = requests.get(best_url, timeout=20)

        if response.status_code == 200:

            filepath = os.path.join("downloads", filename)

            with open(filepath, "wb") as f:

                f.write(response.content)

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