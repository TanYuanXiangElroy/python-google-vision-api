import os
from flask import Flask, request, jsonify
from serpapi import GoogleSearch
from dotenv import load_dotenv
import requests
from collections import Counter
import re

load_dotenv()

app = Flask(__name__)

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
IMGBB_KEY = os.environ.get("IMGBB_KEY") # Load ImgBB key

# Function to upload image to ImgBB
def upload_to_imgbb(filepath, api_key):
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
                return None
        else:
            print(f"ImgBB Upload HTTP Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"ImgBB Upload Exception: {e}")
        return None

def get_common_words(titles):
    """
    Analyzes titles to find the most frequent meaningful words.
    """
    if not titles:
        return []

    # Simple stop words to ignore (can be expanded)
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'buy', 'sell', 'shop', 'online', 'store',
        'price', 'best', 'review', 'images', 'photos', 'video', 'youtube', 'com', 'www', 'http',
        'https', 'reddit', 'ebay', 'amazon', 'pinterest', 'twitter', 'facebook', 'instagram',
        'stuffed', 'animal', 'toy', 'plush', 'soft', 'doll', 'figure', 'figurine', 'new', 'used',
        'sale', 'free', 'shipping', 'official', 'licensed', 'authentic', 'japan', 'center', 'collection'
    }

    all_text = " ".join(titles)
    
    # Normalize: lowercase and remove non-alphanumeric chars (keep spaces)
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', all_text.lower())
    
    words = cleaned_text.split()
    
    # Filter out stop words and short words
    meaningful_words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    
    # Count frequency
    word_counts = Counter(meaningful_words)
    
    # Return top 5 as a list of dictionaries
    return [{"word": word, "count": count} for word, count in word_counts.most_common(5)]


@app.route('/scan', methods=['POST'])
def scan_image():
    if not SERPAPI_KEY:
        return jsonify({"error": "SERPAPI_KEY not set in environment or .env file"}), 500
    if not IMGBB_KEY:
        return jsonify({"error": "IMGBB_KEY not set in environment or .env file"}), 500

    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    try:
        file = request.files['image']
        temp_filename = "temp_upload_image.jpg"
        file.save(temp_filename)

        # 1. Upload to ImgBB
        public_image_url = upload_to_imgbb(temp_filename, IMGBB_KEY)
        
        # Clean up temporary local file immediately after upload
        os.remove(temp_filename)

        if not public_image_url:
            return jsonify({"error": "Failed to get a public image URL from ImgBB"}), 500

        # 2. Query SerpApi with the public URL
        params = {
            "engine": "google_lens",
            "url": public_image_url, # Use the public URL
            "api_key": SERPAPI_KEY
        }
        
        print(f"Sending public URL {public_image_url} to SerpApi...")
        search = GoogleSearch(params)
        data = search.get_dict() # Use the library's get_dict() method

        if "error" in data:
            return jsonify({"error": data["error"]}), 500

        # --- PARSE RESULTS ---
        results = {
            "success": True,
            "best_guesses": [],
            "visual_matches": [],
            "common_keywords": []
        }
        
        # 1. Check Knowledge Graph (The "Box" Google shows for entities)
        if "knowledge_graph" in data:
            kg = data["knowledge_graph"]
            title = kg.get("title", "")
            subtitle = kg.get("subtitle", "")
            if title:
                results["best_guesses"].append(f"{title} ({subtitle})")

        # 2. Visual Matches (Similar images found)
        titles_for_analysis = []
        if "visual_matches" in data:
            # Get up to 50 matches for analysis
            matches = data["visual_matches"][:50]
            
            for match in matches:
                title = match.get("title", "")
                titles_for_analysis.append(title)
                
                # Only add top 10 to the return list for display to keep response size down
                if len(results["visual_matches"]) < 10:
                    results["visual_matches"].append({
                        "title": title,
                        "source": match.get("source", ""),
                        "link": match.get("link", ""),
                        "thumbnail": match.get("thumbnail", "")
                    })
        
        # 3. Analyze Keywords from Titles
        results["common_keywords"] = get_common_words(titles_for_analysis)

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)