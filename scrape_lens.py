import os
import time
import urllib.parse
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load environment variables
load_dotenv()

IMGBB_KEY = os.environ.get("IMGBB_KEY")
image_path = "image/test_char.jpg"

if not IMGBB_KEY:
    print("Error: IMGBB_KEY not found in .env file.")
    exit(1)

def upload_to_imgbb(filepath, api_key):
    print(f"Uploading {filepath} to ImgBB...")
    upload_url = "https://api.imgbb.com/1/upload"
    try:
        with open(filepath, 'rb') as f:
            files = {'image': f}
            params = {'key': api_key}
            response = requests.post(upload_url, params=params, files=files)
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                return data['data']['url']
            else:
                print("ImgBB Upload failed:", data)
        else:
            print(f"ImgBB Upload HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"ImgBB Upload Exception: {e}")
    return None

def scrape_google_lens(image_url):
    print("Initializing Undetected Chrome Driver (Headless Mode)...")
    options = uc.ChromeOptions()
    options.add_argument("--headless=new") # Re-enable headless
    options.add_argument("--window-size=1920,1080") # Set a standard resolution
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=en-US")
    # Fake user agent just in case, though UC usually handles it
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Initialize the driver
    driver = uc.Chrome(options=options, version_main=142) 

    try:
        # Construct the Lens URL
        lens_url = f"https://lens.google.com/uploadbyurl?url={urllib.parse.quote(image_url)}"
        print(f"Navigating to: {lens_url}")
        
        driver.get(lens_url)
        
        print("Waiting for results to load...")
        time.sleep(5) # Wait for JS
        
        # Save screenshot for debugging
        driver.save_screenshot("lens_screenshot.png")
        print("Saved debug screenshot to lens_screenshot.png")

        # Get page source
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Save full HTML for inspection
        with open("lens_full_source.html", "w") as f:
            f.write(html)
        print("Saved full HTML to lens_full_source.html")
        
        # Extract data based on the user's observed classes
        # They mentioned: Yt787 JGD2rd
        results = soup.select(".Yt787")
        print(f"\n--- Found {len(results)} items with class 'Yt787' ---")
        
        unique_titles = set()
        for item in results:
            text = item.get_text(strip=True)
            if text:
                unique_titles.add(text)
                
        for title in unique_titles:
            print(f"- {title}")

        # Try finding the specific span pattern: <span class="Yt787 JGD2rd">
        print("\n--- Searching for 'Yt787 JGD2rd' combination ---")
        combined = soup.select(".Yt787.JGD2rd")
        for item in combined:
            print(f"Match: {item.get_text(strip=True)}")

        # Fallback: Check for knowledge graph title or other common elements
        if not unique_titles and not combined:
            print("\n[Fallback] No specific matches found. Checking other common elements...")
            # Google Lens often puts the main guess in a specific area, but it changes.
            # Let's list some text from H1, H2, or links
            for h in soup.find_all(['h1', 'h2', 'h3']):
                 print(f"Header: {h.get_text(strip=True)}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    public_url = upload_to_imgbb(image_path, IMGBB_KEY)
    if public_url:
        print(f"Image uploaded: {public_url}")
        scrape_google_lens(public_url)
    else:
        print("Failed to get public URL.")