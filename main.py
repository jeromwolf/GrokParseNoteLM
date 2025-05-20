import os
import argparse
import json
import base64
from datetime import datetime
from typing import List, Optional, Tuple
from dotenv import load_dotenv
from document_processor import extract_text_and_images_from_pdf  # 업스테이지 Document Parser 사용
from pymupdf_processor import extract_text_and_images_from_pdf as extract_with_pymupdf  # PyMuPDF 백업 방법
from model_handler import ModelHandler

# 환경 변수 로드
load_dotenv()

# --- Helper Functions ---

def get_image_mime_type(image_path: str) -> str:
    """이미지 파일의 MIME 타입을 반환합니다."""
    ext = os.path.splitext(image_path)[1].lower()
    if ext == ".png":
        return "image/png"
    elif ext in [".jpg", ".jpeg"]:
        return "image/jpeg"
    return "application/octet-stream"

def image_to_base64(image_path: str) -> str:
    """이미지 파일을 base64 문자열로 변환합니다."""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        mime_type = get_image_mime_type(image_path)
        return f"data:{mime_type};base64,{encoded_string}"
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None


    """Base class for model handlers."""
    def __init__(self, model_type, model_name=None):
        self.model_type = model_type
        self.model_name = model_name





    """Handler for Upstage Solar API."""
    def __init__(self):
        if not UPSTAGE_API_KEY:
            raise ValueError("UPSTAGE_API_KEY is not set in .env file")
        
        self.headers = {
            "Authorization": f"Bearer {UPSTAGE_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def generate_summary(self, text: str, image_paths: List[str] = None) -> str:
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



    """Handler for local Llama model using Ollama API."""
    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/generate"
        
        # Test if Ollama is running
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code != 200:
                raise ConnectionError("Ollama 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인해주세요.")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Ollama 서버에 연결할 수 없습니다: {str(e)}")
        
        # Check if the model is available
        available_models = [m["name"] for m in response.json().get("models", [])]
        if self.model_name not in available_models:
            print(f"경고: 모델 '{self.model_name}'이(가) 로컬에 없습니다. 사용 가능한 모델: {', '.join(available_models)}")
            print(f"다음 명령어로 모델을 다운로드할 수 있습니다: ollama pull {self.model_name}")
            self.model_name = available_models[0] if available_models else "llama3"
            print(f"기본 모델 '{self.model_name}'을(를) 사용합니다.")
    
    def generate_summary(self, text: str, image_paths: List[str] = None) -> str:
        """Summarize text using local Llama model via Ollama API."""
        if image_paths:
            print(f"Note: Found {len(image_paths)} images. Image analysis is not yet implemented for Llama.")
        
        # Simple prompt with Korean instruction
        prompt = f"""[INST] <<SYS>>
        당신은 문서를 명확하고 구조화된 형식으로 요약해주는 도우미입니다. 반드시 한국어로만 답변해주세요.
        <</SYS>>
        
        다음 문서를 한국어로 자세히 요약해주세요. 주요 포인트, 핵심 주장, 중요한 세부 사항을 포함해주세요.
        
        문서 내용:
        {text}
        
        한국어로 요약: [/INST]"""
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "max_tokens": 1000,
                        "stop": ["</s>", "[INST]", "<|eot_id|>"]
                    }
                }
            )
            response.raise_for_status()
            return response.json().get("response", "요약을 생성할 수 없었습니다.")
        except Exception as e:
            return f"Ollama API 요청 중 오류가 발생했습니다: {str(e)}"



    """Handler for OpenAI API."""
    def __init__(self, model_name: str = "text-davinci-003"):
        self.model_name = model_name
        self.api_url = "https://api.openai.com/v1/completions"
        self.headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def generate_summary(self, text: str, image_paths: List[str] = None) -> str:
        """Summarize text using OpenAI API."""
        if image_paths:
            print(f"Note: Found {len(image_paths)} images. Images will be saved but not included in summarization for now.")
        
        prompt = f"""Summarize the following text in Korean:
        
        {text}
        """
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": 1000,
            "temperature": 0.3,
            "stream": False
        }

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()["choices"][0]["text"]
        except Exception as e:
            return f"API 요청 중 오류가 발생했습니다: {str(e)}"



    """Handler for Gemini API."""
    def __init__(self, model_name: str = "llama"):
        self.model_name = model_name
        self.api_url = "https://api.gemini.ai/v1/completions"
        self.headers = {
            "Authorization": f"Bearer {GEMINI_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def generate_summary(self, text: str, image_paths: List[str] = None) -> str:
        """Summarize text using Gemini API."""
        if image_paths:
            print(f"Note: Found {len(image_paths)} images. Images will be saved but not included in summarization for now.")
        
        prompt = f"""Summarize the following text in Korean:
        
        {text}
        """
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": 1000,
            "temperature": 0.3,
            "stream": False
        }

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()["choices"][0]["text"]
        except Exception as e:
            return f"API 요청 중 오류가 발생했습니다: {str(e)}"


