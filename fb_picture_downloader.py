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
input("After login press ENTER...")

# ----------------------------
# Open Photos Page
# ----------------------------

driver.get(PAGE_URL)

print("Opened photos page")

time.sleep(10)

# ----------------------------
# Scroll and Collect Images
# ----------------------------

image_urls = set()

last_height = driver.execute_script(
    "return document.body.scrollHeight"
)

for i in range(30):

    print(f"\nScroll {i+1}")

    driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);"
    )

    time.sleep(5)

    images = driver.find_elements(By.TAG_NAME, "img")

    print(f"Found {len(images)} images")

    for img in images:

        src = img.get_attribute("src")

        if src:

            # skip tiny icons/profile pics
            if "scontent" in src:

                image_urls.add(src)

    print(f"Collected {len(image_urls)} image URLs")

    new_height = driver.execute_script(
        "return document.body.scrollHeight"
    )

    if new_height == last_height:

        print("Reached end")
        break

    last_height = new_height

driver.quit()

# ----------------------------
# Download Images
# ----------------------------

os.makedirs("downloads", exist_ok=True)

print("\nStarting downloads...")

for url in image_urls:

    try:

        response = requests.get(url, timeout=15)

        if response.status_code == 200:

            # ----------------------------
            # Extract Facebook media ID
            # ----------------------------

            filename_id = None

            parts = url.split("/")

            for part in parts:

                if part.isdigit() and len(part) > 8:
                    filename_id = part
                    break

            # fallback
            if not filename_id:
                filename_id = str(abs(hash(url)))

            filename = f"downloads/{filename_id}.jpg"

            # ----------------------------
            # Save Image
            # ----------------------------

            with open(filename, "wb") as f:
                f.write(response.content)

            print(f"Downloaded {filename}")

    except Exception as e:

        print(f"Failed: {e}")

print("\nDone.")