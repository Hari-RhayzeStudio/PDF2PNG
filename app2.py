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

# --- Caching ---
# This function is cached and will only run when the input changes.
@st.cache_data(max_entries=5) 
def perform_conversion(pdf_bytes, dpi):
    """
    Converts PDF bytes into a list of image bytes and a zip file.
    This function is cached to prevent re-running.
    """
    try:
        # --- IMPORTANT: Poppler Path (if needed) ---
        # If Poppler is NOT in your system's PATH, you must tell
        # pdf2image where to find it. Uncomment the line below.
        # poppler_path = r"C:\ProgramData\chocolatey\lib\poppler\bin"
        # images = convert_from_bytes(pdf_bytes, dpi=dpi, poppler_path=poppler_path)
        
        # If Poppler IS in your system PATH:
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
        
        image_bytes_list = []
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, image in enumerate(images):
                img_buffer = io.BytesIO()
                image.save(img_buffer, format="PNG")
                img_bytes = img_buffer.getvalue()
                
                image_bytes_list.append(img_bytes)
                zf.writestr(f"page_{i + 1:03d}.png", img_bytes)
        
        return image_bytes_list, zip_buffer.getvalue()

    except Exception as e:
        return None, str(e) # Return the error

# --- Sidebar ---
with st.sidebar:
    st.header("Upload & Settings")
    uploaded_file = st.file_uploader(
        "Select a PDF file", 
        type=["pdf"]
    )
    
    load_dotenv() 
    dpi_options = [150, 300, 600]
    try:
        default_dpi = int(os.getenv("OUTPUT_DPI", 300))
        default_index = dpi_options.index(default_dpi)
    except ValueError:
        default_index = 1 
    
    dpi = st.selectbox(
        "Select Image Resolution (DPI)",
        options=dpi_options,
        index=default_index,
        help="Higher DPI means higher quality and longer conversion time."
    )
    
    st.markdown("---")
    st.write("This app converts your PDF into high-quality PNG images.")

# --- Main Page ---
st.title("📄 PDF to High-Quality PNG Converter")

if uploaded_file is not None:
    pdf_filename = os.path.splitext(uploaded_file.name)[0]
    
    # Use the file's unique ID to manage session state
    file_id = uploaded_file.file_id
    if "last_file_id" not in st.session_state or st.session_state.last_file_id != file_id or st.session_state.last_dpi != dpi:
        with st.spinner(f"Converting '{uploaded_file.name}' at {dpi} DPI..."):
            image_bytes_list, zip_data = perform_conversion(uploaded_file.getvalue(), dpi)
            
            # Store results in session state
            st.session_state.image_bytes_list = image_bytes_list
            st.session_state.zip_data = zip_data
            st.session_state.last_file_id = file_id
            st.session_state.last_dpi = dpi
            st.session_state.pdf_filename = pdf_filename
            
            if isinstance(image_bytes_list, list):
                st.success(f"✅ Conversion successful! Found {len(image_bytes_list)} pages.")
            else:
                st.error(f"❌ A conversion error occurred: {zip_data}")
                st.session_state.clear() # Clear state on error

    # --- Display Results from Session State ---
    if "image_bytes_list" in st.session_state and isinstance(st.session_state.image_bytes_list, list):
        
        image_bytes_list = st.session_state.image_bytes_list
        zip_data = st.session_state.zip_data
        pdf_filename = st.session_state.pdf_filename

        # --- "Download All" Button ---
        st.download_button(
            label=f"Download All Pages as .ZIP",
            data=zip_data,
            file_name=f"{pdf_filename}_all_pages.zip",
            mime="application/zip",
            use_container_width=True,
            on_click="ignore"  # <-- **THE FIX IS HERE**
        )
        
        st.divider()

        # --- Individual Image Display and Download ---
        st.subheader("Individual Page Downloads")
        cols = st.columns(3) 

        for i, img_bytes in enumerate(image_bytes_list):
            page_name = f"{pdf_filename}_page_{i + 1:03d}.png"
            
            with cols[i % 3]:
                st.image(
                    img_bytes,
                    caption=f"Page {i + 1}",
                    use_column_width=True
                )
                
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    with st.popover("Enlarge 🔎", use_container_width=True):
                        st.image(img_bytes, use_column_width=True)
                
                with btn_col2:
                    st.download_button(
                        label="Download ⬇️",
                        data=img_bytes,
                        file_name=page_name,
                        mime="image/png",
                        use_container_width=True,
                        key=f"download_{i}",
                        on_click="ignore"  # <-- **AND THE FIX IS HERE**
                    )
                st.markdown("---")
else:
    # Clear the session state if no file is uploaded
    if "last_file_id" in st.session_state:
        st.session_state.clear()
    st.info("Please upload a PDF file using the sidebar on the left to begin.")