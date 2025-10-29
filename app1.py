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
    layout="centered"  # Centered layout often works well for single image viewers
)

# --- Caching ---
# Cached function for the heavy conversion work
@st.cache_data(max_entries=5)
def perform_conversion(pdf_bytes, dpi):
    """ Converts PDF bytes into a list of image bytes and a zip file. """
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
        type=["pdf"],
        # Use on_change to reset page index when a new file is uploaded
        on_change=lambda: st.session_state.update(current_page_index=0)
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
        help="Higher DPI = higher quality, larger size, longer conversion.",
        # Use on_change to reset page index when DPI changes
        on_change=lambda: st.session_state.update(current_page_index=0)
    )

    st.markdown("---")
    st.write("Convert PDF pages to PNG.")
    
    # Add the "Download All" button to the sidebar for convenience
    if "zip_data" in st.session_state and st.session_state.zip_data:
        st.download_button(
            label=f"Download All Pages (.ZIP)",
            data=st.session_state.zip_data,
            file_name=f"{st.session_state.pdf_filename}_all_pages.zip",
            mime="application/zip",
            use_container_width=True,
            on_click="ignore"
        )

# --- Main Page ---
st.title("📄 PDF Page Viewer & Downloader")

# Initialize session state for page index if it doesn't exist
if "current_page_index" not in st.session_state:
    st.session_state.current_page_index = 0

if uploaded_file is not None:
    pdf_filename = os.path.splitext(uploaded_file.name)[0]
    file_id = uploaded_file.file_id

    # Check if we need to run conversion (new file or changed DPI)
    if "last_file_id" not in st.session_state or st.session_state.last_file_id != file_id or st.session_state.last_dpi != dpi:
        with st.spinner(f"Converting '{uploaded_file.name}' at {dpi} DPI..."):
            image_bytes_list, zip_data = perform_conversion(uploaded_file.getvalue(), dpi)

            # Store results in session state
            st.session_state.image_bytes_list = image_bytes_list
            st.session_state.zip_data = zip_data
            st.session_state.last_file_id = file_id
            st.session_state.last_dpi = dpi
            st.session_state.pdf_filename = pdf_filename
            st.session_state.total_pages = len(image_bytes_list) if isinstance(image_bytes_list, list) else 0
            # Reset index on new conversion
            st.session_state.current_page_index = 0 
            
            if isinstance(image_bytes_list, list):
                st.success(f"✅ Conversion successful! Found {st.session_state.total_pages} pages.")
            else:
                st.error(f"❌ A conversion error occurred: {zip_data}")
                st.session_state.clear() # Clear state on error

    # --- Display Current Page and Controls ---
    if "image_bytes_list" in st.session_state and isinstance(st.session_state.image_bytes_list, list) and st.session_state.total_pages > 0:
        
        # Get current page data from session state
        current_index = st.session_state.current_page_index
        total_pages = st.session_state.total_pages
        current_image_bytes = st.session_state.image_bytes_list[current_index]
        current_page_name = f"{st.session_state.pdf_filename}_page_{current_index + 1:03d}.png"

        # --- Image Display ---
        st.image(
            current_image_bytes,
            caption=f"Page {current_index + 1} of {total_pages}",
            use_column_width=True # Make image fit the container width
        )

        # --- Navigation Buttons ---
        col1, col2, col3 = st.columns([1, 1, 1]) # Adjust ratios as needed

        with col1:
            # Disable Previous button if on the first page
            if st.button("⬅️ Previous", use_container_width=True, disabled=(current_index == 0)):
                st.session_state.current_page_index -= 1
                st.rerun() # Rerun to update the displayed image

        with col2:
             # Add page number display
             st.markdown(f"<p style='text-align: center; font-size: 1.1em;'>Page {current_index + 1} / {total_pages}</p>", unsafe_allow_html=True)

        with col3:
            # Disable Next button if on the last page
            if st.button("Next ➡️", use_container_width=True, disabled=(current_index == total_pages - 1)):
                st.session_state.current_page_index += 1
                st.rerun() # Rerun to update the displayed image

        # --- Download Button for Current Image ---
        st.download_button(
            label=f"⬇️ Download Page {current_index + 1}",
            data=current_image_bytes,
            file_name=current_page_name,
            mime="image/png",
            use_container_width=True,
            key=f"download_page_{current_index}", # Key changes with page
            on_click="ignore" # Prevent rerun on download
        )

else:
    # Clear session state if no file is present
    if "last_file_id" in st.session_state:
        st.session_state.clear()
        st.session_state.current_page_index = 0 # Reset index explicitly
    st.info("👋 Upload a PDF file using the sidebar to begin.")