import os
import streamlit as st
import requests


# Docker Backend environment variable
API_URL = os.getenv("API_URL", "http://localhost:5000/scan")

st.set_page_config(page_title="Poke-Dex Vision (Unified)", page_icon="🔍", layout="wide")

st.title("🔍 Universal Image Search")
st.write("Compare different techniques for identifying objects.")

# --- SIDEBAR: METHOD SELECTION ---
st.sidebar.header("⚙️ Configuration")
method = st.sidebar.radio(
    "Select Search Method:",
    ("Google Cloud Vision API", "SerpApi (Google Lens)", "Selenium Scraping (Free)")
)

# Map friendly names to backend keys
method_map = {
    "Google Cloud Vision API": "cloud_vision",
    "SerpApi (Google Lens)": "serpapi",
    "Selenium Scraping (Free)": "selenium"
}
selected_method_key = method_map[method]

st.sidebar.info(f"**Current Mode:** {method}")
if selected_method_key == "selenium":
    st.sidebar.warning("⚠️ Selenium mode is slow and may be blocked by Google.")

# --- MAIN UI ---
input_source = st.radio("Select Input Source:", ("📸 Take Photo", "📂 Upload Image"), horizontal=True)
image_file = None

if input_source == "📸 Take Photo":
    camera_image = st.camera_input("Take a picture")
    if camera_image:
        image_file = camera_image

elif input_source == "📂 Upload Image":
    uploaded_image = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    if uploaded_image:
        image_file = uploaded_image
        st.image(image_file, caption="Uploaded Image", width='stretch')

if image_file is not None:
    if st.button("🔍 Analyze Image", type="primary"):
        with st.spinner(f"Analyzing using {method}..."):
            try:
                # Prepare request
                files = {"image": image_file.getvalue()}
                data = {"method": selected_method_key}
                
                response = requests.post(API_URL, files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success("Analysis Complete!")
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.subheader("🏆 Best Guess")
                        best_guesses = result.get("best_guesses", [])
                        if best_guesses:
                            for guess in best_guesses:
                                st.markdown(f"### **{guess}**")
                        else:
                            st.write("No confident text match found.")
                            
                        st.divider()
                        st.subheader("📊 Top Keywords")
                        keywords = result.get("common_keywords", [])
                        if keywords:
                            for k in keywords:
                                st.write(f"- **{k['word']}**: {k['count']}")
                    
                    with col2:
                        st.subheader("🖼️ Visual Matches")
                        matches = result.get("visual_matches", [])
                        if matches:
                            grid_cols = st.columns(3)
                            for idx, match in enumerate(matches):
                                with grid_cols[idx % 3]:
                                    if match.get('thumbnail'):
                                        st.image(match['thumbnail'], width='stretch')
                                    st.markdown(f"[{match.get('title', 'Link')}]({match.get('link', '#')})")
                                    st.caption(match.get('source', 'Unknown'))
                        else:
                            st.write("No visual matches returned.")

                else:
                    st.error(f"Server Error: {response.text}")

            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend. Is `server.py` running?")
            except Exception as e:
                st.error(f"Error: {e}")
