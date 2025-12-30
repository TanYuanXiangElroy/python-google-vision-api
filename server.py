import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Import our distinct logic modules
from methods.google_cloud import analyze_with_google_cloud
from methods.serpapi import analyze_with_serpapi
from methods.selenium_lens import analyze_with_selenium

load_dotenv()

app = Flask(__name__)

# --- CONFIG ---
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
IMGBB_KEY = os.environ.get("IMGBB_KEY")
GOOGLE_CREDS = "my-google-cloud-key.json" 

@app.route('/scan', methods=['POST'])
def scan_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    method = request.form.get('method', 'cloud_vision') # Default to method 1
    file = request.files['image']
    image_bytes = file.read()

    try:
        if method == 'cloud_vision':
            result = analyze_with_google_cloud(image_bytes, GOOGLE_CREDS)
        elif method == 'serpapi':
            if not SERPAPI_KEY or not IMGBB_KEY:
                return jsonify({"error": "Missing API Keys for SerpApi method"}), 500
            result = analyze_with_serpapi(image_bytes, SERPAPI_KEY, IMGBB_KEY)
        elif method == 'selenium':
            if not IMGBB_KEY:
                return jsonify({"error": "Missing ImgBB Key for Selenium method"}), 500
            result = analyze_with_selenium(image_bytes, IMGBB_KEY)
        else:
            return jsonify({"error": "Invalid method specified"}), 400
            
        return jsonify(result)

    except Exception as e:
        print(f"Error processing request ({method}): {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)