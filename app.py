import streamlit as st
from pdf2image import convert_from_bytes
from dotenv import load_dotenv
import os
import io
import zipfile

# --- Configuration and Page Setup ---
st.set_page_config(
    page_title="PDF to PNG Converter",
    page_icon="📄",
    layout="wide"
)

# --- Sidebar ---
# All elements inside this 'with' block will appear in the sidebar
with st.sidebar:
    st.header("Upload Your PDF")
    
    # 1. File Uploader is now in the sidebar
    uploaded_file = st.file_uploader(
        "Select a PDF file", 
        type=["pdf"]
    )
    
    st.markdown("---")
    st.write("This app converts all pages of your PDF into high-quality PNG images.")
    
# --- Main Page ---
st.title("📄 PDF to High-Quality PNG Converter")

# Load DPI from .env or default to 300
load_dotenv()
DPI = int(os.getenv("OUTPUT_DPI", 300))

# --- IMPORTANT: Poppler Path (if needed) ---
# If Poppler is NOT in your system's PATH, you must tell
# pdf2image where to find it. Uncomment the line below and
# add the path to your Poppler 'bin' folder.
# poppler_path = r"C:\ProgramData\chocolatey\lib\poppler\bin"
# --- ---

# Proceed only if a file has been uploaded in the sidebar
if uploaded_file is not None:
    # Get the filename (for the zip file)
    pdf_filename = os.path.splitext(uploaded_file.name)[0]

    # Show a "processing" message while it works
    with st.spinner(f"Converting '{uploaded_file.name}' at {DPI} DPI..."):
        
        try:
            # 1. Read the uploaded file's bytes
            pdf_bytes = uploaded_file.getvalue()

            # 2. Convert PDF from bytes into a list of PIL Images
            # If you set 'poppler_path' above, add it here:
            # images = convert_from_bytes(pdf_bytes, dpi=DPI, poppler_path=poppler_path)
            
            # If Poppler is in your system PATH:
            images = convert_from_bytes(pdf_bytes, dpi=DPI)

            # 3. Create an in-memory ZIP file to hold all images
            zip_buffer = io.BytesIO()
            
            # A list to hold all our image bytes for individual display
            image_bytes_list = []

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, image in enumerate(images):
                    # Create a byte buffer for each individual image
                    img_buffer = io.BytesIO()
                    image.save(img_buffer, format="PNG")
                    img_bytes = img_buffer.getvalue()
                    
                    # Add this image's bytes to our list
                    image_bytes_list.append(img_bytes)
                    
                    # Add this image to the ZIP file
                    zf.writestr(f"{pdf_filename}_page_{i + 1:03d}.png", img_bytes)

            st.success(f"✅ Conversion successful! Found {len(images)} pages.")
            st.balloons()

            # --- "Download All" Button ---
            st.download_button(
                label=f"Download All Pages as .ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"{pdf_filename}_all_pages.zip",
                mime="application/zip",
                use_container_width=True
            )
            
            st.divider()

            # --- Individual Image Display and Download ---
            st.subheader("Individual Page Downloads")
            
            # Create a grid of 3 columns
            cols = st.columns(3) 

            for i, img_bytes in enumerate(image_bytes_list):
                page_name = f"{pdf_filename}_page_{i + 1:03d}.png"
                
                # Place each image and its button in the next available column
                with cols[i % 3]:
                    st.image(img_bytes, caption=f"Page {i + 1}")
                    
                    st.download_button(
                        label=f"Download Page {i + 1}",
                        data=img_bytes,
                        file_name=page_name,
                        mime="image/png",
                        use_container_width=True
                    )
                    st.markdown("---") # Visual separator

        except Exception as e:
            st.error(f"❌ An error occurred during conversion.")
            st.error(f"This is often caused by Poppler not being installed or not being in your system's PATH.")
            st.exception(e)

else:
    # This message shows in the main area when no file is uploaded
    st.info("Please upload a PDF file using the sidebar on the left to begin.")