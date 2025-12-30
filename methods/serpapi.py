import requests
from serpapi import GoogleSearch
from collections import Counter
import re

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

def analyze_with_serpapi(image_bytes, serpapi_key, imgbb_key):
    # 1. Upload to ImgBB first (SerpApi needs a public URL)
    print("Method 2: Uploading to ImgBB for SerpApi...")
    upload_url = "https://api.imgbb.com/1/upload"
    files = {'image': image_bytes}
    params = {'key': imgbb_key}
    response = requests.post(upload_url, params=params, files=files)
    
    if response.status_code != 200:
        raise Exception(f"ImgBB Upload Failed: {response.text}")
    
    public_url = response.json()['data']['url']
    
    # 2. Call SerpApi
    print(f"Method 2: Querying SerpApi with {public_url}...")
    params = {
        "engine": "google_lens",
        "url": public_url,
        "api_key": serpapi_key
    }
    search = GoogleSearch(params)
    data = search.get_dict()
    
    if "error" in data:
        raise Exception(data["error"])

    # Transform
    best_guesses = []
    if "knowledge_graph" in data:
        kg = data["knowledge_graph"]
        if kg.get("title"):
             best_guesses.append(f"{kg.get('title')} ({kg.get('subtitle','')})")

    visual_matches = []
    if "visual_matches" in data:
        for match in data["visual_matches"][:20]:
            visual_matches.append({
                "title": match.get("title"),
                "link": match.get("link"),
                "source": match.get("source"),
                "thumbnail": match.get("thumbnail")
            })

    return {
        "success": True,
        "method": "SerpApi (Google Lens)",
        "best_guesses": best_guesses,
        "visual_matches": visual_matches[:10],
        "common_keywords": get_common_words([m['title'] for m in visual_matches])
    }
