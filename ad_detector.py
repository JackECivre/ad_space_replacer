from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from PIL import Image
import os
import time
import json
import shutil

# Paths for outputs
SCREENSHOT_FOLDER = "static/screenshots"
METADATA_PATH = os.path.join(SCREENSHOT_FOLDER, "metadata.json")
UPDATED_SCREENSHOT_PATH = os.path.join(SCREENSHOT_FOLDER, "updated_page.png")

# Initialize Selenium WebDriver
def init_driver():
    CHROMEDRIVER_PATH = "d:\\chromedriver\\chromedriver.exe"  # User's specific path
    options = webdriver.ChromeOptions()
    # Full-page mode
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--start-maximized')
    return webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

# Open a webpage and return the driver instance
def open_webpage(url):
    driver = init_driver()
    driver.get(url)
    print(f"Webpage opened: {url}")
    return driver

# Capture ad space and return metadata
def capture_ad_space(driver, selector, screenshot_folder):
    element = driver.find_element("css selector", selector)
    location = element.location
    size = element.size

    # Full-page screenshot
    full_screenshot_path = os.path.join(screenshot_folder, "full_page_screenshot.png")
    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_width = driver.execute_script("return window.innerWidth")
    driver.set_window_size(viewport_width, total_height)
    time.sleep(1)  # Allow resizing to take effect
    driver.save_screenshot(full_screenshot_path)

    # Crop the ad space
    with Image.open(full_screenshot_path) as img:
        x, y, width, height = int(location["x"]), int(location["y"]), int(size["width"]), int(size["height"])
        cropped = img.crop((x, y, x + width, y + height))
        ad_screenshot_path = os.path.join(screenshot_folder, "ad_space_screenshot.png")
        cropped.save(ad_screenshot_path)

    # Metadata
    metadata = {
        "selector": selector,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "screenshot": ad_screenshot_path
    }
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=4)

    return metadata

# Replace ad space in full-page screenshot
def replace_ad_space(metadata, creative_path, updated_path):
    with Image.open(metadata["screenshot"]) as ad_space_img, Image.open(creative_path) as creative_img, Image.open(metadata["screenshot"]) as full_img:
        # Resize creative if dimensions don't match
        if creative_img.size != (metadata["width"], metadata["height"]):
            creative_img = creative_img.resize((metadata["width"], metadata["height"]))
        full_img.paste(creative_img, (metadata["x"], metadata["y"]))
        full_img.save(updated_path)

# Clear all outputs
def reset_process():
    if os.path.exists(SCREENSHOT_FOLDER):
        shutil.rmtree(SCREENSHOT_FOLDER)
    os.makedirs(SCREENSHOT_FOLDER)
    print("All screenshots and metadata have been reset.")
