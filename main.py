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
from typing import List, Tuple, Optional
from pathlib import Path

# Try to import llama-cpp-python, but make it optional
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False

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

class ModelHandler:
    """Base class for model handlers."""
    def summarize(self, text: str, image_paths: List[str] = None) -> str:
        raise NotImplementedError("Subclasses must implement this method")


class UpstageHandler(ModelHandler):
    """Handler for Upstage Solar API."""
    def __init__(self):
        if not UPSTAGE_API_KEY:
            raise ValueError("UPSTAGE_API_KEY is not set in .env file")
        
        self.headers = {
            "Authorization": f"Bearer {UPSTAGE_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def summarize(self, text: str, image_paths: List[str] = None) -> str:
        """Summarize text using Upstage Solar API."""
        if image_paths:
            print(f"Note: Found {len(image_paths)} images. Images will be saved but not included in summarization for now.")
        
        prompt = f"""다음 문서를 한국어로 자세히 요약해주세요. 
        - 주요 포인트, 핵심 주장, 중요한 세부 사항을 포함해주세요.
        - 명확하고 구조화된 형식으로 작성해주세요.
        - 문서에 이미지가 있는 경우 별도로 추출되어 저장되었습니다.
        
        문서 내용:
        {text}
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
            "max_tokens": 1000,
            "temperature": 0.3,
            "stream": False
        }

        try:
            response = requests.post(
                "https://api.upstage.ai/v1/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"API 요청 중 오류가 발생했습니다: {str(e)}"


class LlamaHandler(ModelHandler):
    """Handler for local Llama model."""
    def __init__(self, model_path: str = None):
        if not LLAMA_AVAILABLE:
            raise ImportError("llama-cpp-python is not installed. Please install it with: pip install llama-cpp-python")
        
        # Default model path if not provided
        self.model_path = model_path or os.path.expanduser("~/.cache/llama_models/llama-2-7b-chat.Q4_K_M.gguf")
        
        # Download model if it doesn't exist
        if not os.path.exists(self.model_path):
            print(f"Model not found at {self.model_path}")
            print("Please download the model first or specify the correct path with --model-path")
            print("Example model: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf")
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        
        # Initialize Llama model
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=2048,  # Context window
            n_threads=4   # Number of CPU threads to use
        )
    
    def summarize(self, text: str, image_paths: List[str] = None) -> str:
        """Summarize text using local Llama model."""
        if image_paths:
            print(f"Note: Found {len(image_paths)} images. Image analysis is not yet implemented for Llama.")
        
        prompt = f"""[INST] <<SYS>>
        당신은 문서를 명확하고 구조화된 형식으로 요약해주는 도우미입니다. 한국어로 답변해주세요.
        <</SYS>>
        
        다음 문서를 한국어로 자세히 요약해주세요. 주요 포인트, 핵심 주장, 중요한 세부 사항을 포함해주세요.
        
        문서 내용:
        {text}
        [/INST]"""
        
        try:
            output = self.llm(
                prompt,
                max_tokens=1000,
                temperature=0.3,
                stop=["</s>", "[INST]"]
            )
            return output["choices"][0]["text"]
        except Exception as e:
            return f"Llama 모델 요약 중 오류가 발생했습니다: {str(e)}"


# --- Main Execution ---

def process_pdf(pdf_path: str, model_type: str = "upstage", model_path: str = None) -> str:
    """
    Process a PDF file: extract text and images, then summarize the text.
    
    Args:
        pdf_path: Path to the PDF file
        model_type: Type of model to use ('upstage' or 'llama')
        model_path: Path to the Llama model (only used when model_type is 'llama')
    """
    print(f"Processing PDF: {pdf_path}")
    print(f"Using model: {model_type.upper()}")
    
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
        # Initialize the appropriate model handler
        if model_type.lower() == "llama":
            model = LlamaHandler(model_path)
            print("Using local Llama model for summarization")
        else:  # Default to Upstage
            model = UpstageHandler()
            print("Using Upstage Solar API for summarization")
        
        # Extract text and images
        print(f"Extracting text and images from PDF...")
        text_content, image_paths = extract_text_and_images_from_pdf(pdf_path, images_dir)
        
        if not text_content.strip():
            error_msg = "Warning: No text content was extracted from the PDF."
            print(error_msg)
            return error_msg
        
        # Summarize the text content
        print("\nGenerating summary...")
        summary = model.summarize(text_content, image_paths)
        
        # Print the summary
        print("\n--- Summary ---")
        print(summary)
        print("----------------")
        
        # Save the summary to a file
        summary_file = os.path.join(pdf_specific_output_dir, "summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"\nSummary saved to: {summary_file}")
        
        # Save model info
        with open(os.path.join(pdf_specific_output_dir, "model_info.txt"), 'w') as f:
            f.write(f"Model: {model_type.upper()}\n")
            if model_type.lower() == "llama":
                f.write(f"Model path: {model_path or 'default'}\n")
        
        return summary
    
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        print(f"\n{error_msg}")
        return error_msg

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize a PDF document using different AI models.")
    parser.add_argument("pdf_file", help="Path to the PDF file to summarize.")
    parser.add_argument(
        "--model", 
        type=str, 
        choices=["upstage", "llama"], 
        default="upstage",
        help="Model to use for summarization (default: upstage)"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Path to the Llama model file (only used when --model=llama)"
    )
    
    args = parser.parse_args()

    if not os.path.exists(args.pdf_file):
        print(f"Error: PDF file not found at {args.pdf_file}")
        exit(1)
    
    print("=" * 40)
    print(f"PDF Document: {os.path.basename(args.pdf_file)}")
    print(f"Model: {args.model.upper()}")
    if args.model == "llama" and args.model_path:
        print(f"Custom model path: {args.model_path}")
    print("=" * 40 + "\n")

    process_pdf(args.pdf_file, args.model, args.model_path)
    print("\nProcessing complete.")
