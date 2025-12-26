import os
import requests

url = 'http://localhost:5000/scan'
image_dir = 'test_pic'

if not os.path.exists(image_dir):
    print(f"Directory '{image_dir}' not found.")
    exit()

# Get all valid image files
image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
image_files.sort()

for image_name in image_files:
    image_path = os.path.join(image_dir, image_name)
    print(f"\n--- Scanning {image_name} ---")
    
    try:
        with open(image_path, 'rb') as f:
            response = requests.post(url, files={'image': f})
        
        if response.status_code == 200:
            data = response.json()
            print(f"Best Guess: {data.get('best_guess')}")
            # Print top 3 labels
            top_3 = [item['description'] for item in data.get('google_sees', [])[:3]]
            print(f"Tags: {top_3}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Failed to connect or process: {e}")