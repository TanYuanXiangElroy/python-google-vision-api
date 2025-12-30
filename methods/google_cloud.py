import os
from collections import Counter
import re
from google.cloud import vision

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

def analyze_with_google_cloud(image_bytes, credentials_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)
    
    print("Method 1: Sending to Google Cloud Vision API...")
    response = client.web_detection(image=image)

    if response.error.message:
        raise Exception(response.error.message)

    # Transform to common format
    visual_matches = []
    if response.web_detection.pages_with_matching_images:
        for page in response.web_detection.pages_with_matching_images:
             visual_matches.append({
                "title": page.page_title,
                "link": page.url,
                "source": "Google Vision",
                "thumbnail": None
            })

    best_guesses = [label.label for label in response.web_detection.best_guess_labels]
    
    return {
        "success": True,
        "method": "Google Cloud Vision",
        "best_guesses": best_guesses,
        "visual_matches": visual_matches[:10],
        "common_keywords": get_common_words([m['title'] for m in visual_matches])
    }
