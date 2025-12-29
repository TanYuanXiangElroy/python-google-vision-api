#app.py
import streamlit as st
import requests
from PIL import Image
import io

# backend URL
API_URL = "http://localhost:5000/scan"

st.set_page_config(page_title="Poke-Dex Vision (SerpApi)", page_icon="🔍", layout="wide")

st.title("🔍 Google Lens Image Search")
st.write("Identify objects using SerpApi (Google Lens)")

# Create tabs for different input methods
tab1, tab2 = st.tabs(["📸 Take Photo", "📂 Upload Image"])

image_file = None

with tab1:
    camera_image = st.camera_input("Take a picture")
    if camera_image:
        image_file = camera_image

with tab2:
    uploaded_image = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    if uploaded_image:
        image_file = uploaded_image
        st.image(image_file, caption="Uploaded Image", use_column_width=True)

if image_file is not None:
    if st.button("🔍 Analyze Image", type="primary"):
        with st.spinner("Analyzing with Google Lens..."):
            try:
                # Prepare the file for the request
                files = {"image": image_file.getvalue()}
                
                response = requests.post(API_URL, files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    st.success("Analysis Complete!")
                    
                    # 1. Knowledge Graph (Best Guess)
                    st.subheader("🏆 Best Match (Knowledge Graph)")
                    best_guesses = data.get("best_guesses", [])
                    if best_guesses:
                        for guess in best_guesses:
                            st.markdown(f"### **{guess}**")
                    else:
                        st.write("No direct knowledge graph match found.")
                    
                    st.divider()

                    # 2. Visual Matches
                    st.subheader("🖼️ Visual Matches")
                    visual_matches = data.get("visual_matches", [])
                    
                    if visual_matches:
                        # Create a grid layout
                        cols = st.columns(3)
                        for idx, match in enumerate(visual_matches):
                            with cols[idx % 3]:
                                if match.get('thumbnail'):
                                    st.image(match['thumbnail'], use_column_width=True)
                                st.markdown(f"**[{match.get('title', 'No Title')}]({match.get('link', '#')})**")
                                st.caption(f"Source: {match.get('source', 'Unknown')}")
                    else:
                        st.write("No visual matches found.")
                            
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend server. Is it running?")
            except Exception as e:
                st.error(f"An error occurred: {e}")
