import os
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# 내부 모듈 임포트
from document_processor import extract_text_and_images_from_pdf
from model_handler import ModelHandler
from image_analyzer import analyze_pdf_images

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('pdf_analyzer')

def analyze_pdf(
    pdf_path: str, 
    output_dir: str = "output", 
    model_type: str = "upstage", 
    model_name: Optional[str] = None,
    parser: str = "auto",
    language: str = "ko",
    ocr_language: str = "kor+eng",
    save_json: bool = True
) -> str:
    """
    PDF 파일을 분석하여 텍스트 추출, 이미지 추출 및 OCR 분석을 수행하고
    마크다운 형식으로 결과를 반환합니다.
    
    Args:
        pdf_path: PDF 파일 경로
        output_dir: 출력 디렉토리
        model_type: 요약에 사용할 모델 타입 ('upstage', 'llama', 'openai', 'gemini')
        model_name: 특정 모델 이름/버전
        parser: PDF 파서 ('auto', 'upstage', 'pymupdf')
        language: 요약 언어 ('ko', 'en')
        ocr_language: OCR 언어 ('kor+eng', 'eng', 'kor' 등)
        save_json: JSON 형식으로도 결과를 저장할지 여부
        
    Returns:
        마크다운 형식의 분석 결과
    """
    try:
        # PDF 파일 존재 확인
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
            
        # 문서 처리기 초기화
        model_handler = ModelHandler(model_type=model_type, model_name=model_name)
        
        # 출력 디렉토리 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        pdf_specific_output_dir = os.path.join(output_dir, f"{pdf_name}_{model_type.upper()}_{timestamp}")
        os.makedirs(pdf_specific_output_dir, exist_ok=True)
        
        # 로그 파일 설정
        log_file = os.path.join(pdf_specific_output_dir, "process_log.txt")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
        def log_message(message: str):
            """로그 메시지를 콘솔과 파일에 기록합니다."""
            logger.info(message)
            print(message)
        
        log_message(f"PDF 분석 시작: {pdf_path}")
        log_message(f"출력 디렉토리: {pdf_specific_output_dir}")
        log_message(f"모델: {model_type.upper()}{' - ' + model_name if model_name else ''}")
        
        # 1. PDF에서 텍스트와 이미지 추출
        log_message("1. PDF에서 텍스트와 이미지 추출 중...")
        
        text = ""
        image_paths = []
        parser_used = ""
        
        # PDF 파싱 (업스테이지 파서만 사용)
        try:
            # 이미지 저장을 위한 디렉토리 생성
            images_output_dir = os.path.join(output_dir, "images")
            os.makedirs(images_output_dir, exist_ok=True)
            
            text, images = extract_text_and_images_from_pdf(
                pdf_path, 
                output_dir=output_dir  # 이미지 저장 디렉토리는 parse_document 내부에서 처리
            )
            metadata = {}  # 메타데이터는 빈 딕셔너리로 초기화
            logger.info("업스테이지 PDF 파서를 사용하여 문서를 처리했습니다.")
            
            if not text:
                # API 응답에서 직접 텍스트 추출 시도
                response_file = os.path.join(output_dir, "images", "logs", "response_*.json")
                import glob
                response_files = glob.glob(response_file)
                if response_files:
                    with open(response_files[0], 'r', encoding='utf-8') as f:
                        response_data = json.load(f)
                    
                    # 다양한 키에서 텍스트 추출 시도
                    for key in ['text', 'markdown', 'html']:
                        if key in response_data.get('content', {}):
                            text = response_data['content'][key]
                            logger.info(f"API 응답에서 {key} 형식으로 텍스트 추출 성공")
                            break
                    
                    # 여전히 텍스트가 없으면 content에서 직접 추출
                    if not text and 'content' in response_data:
                        text = str(response_data['content'])
            
            if not text:
                raise ValueError("PDF에서 텍스트를 추출할 수 없습니다.")
            
            log_message(f"추출된 텍스트: {len(text)} 자")
            log_message(f"추출된 이미지: {len(images) if images else 0}개")
            
        except Exception as e:
            logger.error(f"PDF 분석 중 오류 발생: {str(e)}")
            raise
        
        # 2. 이미지 OCR 분석
        log_message("2. 추출된 이미지 OCR 분석 중...")
        
        image_analysis_markdown = ""
        if images and len(images) > 0:
            # 이미지 경로가 상대 경로일 수 있으므로 절대 경로로 변환
            image_paths = []
            for img_path in images:
                if not os.path.isabs(img_path):
                    # 이미지 경로가 상대 경로인 경우, output_dir을 기준으로 절대 경로 생성
                    abs_img_path = os.path.abspath(os.path.join(output_dir, img_path))
                    image_paths.append(abs_img_path)
                else:
                    image_paths.append(img_path)
            
            log_message(f"분석할 이미지 경로: {image_paths}")
            
            if image_paths:
                image_analysis_markdown = analyze_pdf_images(image_paths, ocr_language)
                log_message(f"이미지 OCR 분석 완료")
            else:
                image_analysis_markdown = "## 이미지 분석 결과\n\n이미지 경로를 확인할 수 없습니다.\n"
                log_message("분석할 이미지 경로를 찾을 수 없습니다.")
        else:
            image_analysis_markdown = "## 이미지 분석 결과\n\n이미지가 없거나 추출되지 않았습니다.\n"
            log_message("분석할 이미지가 없습니다.")
        
        # 3. 텍스트 요약 (선택적)
        summary = ""
        if model_type:
            log_message(f"3. {model_type.upper()} 모델을 사용하여 텍스트 요약 중...")
            
            try:
                model_handler = ModelHandler(model_type, model_name, language)
                summary = model_handler.generate_summary(text)
                log_message("텍스트 요약 완료")
            except Exception as e:
                log_message(f"텍스트 요약 오류: {str(e)}")
                summary = f"요약 생성 중 오류 발생: {str(e)}"
        
        # 4. 마크다운 형식으로 결과 통합
        log_message("4. 분석 결과 통합 중...")
        
        markdown_result = f"""# PDF 분석 결과: {os.path.basename(pdf_path)}

## 문서 정보
- **파일명**: {os.path.basename(pdf_path)}
- **처리 시간**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **추출 방법**: {parser_used}
- **텍스트 길이**: {len(text)} 자
- **이미지 수**: {len(image_paths)}개

## 텍스트 내용
```
{text[:2000]}{'...' if len(text) > 2000 else ''}
```
{f'전체 텍스트는 너무 깁니다. 위 내용은 처음 2000자만 표시한 것입니다.' if len(text) > 2000 else ''}

{image_analysis_markdown}

"""
        if summary:
            markdown_result += f"""## 텍스트 요약
```
{summary}
```

"""
        
        # 5. 결과 저장
        log_message("5. 분석 결과 저장 중...")
        
        # 마크다운 파일로 저장
        markdown_path = os.path.join(pdf_specific_output_dir, "summary.md")
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_result)
        
        # 텍스트 파일로도 저장 (LLM 호환성)
        text_path = os.path.join(pdf_specific_output_dir, "summary.txt")
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(markdown_result)
        
        # JSON 형식으로도 저장 (선택적)
        if save_json:
            json_data = {
                "document_info": {
                    "filename": os.path.basename(pdf_path),
                    "processing_time": datetime.now().isoformat(),
                    "extraction_method": parser_used,
                    "text_length": len(text),
                    "image_count": len(image_paths)
                },
                "text_content": text,
                "images": [{"path": path, "filename": os.path.basename(path)} for path in image_paths],
                "summary": summary if summary else None
            }
            
            json_path = os.path.join(pdf_specific_output_dir, "summary.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        # 처리 정보 저장
        info = {
            "pdf_path": pdf_path,
            "output_dir": pdf_specific_output_dir,
            "timestamp": datetime.now().isoformat(),
            "model": {
                "type": model_type,
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
        
        info_path = os.path.join(pdf_specific_output_dir, "process_info.json")
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        
        log_message(f"분석 완료! 결과 저장 위치: {pdf_specific_output_dir}")
        
        return markdown_result
        
    except Exception as e:
        error_msg = f"PDF 분석 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        
        try:
            # 오류 정보 저장
            if 'pdf_specific_output_dir' in locals():
                error_path = os.path.join(pdf_specific_output_dir, "error_log.txt")
                with open(error_path, 'w', encoding='utf-8') as f:
                    f.write(f"Error Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Error Type: {type(e).__name__}\n")
                    f.write(f"Error Message: {str(e)}\n")
                    f.write(f"PDF File: {pdf_path}\n")
                logger.info(f"오류 정보 저장 완료: {error_path}")
        except Exception as log_error:
            logger.error(f"로그 저장 중 추가 오류 발생: {str(log_error)}")
        
        return f"# PDF 분석 오류\n\n{error_msg}"

def main():
    """명령줄에서 실행할 때 사용하는 메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PDF 파일을 분석하여 텍스트, 이미지 추출 및 OCR 분석을 수행합니다.')
    parser.add_argument('pdf_path', type=str, help='분석할 PDF 파일 경로')
    parser.add_argument('--output-dir', type=str, default='output', help='출력 디렉토리 (기본값: output)')
    parser.add_argument('--model', type=str, default='upstage',
                      choices=['upstage', 'llama', 'openai', 'gemini', 'none'],
                      help='요약에 사용할 모델 (기본값: upstage, none: 요약 없음)')
    parser.add_argument('--model-name', type=str, default=None,
                      help='특정 모델 이름/버전 (예: gpt-4-turbo-preview, gemini-pro, llama3:latest)')
    parser.add_argument('--parser', type=str, default='auto',
                      choices=['auto', 'upstage', 'pymupdf', 'api', 'local'],
                      help='PDF 파서 (기본값: auto)')
    parser.add_argument('--language', type=str, default='ko',
                      choices=['ko', 'en'],
                      help='요약 언어 (ko: 한국어, en: 영어) (기본값: ko)')
    parser.add_argument('--ocr-language', type=str, default='kor+eng',
                      help='OCR 언어 (기본값: kor+eng)')
    parser.add_argument('--no-json', action='store_true', help='JSON 형식으로 결과를 저장하지 않음')
    
    args = parser.parse_args()
    
    # 모델 타입이 'none'이면 요약하지 않음
    model_type = None if args.model == 'none' else args.model
    
    # PDF 분석 실행
    analyze_pdf(
        pdf_path=args.pdf_path,
        output_dir=args.output_dir,
        model_type=model_type,
        model_name=args.model_name,
        parser=args.parser,
        language=args.language,
        ocr_language=args.ocr_language,
        save_json=not args.no_json
    )

if __name__ == "__main__":
    main()
