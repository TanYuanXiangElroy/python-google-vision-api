import os
from flask import Flask, request, jsonify
from serpapi import GoogleSearch
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")

@app.route('/scan', methods=['POST'])
def scan_image():
    if not SERPAPI_KEY:
        return jsonify({"error": "SERPAPI_KEY not set in environment or .env file"}), 500

    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    try:
        file = request.files['image']
        temp_filename = "temp_upload_image.jpg"
        file.save(temp_filename)

        url = "https://serpapi.com/search"
        files = {'image': open(temp_filename, 'rb')}
        params = {
            "engine": "google_lens",
            "api_key": SERPAPI_KEY
        }
        
        print("Sending to SerpApi...")
        resp = requests.post(url, params=params, files=files)
        data = resp.json()
        
        # Clean up
        files['image'].close()
        os.remove(temp_filename)
        
        if "error" in data:
            return jsonify({"error": data["error"]}), 500

        # --- PARSE RESULTS ---
        results = {
            "success": True,
            "best_guesses": [],
            "visual_matches": []
        }
        
        # 1. Check Knowledge Graph (The "Box" Google shows for entities)
        if "knowledge_graph" in data:
            kg = data["knowledge_graph"]
            title = kg.get("title", "")
            subtitle = kg.get("subtitle", "")
            if title:
                results["best_guesses"].append(f"{title} ({subtitle})")

        # 2. Visual Matches (Similar images found)
        if "visual_matches" in data:
            for match in data["visual_matches"][:10]:
                results["visual_matches"].append({
                    "title": match.get("title", ""),
                    "source": match.get("source", ""),
                    "link": match.get("link", ""),
                    "thumbnail": match.get("thumbnail", "")
                })

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)