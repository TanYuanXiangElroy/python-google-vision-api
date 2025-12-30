import os
import requests
import json
from dotenv import load_dotenv
from serpapi import GoogleSearch

# Load environment variables
load_dotenv()

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
IMGBB_KEY = os.environ.get("IMGBB_KEY") # New ImgBB key

image_path = "test_pic/test_char.jpg"

if not SERPAPI_KEY:
    print("Error: SERPAPI_KEY not found in .env file.")
    exit()

if not IMGBB_KEY:
    print("Error: IMGBB_KEY not found in .env file. Please add your ImgBB API key.")
    exit()

if not os.path.exists(image_path):
    print(f"Error: Image not found at {image_path}")
    exit()

print(f"Using SerpApi Key: {SERPAPI_KEY[:5]}... (hidden)")
print(f"Using ImgBB Key: {IMGBB_KEY[:5]}... (hidden)")

# 1. UPLOAD TO IMGBB
print(f"1. Uploading {image_path} to ImgBB...")

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

public_url = upload_to_imgbb(image_path, IMGBB_KEY)

if not public_url:
    print("Failed to generate a public URL via ImgBB. Exiting.")
    exit()

print(f"   Success! ImgBB Public URL: {public_url}")

# 2. QUERY SERPAPI with the public URL
print(f"2. Querying SerpApi (engine=google_lens) with the public URL...")

params = {
    "engine": "google_lens",
    "url": public_url,
    "api_key": SERPAPI_KEY
}

try:
    search = GoogleSearch(params)
    results = search.get_dict()

    if "error" in results:
        print(f"Error from SerpApi: {results['error']}")
    else:
        print("\n--- RAW DATA FROM SERPAPI (google_lens) ---\n")
        
        with open("serpapi_lens_response.json", "w") as outfile: # New filename
            json.dump(results, outfile, indent=2)
        print("\n(Full JSON response saved to 'serpapi_lens_response.json')")
        
        # Quick summary for the user
        print("\n--- SUMMARY (google_lens) ---")
        if "knowledge_graph" in results:
            kg = results["knowledge_graph"]
            print(f"Knowledge Graph Title: {kg.get('title')}")
            print(f"Knowledge Graph Subtitle: {kg.get('subtitle')}")
        
        if "visual_matches" in results:
            print(f"Visual Matches Found: {len(results['visual_matches'])}")
            print("Top 3 Matches:")
            for m in results['visual_matches'][:3]:
                print(f" - {m.get('title')} ({m.get('source')})")

except Exception as e:
    print(f"An exception occurred during SerpApi search: {e}")