import os
import fitz  # PyMuPDF
import base64
import requests
import argparse
import shutil
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import datetime

# Load environment variables from .env file
load_dotenv()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
UPSTAGE_API_URL = "https://api.upstage.ai/v1/chat/completions"

# --- Helper Functions ---

def get_image_mime_type(image_path):
    """Determine image MIME type from file extension."""
    ext = os.path.splitext(image_path)[1].lower()
    if ext == ".png":
        return "image/png"
    elif ext in [".jpg", ".jpeg"]:
        return "image/jpeg"
    elif ext == ".gif":
        return "image/gif"
    elif ext == ".bmp":
        return "image/bmp"
    # Add more types if needed
    return "application/octet-stream" # Default if unknown

def image_to_base64(image_path):
    """Convert an image file to a base64 encoded string."""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        mime_type = get_image_mime_type(image_path)
        return f"data:{mime_type};base64,{encoded_string}"
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

def extract_text_and_images_from_pdf(pdf_path, output_image_dir):
    """Extracts text and images from a PDF file into the specified directory."""
    doc = fitz.open(pdf_path)
    full_text = ""
    image_paths = []

    # Ensure the specific output directory for this PDF exists
    if not os.path.exists(output_image_dir):
        os.makedirs(output_image_dir)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        full_text += page.get_text() + "\n\n"
        
        image_list = page.get_images(full=True)
        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"page{page_num+1}_img{img_index+1}.{image_ext}"
            image_save_path = os.path.join(output_image_dir, image_filename)
            
            with open(image_save_path, "wb") as img_file:
                img_file.write(image_bytes)
            image_paths.append(image_save_path)
            
    doc.close()
    return full_text, image_paths

def summarize_with_upstage(text_content, image_base64_list):
    """Sends text and image data to Upstage API for summarization."""
    if not UPSTAGE_API_KEY:
        return "Error: UPSTAGE_API_KEY not found. Please set it in your .env file."

    headers = {
        "Authorization": f"Bearer {UPSTAGE_API_KEY}",
        "Content-Type": "application/json"
    }

    messages_content = []
    # Add text part
    messages_content.append({
        "type": "text",
        "text": text_content
    })

    # Add image parts
    for img_b64 in image_base64_list:
        if img_b64:
            messages_content.append({
                "type": "image_url",
                "image_url": {"url": img_b64}
            })

    payload = {
        "model": "solar-1-mini-chat", # Or another model like solar-1-mini-chat-240410
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Summarize the provided document which includes text and images. Integrate information from both text and images in your summary."
            },
            {
                "role": "user",
                "content": messages_content
            }
        ],
        "stream": False # Set to True if you want streaming responses
    }

    try:
        response = requests.post(UPSTAGE_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        summary = response.json()["choices"][0]["message"]["content"]
        return summary
    except requests.exceptions.RequestException as e:
        return f"API request failed: {e}\nResponse: {response.text if 'response' in locals() else 'No response'}"
    except (KeyError, IndexError) as e:
        return f"Failed to parse API response: {e}\nResponse: {response.json() if 'response' in locals() and response.content else 'No JSON content'}"


# --- Main Execution ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize a PDF document using Upstage Solar API.")
    parser.add_argument("pdf_file", help="Path to the PDF file to summarize.")
    args = parser.parse_args()

    if not os.path.exists(args.pdf_file):
        print(f"Error: PDF file not found at {args.pdf_file}")
        exit(1)

    pdf_basename = os.path.splitext(os.path.basename(args.pdf_file))[0]
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Define the main output directory
    main_output_folder = "output"
    # Define the specific output directory for this PDF run
    pdf_specific_output_dir = os.path.join(main_output_folder, f"{pdf_basename}_{timestamp}")

    # Create the main output folder if it doesn't exist
    if not os.path.exists(main_output_folder):
        os.makedirs(main_output_folder)

    print(f"Processing PDF: {args.pdf_file}...")
    print(f"Images will be temporarily stored in: {pdf_specific_output_dir}")
    
    try:
        extracted_text, extracted_image_paths = extract_text_and_images_from_pdf(args.pdf_file, pdf_specific_output_dir)
        print(f"Extracted {len(extracted_image_paths)} images to {pdf_specific_output_dir}")

        image_base64_data = []
        if extracted_image_paths:
            print("Converting images to base64...")
            for img_path in extracted_image_paths:
                b64_img = image_to_base64(img_path)
                if b64_img:
                    image_base64_data.append(b64_img)
        
        print("Summarizing with Upstage Solar API...")
        summary_result = summarize_with_upstage(extracted_text, image_base64_data)

        print("\n--- Summary ---")
        print(summary_result)
        print("---------------")

    finally:
        # Clean up temporary image directory for this specific PDF run
        if os.path.exists(pdf_specific_output_dir):
            print(f"Cleaning up temporary image directory: {pdf_specific_output_dir}")
            shutil.rmtree(pdf_specific_output_dir)

    print("Processing complete.")
