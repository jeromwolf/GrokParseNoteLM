import os
import requests
import json
import base64
import logging
import time
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('document_processor')

class UpstageDocumentParser:
    """업스테이지 Document Parser API를 사용하여 PDF 문서를 파싱하는 클래스"""
    
    def __init__(self, timeout: int = 300, max_retries: int = 2, retry_delay: int = 3):
        """
        초기화 함수
        
        Args:
            timeout: API 요청 타임아웃(초)
            max_retries: 실패 시 재시도 횟수
            retry_delay: 재시도 전 대기 시간(초)
        """
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            logger.error("환경 변수 오류: UPSTAGE_API_KEY가 설정되지 않았습니다.")
            raise ValueError("UPSTAGE_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        self.base_url = "https://api.upstage.ai/v1/document-digitization"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
            # Content-Type은 requests가 자동으로 설정함 (multipart/form-data)
        }
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        logger.info(f"업스테이지 Document Parser 초기화 완료 (timeout: {timeout}초, max_retries: {max_retries})")
    
    def parse_document(self, pdf_path: str, output_dir: str, save_response: bool = True) -> Tuple[str, List[str]]:
        """PDF 문서를 파싱하여 텍스트와 이미지를 추출합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            output_dir: 추출된 이미지를 저장할 디렉토리
            save_response: API 응답 내용을 파일로 저장할지 여부
            
        Returns:
            (추출된_텍스트, 이미지_경로_리스트) 튜플
        """
        # 이미지 저장 디렉토리 생성
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # 로그 파일 저장 디렉토리 생성
        logs_dir = os.path.join(output_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # 현재 시간을 이용한 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(logs_dir, f"upstage_api_{timestamp}.log")
        
        try:
            logger.info(f"업스테이지 Document Parser API를 사용하여 {os.path.basename(pdf_path)} 파싱 시작")
            print(f"업스테이지 Document Parser API를 사용하여 {pdf_path} 파싱 중...")
            
            # 파일 크기 확인
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB 단위
            logger.info(f"PDF 파일 크기: {file_size:.2f} MB")
            
            # PDF 파일 업로드
            with open(pdf_path, "rb") as file:
                files = {"document": file}
                # API 요청 파라미터 설정
                data = {
                    "model": "document-parse",  # 기본 모델 사용
                    "ocr": "true",  # OCR 활성화
                    "chart_recognition": "true",  # 차트 인식 활성화
                    "coordinates": "true",  # 좌표 정보 포함
                    "output_formats": "[\"html\", \"text\", \"markdown\"]",  # 정확한 문자열 형식으로 전달
                    "base64_encoding": "[\"figure\"]",  # 정확한 문자열 형식으로 전달
                }
                
                # 디버깅을 위해 요청 데이터 출력
                logger.debug(f"API 요청 데이터: {data}")
                print(f"API 요청 데이터: {data}")
                
                logger.info(f"문서 업로드 및 파싱 요청 중: {self.base_url}")
                print(f"문서 업로드 및 파싱 요청 중: {self.base_url}")
                
                # 재시도 로직 추가
                for attempt in range(1, self.max_retries + 1):
                    try:
                        start_time = time.time()
                        logger.info(f"API 요청 시도 {attempt}/{self.max_retries}")
                        
                        response = requests.post(
                            self.base_url,
                            headers=self.headers,
                            files=files,
                            data=data,
                            timeout=self.timeout
                        )
                        
                        elapsed_time = time.time() - start_time
                        
                        # 응답 상태 코드 확인
                        logger.info(f"API 응답 상태 코드: {response.status_code} (소요 시간: {elapsed_time:.2f}초)")
                        print(f"API 응답 상태 코드: {response.status_code}")
                        
                        # 오류 발생 시 응답 내용 출력
                        if response.status_code != 200:
                            error_msg = f"API 오류 응답 (HTTP {response.status_code}): {response.text}"
                            logger.error(error_msg)
                            print(f"API 오류 응답: {response.text}")
                            
                            # 오류 로그 저장
                            with open(os.path.join(logs_dir, f"error_{timestamp}_{attempt}.log"), 'w', encoding='utf-8') as f:
                                f.write(f"Status Code: {response.status_code}\n")
                                f.write(f"Response: {response.text}\n")
                            
                            # 재시도 가능한 오류인지 확인
                            if response.status_code in [429, 500, 502, 503, 504] and attempt < self.max_retries:
                                retry_time = self.retry_delay * attempt  # 점진적 대기 시간 증가
                                logger.info(f"{retry_time}초 후 재시도 예정...")
                                print(f"{retry_time}초 후 재시도 예정...")
                                time.sleep(retry_time)
                                continue
                        
                        response.raise_for_status()
                        break  # 성공적인 응답을 받았으므로 루프 종료
                        
                    except requests.exceptions.Timeout:
                        logger.error(f"타임아웃 발생 (시도 {attempt}/{self.max_retries})")
                        print(f"API 요청 타임아웃 (시도 {attempt}/{self.max_retries})")
                        
                        if attempt < self.max_retries:
                            retry_time = self.retry_delay * attempt
                            logger.info(f"{retry_time}초 후 재시도 예정...")
                            print(f"{retry_time}초 후 재시도 예정...")
                            time.sleep(retry_time)
                        else:
                            logger.error("모든 재시도 실패")
                            raise
                            
                    except requests.exceptions.RequestException as e:
                        error_msg = f"API 요청 실패 (시도 {attempt}/{self.max_retries}): {str(e)}"
                        logger.error(error_msg)
                        print(f"API 요청 실패: {str(e)}")
                        
                        if hasattr(e, 'response') and e.response is not None:
                            logger.error(f"응답 내용: {e.response.text[:500]}")
                            print(f"응답 내용: {e.response.text}")
                            
                            # 오류 로그 저장
                            with open(os.path.join(logs_dir, f"error_{timestamp}_{attempt}.log"), 'w', encoding='utf-8') as f:
                                f.write(f"Error: {str(e)}\n")
                                f.write(f"Response: {e.response.text}\n")
                        
                        if attempt < self.max_retries:
                            retry_time = self.retry_delay * attempt
                            logger.info(f"{retry_time}초 후 재시도 예정...")
                            print(f"{retry_time}초 후 재시도 예정...")
                            time.sleep(retry_time)
                        else:
                            logger.error("모든 재시도 실패")
                            raise
                
                # 파싱 결과 확인
                parse_result = response.json()
                logger.info("문서 파싱 성공")
                print("문서 파싱 성공.")
                
                # API 응답 저장 (선택사항)
                if save_response:
                    response_file = os.path.join(logs_dir, f"response_{timestamp}.json")
                    try:
                        with open(response_file, 'w', encoding='utf-8') as f:
                            json.dump(parse_result, f, ensure_ascii=False, indent=2)
                        logger.info(f"API 응답 저장 완료: {response_file}")
                    except Exception as e:
                        logger.warning(f"API 응답 저장 실패: {str(e)}")
                
                # 응답 내용 로깅
                logger.info(f"API 응답 내용: {list(parse_result.keys())}")
                print(f"API 응답 내용: {parse_result.keys()}")
                
                # 디버깅: 응답 내용 출력
                for key, value in parse_result.items():
                    if isinstance(value, str) and len(value) > 100:
                        logger.debug(f"  - {key}: {value[:100]}... (길이: {len(value)})")
                        print(f"  - {key}: {value[:100]}... (길이: {len(value)})")
                    elif isinstance(value, list):
                        logger.debug(f"  - {key}: [리스트, 길이: {len(value)}]")
                        print(f"  - {key}: [리스트, 길이: {len(value)}]")
                    else:
                        logger.debug(f"  - {key}: {value}")
                        print(f"  - {key}: {value}")
                
                # 텍스트 추출 (여러 출력 형식 중 선택)
                text = ""
                text_source = ""
                
                # 1. 먼저 text 형식 사용 (가장 깔끔한 텍스트)
                if "text" in parse_result and parse_result["text"]:
                    text = parse_result["text"]
                    text_source = "text"
                    logger.info("텍스트 형식에서 내용 추출 성공")
                    print("텍스트 형식에서 내용 추출 성공")
                # 2. text가 없으면 markdown 형식 사용
                elif "markdown" in parse_result and parse_result["markdown"]:
                    text = parse_result["markdown"]
                    text_source = "markdown"
                    logger.info("마크다운 형식에서 내용 추출 성공")
                    print("마크다운 형식에서 내용 추출 성공")
                # 3. 마지막으로 HTML 형식 사용
                elif "html" in parse_result and parse_result["html"]:
                    html_content = parse_result.get("html", "")
                    text_source = "html"
                    # 간단한 HTML 태그 제거 (실제로는 더 정교한 파싱이 필요할 수 있음)
                    text = html_content.replace("<br>", "\n")
                    text = text.replace("<p>", "").replace("</p>", "\n")
                    text = text.replace("<h1>", "").replace("</h1>", "\n")
                    text = text.replace("<h2>", "").replace("</h2>", "\n")
                    text = text.replace("<h3>", "").replace("</h3>", "\n")
                    text = text.replace("<table>", "\n표:\n").replace("</table>", "\n")
                    text = text.replace("<tr>", "").replace("</tr>", "\n")
                    text = text.replace("<td>", "").replace("</td>", "\t")
                    text = text.replace("<th>", "").replace("</th>", "\t")
                    logger.info("HTML 형식에서 내용 추출 성공")
                    print("HTML 형식에서 내용 추출 성공")
                else:
                    logger.warning("지원되는 텍스트 형식을 찾을 수 없음")
                    print("주의: 지원되는 텍스트 형식을 찾을 수 없습니다.")
                
                # 추출된 요소 확인
                elements_count = 0
                if "merged_elements" in parse_result:
                    elements_count = len(parse_result.get("merged_elements", []))
                    logger.info(f"추출된 요소 수: {elements_count}개")
                    print(f"추출된 요소 수: {elements_count}개")
                
                logger.info(f"추출된 텍스트 길이: {len(text)} 자 (소스: {text_source})")
                print(f"추출된 텍스트 길이: {len(text)} 자")
                
                # 텍스트 저장 (디버깅용)
                if text and save_response:
                    text_file = os.path.join(logs_dir, f"extracted_text_{timestamp}.txt")
                    try:
                        with open(text_file, 'w', encoding='utf-8') as f:
                            f.write(text)
                        logger.info(f"추출된 텍스트 저장 완료: {text_file}")
                    except Exception as e:
                        logger.warning(f"텍스트 저장 실패: {str(e)}")
                
                # 이미지 추출 및 저장
                image_paths = []
                figures = parse_result.get("figures", [])
                logger.info(f"추출된 이미지 수: {len(figures)}개")
                print(f"추출된 이미지 수: {len(figures)}개")
                
                for i, figure_data in enumerate(figures):
                    try:
                        # base64로 인코딩된 이미지 데이터 추출
                        image_base64 = figure_data.get("base64_data", "")
                        if not image_base64:
                            logger.warning(f"이미지 {i+1}: base64_data가 없습니다")
                            continue
                            
                        logger.info(f"이미지 {i+1} 처리 중...")
                        print(f"이미지 {i+1} 처리 중...")
                        
                        # base64 디코딩
                        try:
                            image_data = base64.b64decode(image_base64)
                        except Exception as e:
                            logger.error(f"이미지 {i+1} base64 디코딩 실패: {str(e)}")
                            continue
                        
                        # 이미지 형식 확인 및 확장자 설정
                        image_format = figure_data.get("format", "jpg").lower()
                        if not image_format or image_format == "unknown":
                            image_format = "jpg"  # 기본값
                        
                        # 이미지 저장
                        image_filename = f"image_{i+1}.{image_format}"
                        image_path = os.path.join(images_dir, image_filename)
                        
                        try:
                            with open(image_path, "wb") as img_file:
                                img_file.write(image_data)
                            
                            # 이미지 크기 확인
                            image_size = os.path.getsize(image_path) / 1024  # KB 단위
                            
                            image_paths.append(image_path)
                            logger.info(f"이미지 {i+1} 저장 완료: {image_path} ({image_size:.1f} KB)")
                            print(f"이미지 {i+1} 저장 완료: {image_path}")
                        except Exception as e:
                            logger.error(f"이미지 {i+1} 저장 실패: {str(e)}")
                    except Exception as e:
                        logger.error(f"이미지 {i+1} 처리 중 오류 발생: {str(e)}")
                
                # 처리 결과 요약
                logger.info(f"업스테이지 API 처리 결과: 텍스트 {len(text)} 자, 이미지 {len(image_paths)}/{len(figures)} 개 추출")
                
                return text, image_paths
                
        except Exception as e:
            error_msg = f"업스테이지 Document Parser API 요청 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            
            # 오류 로그 저장
            try:
                error_log_file = os.path.join(logs_dir, f"error_{timestamp}.log")
                with open(error_log_file, 'w', encoding='utf-8') as f:
                    f.write(f"Error: {str(e)}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"PDF file: {pdf_path}\n")
                logger.info(f"오류 로그 저장 완료: {error_log_file}")
            except Exception as log_error:
                logger.warning(f"오류 로그 저장 실패: {str(log_error)}")
            
            return "", []

# 사용 예시
def extract_text_and_images_from_pdf(pdf_path: str, output_dir: str) -> Tuple[str, List[str]]:
    """PDF 파일에서 텍스트와 이미지를 추출합니다 (업스테이지 Document Parser API 사용).
    
    Args:
        pdf_path: PDF 파일 경로
        output_dir: 추출된 이미지를 저장할 디렉토리
        
    Returns:
        (추출된_텍스트, 이미지_경로_리스트) 튜플
    """
    parser = UpstageDocumentParser()
    return parser.parse_document(pdf_path, output_dir)
