import streamlit as st
import os
import subprocess

# Set page title
# st.set_page_config(page_title="Postman to LoadRunner Converter", layout="wide")

# Page Header
st.markdown("# 🚀 Postman to LoadRunner Converter")
st.write("Upload a Postman collection JSON file to convert it into a LoadRunner script.")

# File Uploader
uploaded_file = st.file_uploader("Upload Postman Collection (JSON 2.1 format)", type="json")

# Get absolute path of the script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JM_SCRIPT_PATH = os.path.join(SCRIPT_DIR, "../scripts/postman2lr_engine.py")


# Ensure uploads directory exists
# UPLOAD_FOLDER = "uploads"
UPLOAD_FOLDER = os.path.join(SCRIPT_DIR, "../tempScriptsOutput")
# Ensure upload directory exists
# UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if uploaded_file is not None:
    # Save uploaded file
    file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"File uploaded successfully: {uploaded_file.name}")

    # Conversion Button
    if st.button("Convert to LoadRunner"):
        output_file = os.path.splitext(file_path)[0] + ".lr"

        # Run the LoadRunner conversion script
        command = ["python", JM_SCRIPT_PATH, file_path, UPLOAD_FOLDER]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            st.success(f"Conversion successful! LoadRunner file created: {os.path.basename(output_file)}")

            # Provide a download button for the user
            with open(output_file, "rb") as f:
                st.download_button(
                    label="Download LoadRunner Script",
                    data=f,
                    file_name=os.path.basename(output_file),
                    mime="text/plain"
                )
        else:
            st.error("Conversion failed. Please check the Postman JSON format.")
            st.text_area("Error Log:", result.stderr)
