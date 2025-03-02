import streamlit as st
import os
import subprocess
import tempfile

# Streamlit app configuration
# st.set_page_config(page_title="Fiddler to JMeter", layout="wide")

st.title("Fiddler to JMeter Converter")

# Default values
DEFAULT_ALLOWED_HOSTS = "www.demoblaze.com;api.demoblaze.com;www.blazedemo.com"
DEFAULT_ALLOWED_STATUS_CODES = "200;302"
DEFAULT_SKIP_FILE_TYPES = ".jpg;.jpeg;.png;.gif;.bmp;.ico;.css;.js;.woff;.woff2;.ttf;.otf;.svg"

# Get absolute path of the script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(SCRIPT_DIR, "scripts/fiddler2jm_engine.py")

# File upload section
uploaded_file = st.file_uploader("Upload your SAZ file", type=["saz"])

# Input fields for user-defined filters
allowed_status_codes = st.text_input("Allowed Status Codes (semicolon-separated)", "200;302")
skip_file_extensions = st.text_input("Skip File Extensions (semicolon-separated)", ".jpg;.jpeg;.png;.gif;.bmp;.ico;.css;.js;.woff;.woff2;.ttf;.otf;.svg")
included_domains = st.text_input("Included Domains (semicolon-separated)", "www.demoblaze.com;api.demoblaze.com;www.blazedemo.com")

if uploaded_file and st.button("Convert to JMeter Test Plan"):
    with tempfile.TemporaryDirectory() as temp_dir:
        saz_path = os.path.join(temp_dir, uploaded_file.name)
        
        # Save uploaded SAZ file
        with open(saz_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Prepare arguments
        allowed_status_codes_list = allowed_status_codes.split(";")
        skip_file_types_list = skip_file_extensions.split(";")
        included_domains_list = included_domains.split(";")

        # Construct command to call the engine
        command = [
            "python", SCRIPT_PATH, saz_path,
            ";".join(included_domains_list), ";".join(skip_file_types_list), ";".join(allowed_status_codes_list)
        ]

        # Run the script
        process = subprocess.run(command, capture_output=True, text=True)

        if process.returncode == 0:
            jmx_file_path = saz_path.replace(".saz", ".jmx")
            with open(jmx_file_path, "rb") as jmx_file:
                st.download_button(
                    label="Download JMeter Test Plan",
                    data=jmx_file,
                    file_name=os.path.basename(jmx_file_path),
                    mime="application/xml"
                )
            st.success("JMeter test plan generated successfully!")
        else:
            st.error(f"Error occurred: {process.stderr}")

st.info("Upload a SAZ file, set filters, and convert it into a JMeter test plan.")
