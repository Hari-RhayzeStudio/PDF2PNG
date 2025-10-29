import os
import sys
from dotenv import load_dotenv
from pdf2image import convert_from_path

def convert_pdf_to_high_quality_images():
    """
    Loads configuration from a .env file to convert a PDF
    into high-quality PNG images.
    """
    # 1. Load environment variables from .env file
    load_dotenv()

    # 2. Get configuration
    pdf_path = os.getenv("PDF_FILE_PATH")
    # Default to 300 DPI if not specified
    dpi = int(os.getenv("OUTPUT_DPI", 300))

    # 3. Validate PDF path
    if not pdf_path or not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found at path: {pdf_path}")
        print("Please check your PDF_FILE_PATH in the .env file.")
        return

    # 4. Define Output Paths
    # Get the base filename (e.g., 'document' from 'C:/path/document.pdf')
    pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Create an output directory named after the PDF
    output_dir = os.path.join(os.path.dirname(__file__), "output_images", pdf_filename)

    # 5. Create Output Directory
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"📂 Output directory created: {output_dir}")
    except Exception as e:
        print(f"❌ Error creating directory: {e}")
        return

    print(f"🚀 Starting conversion for '{pdf_filename}' at {dpi} DPI...")

    try:
        # 6. Perform the conversion
        # This is the core function that calls Poppler
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            fmt='png',
            thread_count=4  # Use multiple CPU cores for speed
        )

        # 7. Save all the images
        for i, image in enumerate(images):
            # Naming convention: pagename_001.png, pagename_002.png, etc.
            image_name = f"{pdf_filename}_page_{i + 1:03d}.png"
            output_path = os.path.join(output_dir, image_name)
            
            # Save the image
            image.save(output_path, 'PNG')
            print(f"  -> Saved page {i + 1} as: {image_name}")

        print(f"\n✅ Conversion successful! {len(images)} images saved to {output_dir}")

    except Exception as e:
        print(f"\n❌ A conversion error occurred.")
        print("   This is often caused by Poppler not being installed or not being in your system's PATH.")
        print(f"   Error details: {e}")

# --- Run the script ---
if __name__ == "__main__":
    convert_pdf_to_high_quality_images()