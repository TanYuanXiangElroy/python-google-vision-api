#server.py
import os
from flask import Flask, request, jsonify
from google.cloud import vision
from collections import Counter
import re

app = Flask(__name__)

# --- GOOGLE SETUP ---
# We expect the key to be at this specific path inside the Docker container
CREDENTIALS_PATH = "my-google-cloud-key.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH

def get_common_words(pages):
    """
    Analyzes page titles to find the most frequent meaningful words.
    """
    if not pages:
        return []

    # Simple stop words to ignore (can be expanded)
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'buy', 'sell', 'shop', 'online', 'store',
        'price', 'best', 'review', 'images', 'photos', 'video', 'youtube', 'com', 'www', 'http',
        'https', 'reddit', 'ebay', 'amazon', 'pinterest', 'twitter', 'facebook', 'instagram'
    }

    all_text = " ".join([p.page_title for p in pages if p.page_title])
    
    # Normalize: lowercase and remove non-alphanumeric chars (keep spaces)
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', all_text.lower())
    
    words = cleaned_text.split()
    
    # Filter out stop words and short words
    meaningful_words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    
    # Count frequency
    word_counts = Counter(meaningful_words)
    
    # Return top 10 as a list of dictionaries
    return [{"word": word, "count": count} for word, count in word_counts.most_common(10)]

@app.route('/scan', methods=['POST'])
def scan_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    try:
        # 1. Read the image bytes
        file = request.files['image']
        content = file.read()
        image = vision.Image(content=content)

        # 2. Start Google Vision Client
        
        client = vision.ImageAnnotatorClient()

        # 3. Call Web Detection (The "Reverse Image Search" feature)
        print("Sending to Google...")
        response = client.web_detection(image=image)

        if response.error.message:
            return jsonify({"error": response.error.message}), 500

        # 4. Extract Keywords (Web Entities)
        results = []
        if response.web_detection.web_entities:
            for entity in response.web_detection.web_entities:
                results.append({
                    "description": entity.description,
                    "score": round(entity.score, 2) # Confidence (0.0 to 1.0)
                })

        # 5. Extract Matching Pages (Rich Context)
        matching_pages = []
        raw_pages = [] # Keep raw objects for internal analysis
        if response.web_detection.pages_with_matching_images:
            raw_pages = response.web_detection.pages_with_matching_images
            for page in response.web_detection.pages_with_matching_images:
                matching_pages.append({
                    "url": page.url,
                    "page_title": page.page_title,
                    "score": round(page.score, 2) if page.score else 0.0
                })

        # 6. Analyze Keywords from Page Titles
        common_keywords = get_common_words(raw_pages)

        return jsonify({
            "success": True,
            "best_guesses": [label.label for label in response.web_detection.best_guess_labels],
            "google_sees": results,
            "matching_pages": matching_pages,
            "common_keywords": common_keywords
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # This starts the web server
    app.run(host='0.0.0.0', port=5000)