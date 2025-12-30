import os
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from collections import Counter
import re
from dotenv import load_dotenv

# We store the "found" class here to persist it across requests (if the server stays alive)
DETECTED_TITLE_CLASS = "Yt787" 

def get_common_words(titles):
    if not titles:
        return []
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'buy', 'sell', 'shop', 'online', 'store',
        'price', 'best', 'review', 'images', 'photos', 'video', 'youtube', 'com', 'www', 'http',
        'https', 'reddit', 'ebay', 'amazon', 'pinterest', 'twitter', 'facebook', 'instagram',
        'stuffed', 'animal', 'toy', 'plush', 'soft', 'doll', 'figure', 'figurine', 'new', 'used',
        'sale', 'free', 'shipping', 'official', 'licensed', 'authentic', 'japan', 'center', 'collection'
    }
    all_text = " ".join(titles)
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', all_text.lower())
    words = cleaned_text.split()
    meaningful_words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    word_counts = Counter(meaningful_words)
    return [{"word": word, "count": count} for word, count in word_counts.most_common(5)]

def analyze_with_selenium(image_bytes, imgbb_key):
    IMGBB_KEY = imgbb_key
    
    # 1. Upload
    public_url = upload_to_imgbb(image_bytes, IMGBB_KEY)
    if not public_url:
        raise Exception("Failed to upload image to ImgBB")
    
    # 2. Scrape
    print(f"Scraping Lens for URL: {public_url}")
    # TEMPORARY: Set headless=False so the user can see/solve CAPTCHAs for their screenshot
    results, used_class = scrape_google_lens_selenium(public_url, headless=False)
    
    keywords = get_common_words([m['title'] for m in results])

    return {
        "success": True,
        "method": "Selenium Scraping",
        "best_guesses": [k['word'] for k in keywords[:2]] if keywords else [],
        "visual_matches": results,
        "common_keywords": keywords,
        "debug_info": f"Class used: {used_class}"
    }

def upload_to_imgbb(image_bytes, api_key):
    upload_url = "https://api.imgbb.com/1/upload"
    try:
        files = {'image': image_bytes}
        params = {'key': api_key}
        response = requests.post(upload_url, params=params, files=files)
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                return data['data']['url']
    except Exception as e:
        print(f"ImgBB Upload Exception: {e}")
    return None

def detect_dynamic_class(soup, expected_text="Charmander"):
    """
    Searches the soup for elements containing expected_text.
    Returns the most common class name among them.
    """
    print(f"Attemping to auto-detect class using expected text: '{expected_text}'")
    
    # Find all elements containing the text (case-insensitive)
    elements = soup.find_all(string=re.compile(expected_text, re.IGNORECASE))
    
    if not elements:
        print(f"Debug: Expected text '{expected_text}' NOT FOUND in page source.")
        return None

    class_counts = Counter()
    
    for text_node in elements:
        parent = text_node.parent
        if parent and parent.name in ['div', 'span', 'h3', 'a']:
            classes = parent.get('class')
            if classes:
                for cls in classes:
                    class_counts[cls] += 1
    
    if class_counts:
        best_class = class_counts.most_common(1)[0][0]
        print(f"Detected potential title class: '{best_class}'")
        return best_class
    
    return None

def scrape_google_lens_selenium(image_url, headless=True, expected_text="Charmander"):
    global DETECTED_TITLE_CLASS
    results = []
    
    print(f"Initializing Undetected Chrome Driver (Headless={headless})...")
    options = uc.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    # else:
    #     options.add_argument("--start-maximized") # Removed to reduce intrusiveness

    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=en-US")
    
    driver = None
    try:
        driver = uc.Chrome(options=options, version_main=142)
        
        # Minimize window immediately to run in "background" (taskbar)
        if not headless:
            try:
                driver.minimize_window()
            except Exception:
                pass # Ignore if minimization fails

        lens_url = f"https://lens.google.com/uploadbyurl?url={urllib.parse.quote(image_url)}"
        print(f"Navigating to: {lens_url}")
        driver.get(lens_url)
        
        # Human-like pause
        time.sleep(5)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Save debug artifacts
        if not headless:
             driver.save_screenshot("debug_lens_visible.png")
        
        # 1. Try with the currently known class
        title_elements = soup.select(f".{DETECTED_TITLE_CLASS}")
        
        # 2. Dynamic Calibration
        if not title_elements:
            print(f"Warning: No elements found with class '{DETECTED_TITLE_CLASS}'. Attempting dynamic detection...")
            
            # Save HTML for inspection if we are about to fail
            with open("debug_lens_failed.html", "w") as f:
                f.write(html)
            
            new_class = detect_dynamic_class(soup, expected_text)
            if new_class:
                print(f"Calibration Successful! Updating class from '{DETECTED_TITLE_CLASS}' to '{new_class}'")
                DETECTED_TITLE_CLASS = new_class
                title_elements = soup.select(f".{DETECTED_TITLE_CLASS}")
        
        for item in title_elements:
            title = item.get_text(strip=True)
            link = "#"
            parent_a = item.find_parent('a')
            if parent_a:
                link = parent_a.get('href', '#')
            
            if title:
                results.append({
                    "title": title,
                    "link": link,
                    "source": "Google Lens (Scraped)",
                    "thumbnail": None
                })
                
    except Exception as e:
        print(f"Selenium Error: {e}")
    finally:
        if driver:
            driver.quit()
            
    return results, DETECTED_TITLE_CLASS

if __name__ == "__main__":
    load_dotenv()
    print("--- SELENIUM DEBUG MODE ---")
    
    # Get Image
    img_path = "test_pic/test_char.jpg"
    if not os.path.exists(img_path):
        # Handle case where we run from inside 'methods/' folder
        img_path = "../test_pic/test_char.jpg"
        if not os.path.exists(img_path):
            print("Error: Could not find 'test_pic/test_char.jpg'. Please run from project root.")
            exit()
            
    api_key = os.environ.get("IMGBB_KEY")
    if not api_key:
        print("Error: IMGBB_KEY not found in environment.")
        exit()

    print(f"1. Using image: {img_path}")
    
    # Get Mode
    mode = input("Run Headless? (y/n) [n]: ").lower()
    is_headless = mode == 'y'
    
    # Get Expected Text
    expect = input("Enter text expected to be in the title (default 'Charmander'): ")
    if not expect:
        expect = "Charmander"
        
    print(f"2. Uploading...")
    with open(img_path, "rb") as f:
        img_bytes = f.read()
    public_url = upload_to_imgbb(img_bytes, api_key)
    
    if public_url:
        print(f"3. Scraping {public_url} ...")
        res, final_class = scrape_google_lens_selenium(public_url, headless=is_headless, expected_text=expect)
        
        print("\n--- RESULTS ---")
        print(f"Class Used: {final_class}")
        print(f"Matches Found: {len(res)}")
        if res:
            print("Top 3 Matches:")
            for r in res[:3]:
                print(f" - {r['title']}")
        else:
            print("No matches found. Check 'debug_lens_failed.html' if generated.")
    else:
        print("Upload failed.")