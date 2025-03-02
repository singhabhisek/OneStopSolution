import streamlit as st
import os
import subprocess
import time

# Define paths
UPLOAD_FOLDER = "uploads"
DOWNLOAD_FOLDER = "downloads"

# Get absolute path of the script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(SCRIPT_DIR, "../scripts/har2jmxengine.py")

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# UI Elements
st.title("HAR to JMeter Converter")
st.write("Upload a HAR file, specify static file extensions to exclude, and convert it to a JMeter test plan.")

# File uploader
uploaded_file = st.file_uploader("Upload HAR file", type=["har"])

# Static file exclusions (default values)
default_static_extensions = "js;css;png;jpg;gif;svg;woff;woff2;ttf;ico"
exclude_extensions = st.text_input(
    "Exclude Static Extensions (semicolon-separated)", value=default_static_extensions
)

# Process Button
if st.button("Convert to JMeter"):
    if uploaded_file:
        # Save the uploaded file
        file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Output file path
        # output_jmx = os.path.join(DOWNLOAD_FOLDER, "converted.jmx")
        har_filename = os.path.splitext(uploaded_file.name)[0]  # Get filename without extension
        output_jmx = os.path.join(DOWNLOAD_FOLDER, f"{har_filename}_converted.jmx")

        # Run the conversion script
        command = ["python", SCRIPT_PATH, file_path, exclude_extensions, output_jmx]
        process = subprocess.run(command, capture_output=True, text=True)

        if process.returncode == 0:
            st.success("Conversion Successful!")
            # Show download button
            with open(output_jmx, "rb") as f:
                st.download_button(
                    label="Download JMeter Script",
                    data=f,
                    file_name="converted.jmx",
                    mime="application/xml",
                    key="download_button",
                )
        else:
            st.error("Conversion Failed!")
            st.text_area("Error Log", process.stderr)
    else:
        st.warning("Please upload a HAR file first.")
