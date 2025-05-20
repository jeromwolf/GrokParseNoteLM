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
    
    # The output_image_dir should already be created by the caller

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

def summarize_with_upstage(text_content, image_paths=None):
    """Sends text to Upstage API for summarization.
    
    Args:
        text_content (str): Extracted text from the PDF
        image_paths (list, optional): List of paths to extracted images. Not used in summarization for now.
    
    Returns:
        str: Summary of the text content
    """
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        return "Error: UPSTAGE_API_KEY not found in .env file"

    # Set up headers for the API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    url = "https://api.upstage.ai/v1/chat/completions"
    
    # Log that we're only using text for summarization
    if image_paths:
        print(f"Note: Found {len(image_paths)} images. Images will be saved but not included in summarization for now.")
    
    # Prepare the prompt in Korean
    prompt = f"""다음 문서를 한국어로 자세히 요약해주세요. 
    - 주요 포인트, 핵심 주장, 중요한 세부 사항을 포함해주세요.
    - 명확하고 구조화된 형식으로 작성해주세요.
    - 문서에 이미지가 있는 경우 별도로 추출되어 저장되었습니다.
    
    문서 내용:
    {text_content}
    """

    payload = {
        "model": "solar-1-mini-chat",
        "messages": [
            {
                "role": "system",
                "content": "당신은 문서를 명확하고 구조화된 형식으로 요약해주는 도우미입니다. 한국어로 답변해주세요."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 1000,  # 필요에 따라 조정 가능
        "temperature": 0.3,  # 더 일관된 출력을 위한 낮은 온도
        "stream": False
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

def process_pdf(pdf_path):
    """Process a PDF file: extract text and images, then summarize the text."""
    print(f"Processing PDF: {pdf_path}...")
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Create a timestamped subdirectory for this specific PDF run
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
    pdf_specific_output_dir = os.path.join("output", f"{pdf_basename}_{timestamp}")
    
    # Create the specific output directory for this run
    os.makedirs(pdf_specific_output_dir, exist_ok=True)
    
    # Create an images subdirectory for extracted images
    images_dir = os.path.join(pdf_specific_output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    try:
        # Extract text and images
        print(f"Images will be temporarily stored in: {pdf_specific_output_dir}")
        text_content, image_paths = extract_text_and_images_from_pdf(pdf_path, pdf_specific_output_dir)
        
        if not text_content.strip():
            print("Warning: No text content was extracted from the PDF.")
            return "No text content found in the PDF."
            
        # Summarize only the text content
        print("Summarizing text content with Upstage Solar API...")
        summary = summarize_with_upstage(text_content, image_paths)  # Passing image_paths for logging only
        
        # Print the summary
        print("\n--- Summary ---")
        print(summary)
        print("----------------")
        
        # Save the summary to a file
        summary_file = os.path.join(pdf_specific_output_dir, "summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"Summary saved to: {summary_file}")
        
        return summary
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Error processing PDF: {e}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize a PDF document using Upstage Solar API.")
    parser.add_argument("pdf_file", help="Path to the PDF file to summarize.")
    args = parser.parse_args()

    if not os.path.exists(args.pdf_file):
        print(f"Error: PDF file not found at {args.pdf_file}")
        exit(1)

    process_pdf(args.pdf_file)
    print("Processing complete.")
