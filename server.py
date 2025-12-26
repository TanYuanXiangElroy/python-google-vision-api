import os
from flask import Flask, request, jsonify
from google.cloud import vision

app = Flask(__name__)

# --- GOOGLE SETUP ---
# We expect the key to be at this specific path inside the Docker container
CREDENTIALS_PATH = "my-google-cloud-key.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH

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

        return jsonify({
            "success": True,
            "best_guess": response.web_detection.best_guess_labels[0].label if response.web_detection.best_guess_labels else "N/A",
            "google_sees": results
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # This starts the web server
    app.run(host='0.0.0.0', port=5000)