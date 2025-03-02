import streamlit as st
import os
import subprocess

# Page title
# st.set_page_config(page_title="Postman to JMeter Converter", layout="wide")

# Page header
st.markdown("# 📤 Postman to JMeter Converter")
st.write("Upload a Postman collection JSON file to convert it into a JMeter `.jmx` file.")

# File uploader
uploaded_file = st.file_uploader("Upload Postman Collection (JSON 2.1 format)", type="json")

# Get absolute path of the script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JM_SCRIPT_PATH = os.path.join(SCRIPT_DIR, "../scripts/postman_to_jmeter.py")


# Ensure uploads directory exists
UPLOAD_FOLDER = "uploads"
UPLOAD_FOLDER = os.path.join(SCRIPT_DIR, "../tempScriptsOutput")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if uploaded_file is not None:
    # Save uploaded file
    file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"File uploaded successfully: {uploaded_file.name}")

    # Conversion button
    if st.button("Convert to JMeter"):
        output_file = os.path.splitext(file_path)[0] + ".jmx"

        # Run the script from the "scripts" folder
        command = ["python", JM_SCRIPT_PATH, file_path]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            st.success(f"Conversion successful! JMX file created: {output_file}")

            with open(output_file, "rb") as f:
                st.download_button(
                    label="Download JMX File",
                    data=f,
                    file_name=os.path.basename(output_file),
                    mime="application/xml"
                )
        else:
            st.error("Conversion failed. Please check the Postman JSON format.")
            st.text_area("Error Log:", result.stderr)
