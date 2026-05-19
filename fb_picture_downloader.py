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
time.sleep(20)

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

last_height = driver.execute_script(
    "return document.body.scrollHeight"
)

MAX_SCROLLS = 300

for i in range(MAX_SCROLLS):

    print(f"\nScroll {i+1}/{MAX_SCROLLS}")

    # Scroll down
    driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);"
    )

    time.sleep(5)

    anchors = driver.find_elements(By.TAG_NAME, "a")

    print(f"Found {len(anchors)} anchors")

    for a in anchors:

        href = a.get_attribute("href")

        if (
            href and
            "fbid=" in href and
            "facebook.com/photo" in href
        ):

            href = href.split("&")[0]

            photo_links.add(href)

    print(f"Collected {len(photo_links)} unique photo links")

    # Detect end of page
    new_height = driver.execute_script(
        "return document.body.scrollHeight"
    )

    if new_height == last_height:

        print("Reached end of page")
        break

    last_height = new_height

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