# --- Main Execution ---

# extract_text_and_images_from_pdf 함수는 document_processor.py에서 가져옴
# 업스테이지 Document Parser API를 사용하여 PDF에서 텍스트와 이미지를 추출

def process_pdf(pdf_path: str, model_type: str, output_dir: str = "output", model_name: Optional[str] = None, parser: str = "auto", language: str = "ko") -> str:
    """Process a PDF file and generate a summary using the specified model.
    
    Args:
        pdf_path: Path to the PDF file
        model_type: Type of model to use ('upstage', 'llama', 'openai', 'gemini')
        output_dir: Directory to save output files
        model_name: Specific model name/version to use
        
    Returns:
        Generated summary text
    """
    # Create output directory with timestamp and model name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    pdf_specific_output_dir = os.path.join(output_dir, f"{pdf_name}_{model_type.upper()}_{timestamp}")
    
    # 로그 디렉토리 생성
    os.makedirs(pdf_specific_output_dir, exist_ok=True)
    log_file = os.path.join(pdf_specific_output_dir, "process_log.txt")
    
    # 로그 함수 정의
    def log_message(message: str):
        print(message)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
    
    try:
        # 반드시 ModelHandler만 사용하도록 고정
        handler = ModelHandler(model_type, model_name, language)
        
        # Extract text and images from PDF
        log_message(f"PDF 파일 처리 시작: {os.path.basename(pdf_path)}")
        log_message(f"모델: {model_type.upper()}{' - ' + model_name if model_name else ''}")
        log_message(f"언어: {language}")
        log_message(f"파서 모드: {parser}")
        
        parser_used = ""  # 실제 사용된 파서 정보를 저장할 변수
        
        # 파서 선택 로직
        if parser == "pymupdf" or parser == "local":
            # PyMuPDF 직접 사용
            log_message("PyMuPDF 파서를 사용하여 PDF 처리 중...")
            text, image_paths = extract_with_pymupdf(pdf_path, pdf_specific_output_dir)
            parser_used = "PyMuPDF"  # 파서 정보 업데이트
        elif parser == "upstage" or parser == "api":
            # 업스테이지 API 직접 사용
            log_message("업스테이지 Document Parser API를 사용하여 PDF 처리 중...")
            try:
                text, image_paths = extract_text_and_images_from_pdf(pdf_path, pdf_specific_output_dir)
                parser_used = "Upstage Document Parser API"  # 파서 정보 업데이트
                if not text.strip():
                    log_message("⚠️ 경고: 업스테이지 API에서 텍스트가 추출되지 않았습니다.")
                    raise ValueError("업스테이지 API에서 텍스트가 추출되지 않았습니다.")
            except Exception as e:
                log_message(f"❌ 오류: 업스테이지 API 실패: {str(e)}")
                raise e  # 오류를 다시 발생시켜 자동 전환 없이 종료
        else:  # auto 모드 (기본값)
            # 먼저 업스테이지 API 시도, 실패 시 PyMuPDF로 자동 전환
            log_message("업스테이지 Document Parser API를 사용하여 PDF 처리 중... (실패 시 PyMuPDF로 자동 전환)")
            try:
                # 업스테이지 Document Parser API 시도
                text, image_paths = extract_text_and_images_from_pdf(pdf_path, pdf_specific_output_dir)
                parser_used = "Upstage Document Parser API"  # 파서 정보 업데이트
                
                # 텍스트가 추출되지 않았다면 PyMuPDF로 대체
                if not text.strip():
                    log_message("⚠️ 경고: 업스테이지 API에서 텍스트를 추출하지 못했습니다. PyMuPDF로 전환합니다...")
                    text, image_paths = extract_with_pymupdf(pdf_path, pdf_specific_output_dir)
                    parser_used = "PyMuPDF"  # 파서 정보 업데이트
            except Exception as e:
                log_message(f"❌ 오류: 업스테이지 API 실패: {str(e)}. PyMuPDF로 전환합니다...")
                text, image_paths = extract_with_pymupdf(pdf_path, pdf_specific_output_dir)
                parser_used = "PyMuPDF"  # 파서 정보 업데이트
        
        if not text.strip():
            error_msg = "❌ 오류: PDF에서 텍스트를 추출하지 못했습니다."
            log_message(error_msg)
            return error_msg
        
        log_message(f"추출된 텍스트 길이: {len(text)} 자")
        log_message(f"추출된 이미지 수: {len(image_paths)}개")
        log_message(f"사용된 파서: {parser_used}")
        
        # Generate summary
        log_message(f"\n{language} 언어로 요약 생성 중... (모델: {model_type.upper()}{' - ' + model_name if model_name else ''})")
        summary = handler.generate_summary(text, image_paths)
        
        # Print summary to console
        log_message("\n--- Summary ---")
        print(summary)
        log_message("----------------")
        
        # Save summary to file
        summary_path = os.path.join(pdf_specific_output_dir, "summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        log_message(f"\n요약 저장 완료: {summary_path}")
        
        # Save model and parser info
        info_path = os.path.join(pdf_specific_output_dir, "process_info.json")
        info = {
            "timestamp": timestamp,
            "pdf_file": os.path.basename(pdf_path),
            "model": {
                "type": model_type.upper(),
                "name": model_name
            },
            "parser": {
                "requested": parser,
                "used": parser_used
            },
            "language": language,
            "stats": {
                "text_length": len(text),
                "image_count": len(image_paths)
            }
        }
        
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        
        log_message(f"처리 정보 저장 완료: {info_path}")
        
        return summary
        
    
    except Exception as e:
        error_msg = f"❌ 처리 중 오류 발생: {str(e)}"
        try:
            log_message(error_msg)
            
            # 오류 정보 저장
            error_path = os.path.join(pdf_specific_output_dir, "error_log.txt")
            with open(error_path, 'w', encoding='utf-8') as f:
                f.write(f"Error Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Error Type: {type(e).__name__}\n")
                f.write(f"Error Message: {str(e)}\n")
                f.write(f"PDF File: {pdf_path}\n")
                f.write(f"Model: {model_type.upper()}{' - ' + model_name if model_name else ''}\n")
                f.write(f"Parser: {parser}\n")
                f.write(f"Language: {language}\n")
            
            log_message(f"오류 정보 저장 완료: {error_path}")
        except Exception as log_error:
            print(f"로그 저장 중 추가 오류 발생: {str(log_error)}")
        
        return error_msg

def main():
    parser = argparse.ArgumentParser(description='Process a PDF and generate a summary using different AI models.')
    parser.add_argument('pdf_path', type=str, help='Path to the PDF file to process')
    parser.add_argument('--model', type=str, default='upstage',
                      choices=['upstage', 'llama', 'openai', 'gemini'],
                      help='Model to use for summarization (default: upstage)')
    parser.add_argument('--model-name', type=str, default=None,
                      help='Specific model name/version (e.g., gpt-4-turbo-preview for OpenAI, gemini-pro for Gemini, llama3:latest for Ollama)')
    parser.add_argument('--output-dir', type=str, default='output',
                      help='Directory to save output files (default: output)')
    parser.add_argument('--parser', type=str, default='auto',
                      choices=['auto', 'upstage', 'pymupdf', 'api', 'local'],
                      help='PDF parser to use. Options: auto (try upstage first, fallback to pymupdf), upstage/api (only use upstage API), pymupdf/local (only use PyMuPDF) (default: auto)')
    parser.add_argument('--language', type=str, default='ko',
                      choices=['ko', 'en'],
                      help='Language for the summary (ko: Korean, en: English) (default: ko)')
    
    args = parser.parse_args()
    
    # Set default model names if not provided
    if not args.model_name:
        if args.model == 'openai':
            args.model_name = 'gpt-4-turbo-preview'
        elif args.model == 'gemini':
            args.model_name = 'gemini-pro'
        elif args.model == 'llama':
            args.model_name = 'llama3:latest'
    
    # Process the PDF
    if not os.path.exists(args.pdf_path):
        print(f"❌ 오류: PDF 파일을 찾을 수 없습니다: {args.pdf_path}")
        exit(1)
    
    print("=" * 60)
    print(f"📄 PDF 문서: {os.path.basename(args.pdf_path)}")
    print(f"🤖 모델: {args.model.upper()}{' - ' + args.model_name if args.model_name else ''}")
    print(f"🔍 파서: {args.parser}")
    print(f"🌐 언어: {args.language}")
    print(f"📁 출력 디렉토리: {args.output_dir}")
    print("=" * 60 + "\n")
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    process_pdf(
        pdf_path=args.pdf_path, 
        model_type=args.model, 
        output_dir=args.output_dir, 
        model_name=args.model_name,
        parser=args.parser,
        language=args.language
    )

if __name__ == "__main__":
    main()
