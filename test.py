#test.py
import os
import requests

url = 'http://localhost:5000/scan'
image_dir = 'test_pic'

if not os.path.exists(image_dir):
    print(f"Directory '{image_dir}' not found.")
    exit()

# Get all valid image files
image_files = ['test_char.jpg']
image_files.sort()

for image_name in image_files:
    image_path = os.path.join(image_dir, image_name)
    print(f"\n--- Scanning {image_name} ---")
    
    try:
        with open(image_path, 'rb') as f:
            response = requests.post(url, files={'image': f})
        
        if response.status_code == 200:
            data = response.json()
            best_guesses = data.get('best_guesses', [])
            if best_guesses:
                print(f"Best Guesses: {', '.join(best_guesses[:5])}")
            else:
                 print(f"Best Guess: {data.get('best_guess', 'N/A')}")

            # Print top 5 labels
            top_5 = [item['description'] for item in data.get('google_sees', [])[:5]]
            print(f"Tags: {top_5}")

            # Print top 3 matching pages
            matching_pages = data.get('matching_pages', [])
            if matching_pages:
                print("Matching Pages:")
                for page in matching_pages[:3]:
                    print(f" - {page.get('page_title')}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Failed to connect or process: {e}")