import os
import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Set up WebDriver to open the default browser
driver = webdriver.Chrome()

# URL for the initial page
url = "https://www.hktvmall.com/hktv/zh/main/Turbo-Italy/s/H5595001?page=0&q=%3Arelevance%3Astreet%3Amain%3Astore%3AH5595001%3A"

# Directory to save images
os.makedirs("turbo_italy_product_images", exist_ok=True)

# Number of pages to scrape and limit of images per page
page_start = 1
page_end = 6
image_limit_per_page = 3000

# Set to track filenames to avoid duplicates
downloaded_filenames = set()


# Function to extract initial English letters, numbers, and allowed symbols from alt text until encountering other characters
def extract_initial_english_numeric_symbols(text):
    # Include English letters, numbers, spaces, and common symbols: . , - _
    match = re.match(r'^[A-Za-z0-9\s.,-_]*', text)
    return match.group(0).rstrip() if match else ""


# Function to close the ad if it appears
def close_ad():
    try:
        # Attempt to locate and click the ad close button if it exists
        ad_close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[6]/div/i'))
        )
        ad_close_button.click()
        print("Ad closed successfully.")
        time.sleep(2)  # Short delay to ensure ad is fully closed
    except Exception as e:
        print("No ad to close or failed to close the ad.")


# Open the initial page
driver.get(url)
time.sleep(5)  # Wait for the page to load

# Try closing the ad initially
close_ad()

# Loop through each page using the page navigation
for page_num in range(page_start, page_end + 1):
    # Repeatedly attempt to close the ad before navigating to the next page
    close_ad()

    # Wait until the dropdown is clickable and select the page number
    try:
        page_select = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@class="page-nav"]//select'))
        )
        page_select.click()  # Click to open the dropdown

        # Select the specific page number
        option = driver.find_element(By.XPATH, f'//option[@value="{page_num}"]')
        option.click()
        print(f"Navigated to page {page_num}")
        time.sleep(5)  # Wait for the page to load after selecting
    except Exception as e:
        print(f"Failed to navigate to page {page_num}: {e}")
        continue

    # Parse the page content with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Find all <img> tags on the page
    img_tags = soup.find_all("img")

    # Loop through <img> tags, download images, and stop after 300 images
    image_count = 0
    for img_tag in img_tags:
        if image_count >= image_limit_per_page:
            print(f"Reached the limit of {image_limit_per_page} images for page {page_num}. Moving to the next page.")
            break

        try:
            # Get the image URL
            img_url = img_tag.get("src")

            # Skip if img_url is None
            if not img_url:
                continue

            # Ensure full URL if the src is relative
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                img_url = url + img_url

            # Get the alt text and generate a filename
            alt_text = img_tag.get("alt", "")
            truncated_alt_text = extract_initial_english_numeric_symbols(alt_text)
            img_name = f"{truncated_alt_text}.jpg"

            # Skip if filename is already downloaded
            if img_name in downloaded_filenames:
                print(f"Skipping duplicate image: {img_name}")
                continue

            # Add filename to set to track downloaded files
            downloaded_filenames.add(img_name)

            # Define the path for saving the image
            img_path = os.path.join("turbo_italy_product_images", img_name)

            # Download the image
            img_data = requests.get(img_url).content
            with open(img_path, 'wb') as handler:
                handler.write(img_data)
            print(f"Downloaded {img_path}")

            image_count += 1  # Increment the count of downloaded images for this page

        except Exception as e:
            print(f"Failed to download image on page {page_num}: {e}")

# Close the WebDriver after scraping
driver.quit()
