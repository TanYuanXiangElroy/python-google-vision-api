import streamlit as st
import requests
from PIL import Image
import io

# backend URL
API_URL = "http://localhost:5000/scan"

st.set_page_config(page_title="Poke-Dex Vision", page_icon="🔍")

st.title("🔍 Google Vision Image Search")
st.write("Identify objects using Google Cloud Vision API")

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
        with st.spinner("Analyzing..."):
            try:
                # Prepare the file for the request
                # Streamlit file objects act like open files
                files = {"image": image_file.getvalue()}
                
                response = requests.post(API_URL, files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Display Results
                    st.success("Analysis Complete!")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🏆 Best Guesses")
                        best_guesses = data.get("best_guesses", [])
                        if best_guesses:
                            for guess in best_guesses[:5]:
                                st.write(f"- **{guess}**")
                        else:
                            # Fallback for older server version or empty list
                            st.write(f"- {data.get('best_guess', 'N/A')}")
                            
                    with col2:
                        st.subheader("🏷️ Tags (Web Entities)")
                        google_sees = data.get("google_sees", [])
                        if google_sees:
                            for item in google_sees[:10]:
                                st.write(f"- {item['description']} ({item['score']})")
                        else:
                            st.write("No tags found.")
                            
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend server. Is it running?")
            except Exception as e:
                st.error(f"An error occurred: {e}")
