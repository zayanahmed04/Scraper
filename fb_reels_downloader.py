from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import subprocess

PAGE_URL = "https://www.facebook.com/bssjauharcampus/reels"

# ----------------------------
# Chrome Setup
# ----------------------------

options = webdriver.ChromeOptions()

# IMPORTANT
# create a separate selenium profile

options.add_argument(r"--user-data-dir=C:\selenium_profile")

options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

print("Chrome launched")

# ----------------------------
# Open Facebook
# ----------------------------

driver.get("https://facebook.com")

print("Please login manually...")
input("After login press ENTER here...")

# ----------------------------
# Open Reels Page
# ----------------------------

driver.get(PAGE_URL)

print("Opened reels page")

time.sleep(10)

# ----------------------------
# Scroll + Extract
# ----------------------------

links = set()

last_height = driver.execute_script(
    "return document.body.scrollHeight"
)

for i in range(30):

    print(f"\nScroll {i+1}")

    # scroll down
    driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);"
    )

    time.sleep(5)

    elements = driver.find_elements(By.TAG_NAME, "a")

    print(f"Found {len(elements)} anchors")

    for el in elements:

        href = el.get_attribute("href")

        if href:

            if "/reel/" in href or "/videos/" in href:

                href = href.split("?")[0]

                links.add(href)

    print(f"Collected {len(links)} unique links")

    # detect end
    new_height = driver.execute_script(
        "return document.body.scrollHeight"
    )

    if new_height == last_height:

        print("Reached end of page")
        break

    last_height = new_height

# ----------------------------
# Save URLs
# ----------------------------

with open("urls.txt", "w", encoding="utf-8") as f:

    for url in links:
        f.write(url + "\n")

print(f"\nSaved {len(links)} URLs")

# ----------------------------
# Download
# ----------------------------

print("\nStarting downloads...")

command = [
    "python",
    "-m",
    "yt_dlp",
    "--cookies", "cookies.txt",
    "-a", "urls.txt",
    "--ignore-errors",
    "--download-archive", "downloaded.txt",
    "-o",
    "downloads/%(uploader)s/%(upload_date)s-%(title)s.%(ext)s"
]

subprocess.run(" ".join(command), shell=True)

driver.quit()