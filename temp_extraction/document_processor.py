import os
import requests
import json
import base64
import logging
import time
import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, Union
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('document_processor')

class ImageAnalysisError(Exception):
    """이미지 분석 중 발생하는 예외"""
    pass

class DocumentProcessorError(Exception):
    """문서 처리 중 발생하는 예외"""
    pass

# 환경 변수 로드
load_dotenv()

class ImageAnalyzer:
    """이미지 분석을 위한 클래스 (Tesseract OCR 기반)"""
    
    def __init__(self, server_url: str = "http://localhost:5050"):
        """
        이미지 분석기 초기화
        
        Args:
            server_url: 이미지 분석 서버 URL (기본값: http://localhost:5050)
        """
        self.server_url = server_url.rstrip('/')
        self.logger = logging.getLogger('image_analyzer')
        self.logger.info(f"이미지 분석기 초기화 완료 (서버: {self.server_url})")
    
    def analyze_image(self, image_path: Union[str, Path]) -> Dict[str, Any]:
        """
        단일 이미지 분석
        
        Args:
            image_path: 분석할 이미지 파일 경로
            
        Returns:
            분석 결과 딕셔너리
        """
        try:
            if isinstance(image_path, Path):
                image_path = str(image_path)
                
            with open(image_path, 'rb') as img_file:
                files = {'file': (os.path.basename(image_path), img_file, 'image/jpeg')}
                response = requests.post(
                    f"{self.server_url}/analyze/ocr",
                    files=files,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                return {
                    'text': result.get('text', ''),
                    'confidence': result.get('confidence', 0.0),
                    'success': True
                }
        except Exception as e:
            error_msg = f"이미지 분석 실패: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                'error': str(e),
                'text': '',
                'confidence': 0.0,
                'success': False
            }
    
    def analyze_directory(self, directory_path: Union[str, Path]) -> Dict[str, Dict[str, Any]]:
        """
        디렉토리 내 모든 이미지 분석
        
        Args:
            directory_path: 이미지가 포함된 디렉토리 경로
            
        Returns:
            {이미지_파일명: 분석_결과} 형식의 딕셔너리
        """
        results = {}
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
        
        try:
            if isinstance(directory_path, str):
                directory_path = Path(directory_path)
                
            if not directory_path.is_dir():
                raise ValueError(f"디렉토리가 존재하지 않습니다: {directory_path}")
                
            image_files = [f for f in directory_path.iterdir() 
                         if f.suffix.lower() in image_extensions and f.is_file()]
            
            self.logger.info(f"분석할 이미지 {len(image_files)}개를 찾았습니다.")
            
            for img_path in image_files:
                self.logger.info(f"이미지 분석 중: {img_path.name}")
                results[img_path.name] = self.analyze_image(img_path)
                
            return results
            
        except Exception as e:
            error_msg = f"이미지 디렉토리 분석 실패: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise ImageAnalysisError(error_msg) from e


class UpstageDocumentParser:
    """업스테이지 Document Parser API를 사용하여 PDF 문서를 파싱하는 클래스"""
    
    def __init__(self, api_key: str = None, timeout: int = 300, max_retries: int = 2, retry_delay: int = 3):
        """
        초기화 함수
        
        Args:
            api_key: 업스테이지 API 키 (None인 경우 환경변수에서 로드)
            timeout: API 요청 타임아웃(초)
            max_retries: 실패 시 재시도 횟수
            retry_delay: 재시도 전 대기 시간(초)
        """
        self.api_key = api_key or os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        self.base_url = "https://api.upstage.ai/v1/document-digitization"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
            # Content-Type은 requests가 자동으로 설정함 (multipart/form-data)
        }
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger('upstage_parser')
        
        self.logger.info(f"업스테이지 Document Parser 초기화 완료 (timeout: {timeout}초, max_retries: {max_retries})")
    
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
                
                # 응답 구조에 따라 텍스트 추출
                content = parse_result.get('content', {}) if isinstance(parse_result, dict) else {}
                
                # 1. content 내부에 있는 경우
                if isinstance(content, dict):
                    for key in ['text', 'markdown', 'html']:
                        if key in content and content[key]:
                            text = content[key]
                            text_source = key
                            logger.info(f"content.{key}에서 내용 추출 성공")
                            print(f"content.{key}에서 내용 추출 성공")
                            break
                
                # 2. content가 없거나 비어있는 경우 루트 레벨에서 직접 검색
                if not text and isinstance(parse_result, dict):
                    for key in ['text', 'markdown', 'html']:
                        if key in parse_result and parse_result[key]:
                            text = parse_result[key]
                            text_source = f"root.{key}"
                            logger.info(f"root.{key}에서 내용 추출 성공")
                            print(f"root.{key}에서 내용 추출 성공")
                            break
                
                # 3. 여전히 텍스트가 없으면 전체 응답을 문자열로 변환
                if not text:
                    text = str(parse_result)
                    text_source = "raw_response"
                    logger.warning("지원되는 텍스트 형식을 찾을 수 없어 전체 응답을 사용합니다.")
                    print("주의: 지원되는 텍스트 형식을 찾을 수 없어 전체 응답을 사용합니다.")
                
                # HTML 태그가 있는 경우 간단히 정리
                if text_source in ['html', 'root.html', 'content.html']:
                    text = text.replace("<br>", "\n")
                    text = text.replace("<p>", "").replace("</p>", "\n")
                    text = text.replace("<h1>", "\n# ").replace("</h1>", "\n")
                    text = text.replace("<h2>", "\n## ").replace("</h2>", "\n")
                    text = text.replace("<h3>", "\n### ").replace("</h3>", "\n")
                    text = text.replace("<table>", "\n표:\n").replace("</table>", "\n")
                    text = text.replace("<tr>", "").replace("</tr>", "\n")
                    text = text.replace("<td>", "").replace("</td>", "\t")
                    text = text.replace("<th>", "").replace("</th>", "\t")
                
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
                
                # 1. figures 배열에서 이미지 추출
                figures = []
                if 'figures' in parse_result and isinstance(parse_result['figures'], list):
                    figures = parse_result['figures']
                # content 내부에 figures가 있는 경우
                elif isinstance(content, dict) and 'figures' in content and isinstance(content['figures'], list):
                    figures = content['figures']
                
                # 2. merged_elements에서 category가 'figure'인 요소 찾기
                merged_figures = []
                if 'merged_elements' in parse_result and isinstance(parse_result['merged_elements'], list):
                    for elem in parse_result['merged_elements']:
                        if isinstance(elem, dict) and elem.get('category') == 'figure':
                            merged_figures.append(elem)
                
                logger.info(f"일반 figures에서 추출된 이미지 수: {len(figures)}개")
                logger.info(f"merged_elements에서 추출된 이미지 수: {len(merged_figures)}개")
                print(f"추출된 이미지 수: {len(figures) + len(merged_figures)}개 (일반: {len(figures)}, merged: {len(merged_figures)})")
                
                # 두 리스트 합치기
                all_figures = figures + merged_figures
                
                for i, figure_data in enumerate(all_figures):
                    try:
                        # base64로 인코딩된 이미지 데이터 추출 (다양한 키 이름 지원)
                        image_base64 = ""
                        
                        # 1. content 내부에 이미지 데이터가 있는 경우
                        if 'content' in figure_data and isinstance(figure_data['content'], dict):
                            for key in ['base64_data', 'data', 'image']:
                                if key in figure_data['content'] and figure_data['content'][key]:
                                    image_base64 = figure_data['content'][key]
                                    break
                        
                        # 2. 직접 키에 이미지 데이터가 있는 경우
                        if not image_base64:
                            for key in ['base64_data', 'data', 'image', 'content']:
                                if key in figure_data and figure_data[key] and isinstance(figure_data[key], str):
                                    image_base64 = figure_data[key]
                                    break
                        
                        if not image_base64:
                            logger.warning(f"이미지 {i+1}: base64 데이터를 찾을 수 없습니다. 사용 가능한 키: {list(figure_data.keys())}")
                            if 'content' in figure_data and isinstance(figure_data['content'], dict):
                                logger.warning(f"content 내부 키: {list(figure_data['content'].keys())}")
                            continue
                            
                        logger.info(f"이미지 {i+1} 처리 중... (출처: {'merged_elements' if i >= len(figures) else 'figures'})")
                        print(f"이미지 {i+1} 처리 중... (출처: {'merged_elements' if i >= len(figures) else 'figures'})")
                        
                        # base64 디코딩 (이미 base64 디코딩된 경우를 대비해 예외 처리)
                        try:
                            if isinstance(image_base64, str):
                                # base64 문자열에서 data:image/...;base64, 접두사 제거 (있는 경우)
                                if ';base64,' in image_base64:
                                    image_base64 = image_base64.split(';base64,', 1)[1]
                                image_data = base64.b64decode(image_base64)
                            else:
                                # 이미 바이너리 데이터인 경우
                                image_data = image_base64
                        except Exception as e:
                            logger.error(f"이미지 {i+1} base64 디코딩 실패: {str(e)}")
                            continue
                        
                        # 이미지 형식 확인
                        image_format = None
                        
                        # 1. figure_data에서 직접 format 정보 가져오기
                        if 'format' in figure_data and figure_data['format']:
                            image_format = figure_data['format'].lower()
                        # 2. content 내부에 format 정보가 있는 경우
                        elif 'content' in figure_data and isinstance(figure_data['content'], dict) and 'format' in figure_data['content']:
                            image_format = figure_data['content']['format'].lower()
                        
                        # 3. MIME 타입에서 추출 (data:image/png;base64,... 형태인 경우)
                        if not image_format and 'content' in figure_data and isinstance(figure_data['content'], str):
                            if figure_data['content'].startswith('data:image/'):
                                mime_type = figure_data['content'].split(';')[0].split('/')[-1]
                                if mime_type in ['jpeg', 'jpg', 'png', 'gif', 'bmp', 'tiff', 'webp']:
                                    image_format = mime_type
                        
                        # 4. 기본값 설정
                        if not image_format or image_format == 'unknown':
                            image_format = 'jpg'
                        
                        # 5. 올바른 확장자로 변환
                        format_mapping = {
                            'jpeg': 'jpg',  # jpeg -> jpg로 통일
                            'tiff': 'tif',   # tiff -> tif로 통일
                        }
                        image_ext = format_mapping.get(image_format, image_format)
                        
                        # 6. 이미지 저장
                        image_filename = f"image_{i+1}_{int(time.time())}.{image_ext}"  # 타임스탬프 추가로 고유성 보장
                        image_path = os.path.join(images_dir, image_filename)
                        
                        try:
                            with open(image_path, "wb") as img_file:
                                img_file.write(image_data)
                            
                            # 이미지 크기 확인
                            image_size = os.path.getsize(image_path) / 1024  # KB 단위
                            
                            # 이미지가 유효한지 확인 (0바이트 파일 방지)
                            if os.path.getsize(image_path) == 0:
                                logger.error(f"이미지 {i+1} 저장 실패: 0바이트 파일이 생성되었습니다.")
                                os.remove(image_path)  # 잘못된 파일 삭제
                                continue
                            
                            # 이미지 메타데이터 로깅
                            logger.info(f"이미지 {i+1} 저장 완료: {image_path} ({image_size:.1f} KB, 형식: {image_format})")
                            print(f"이미지 {i+1} 저장 완료: {image_path} ({image_size:.1f} KB)")
                            
                            # 이미지 경로 저장
                            image_paths.append(image_path)
                            
                        except Exception as e:
                            logger.error(f"이미지 {i+1} 저장 실패: {str(e)}")
                            # 저장에 실패한 경우, 이미지 데이터의 처음 100바이트를 로깅하여 디버깅에 도움
                            logger.debug(f"이미지 데이터 샘플: {image_data[:100] if image_data else '없음'}")
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


class DocumentProcessor:
    """문서 처리 및 이미지 분석을 통합하는 클래스"""
    
    def __init__(
        self,
        upstage_api_key: Optional[str] = None,
        image_server_url: str = "http://localhost:5050",
        output_dir: str = "output",
        log_level: int = logging.INFO
    ):
        """
        문서 처리기 초기화
        
        Args:
            upstage_api_key: 업스테이지 API 키 (None인 경우 환경변수에서 로드)
            image_server_url: 이미지 분석 서버 URL
            output_dir: 출력 디렉토리
            log_level: 로깅 레벨
        """
        # 로깅 설정
        self.logger = logging.getLogger('document_processor')
        self.logger.setLevel(log_level)
        
        # 출력 디렉토리 설정
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # 이미지 분석기 초기화
        self.image_analyzer = ImageAnalyzer(server_url=image_server_url)
        
        # 문서 파서 초기화
        self.document_parser = UpstageDocumentParser(api_key=upstage_api_key)
        
        self.logger.info("문서 처리기가 초기화되었습니다.")
    
    def process_pdf(
        self,
        pdf_path: str,
        analyze_images: bool = True,
        save_markdown: bool = True
    ) -> Dict[str, Any]:
        """
        PDF 문서를 처리하고 분석 결과를 반환합니다.
        
        Args:
            pdf_path: 처리할 PDF 파일 경로
            analyze_images: 이미지 분석 수행 여부
            save_markdown: 마크다운 파일로 저장 여부
            
        Returns:
            분석 결과 딕셔너리
        """
        start_time = time.time()
        pdf_name = Path(pdf_path).stem
        output_subdir = self.output_dir / f"output_{pdf_name}"
        images_dir = output_subdir / "images"
        logs_dir = output_subdir / "logs"
        
        # 디렉토리 생성
        images_dir.mkdir(exist_ok=True, parents=True)
        logs_dir.mkdir(exist_ok=True)
        
        # 로깅 설정
        self._setup_file_logging(logs_dir / "analysis.log")
        
        try:
            self.logger.info(f"PDF 처리 시작: {pdf_path}")
            
            # 1. PDF에서 텍스트와 이미지 추출
            self.logger.info("PDF에서 텍스트와 이미지 추출 중...")
            text, image_paths = self.document_parser.parse_document(
                pdf_path=pdf_path,
                output_dir=str(output_subdir)
            )
            
            result = {
                'pdf_path': pdf_path,
                'text': text,
                'images': image_paths,
                'analysis': {},
                'metadata': {
                    'extraction_time': time.time() - start_time,
                    'image_count': len(image_paths)
                }
            }
            
            # 2. 이미지 분석 (필요한 경우)
            if analyze_images and image_paths:
                self.logger.info(f"이미지 {len(image_paths)}개 분석 시작...")
                image_analysis = {}
                
                for i, img_path in enumerate(image_paths):
                    img_name = Path(img_path).name
                    self.logger.info(f"이미지 {i+1}/{len(image_paths)} 분석 중: {img_name}")
                    
                    try:
                        analysis_result = self.image_analyzer.analyze_image(img_path)
                        image_analysis[img_name] = analysis_result
                    except Exception as e:
                        self.logger.error(f"이미지 분석 중 오류 발생: {str(e)}")
                        image_analysis[img_name] = {
                            'error': str(e),
                            'success': False,
                            'text': '',
                            'confidence': 0.0
                        }
                
                result['analysis'] = image_analysis
                
                # 이미지 분석 결과를 텍스트에 통합
                analysis_text = self._format_analysis_results(image_analysis)
                result['text_with_analysis'] = f"{text}\n\n## 이미지 분석 결과\n\n{analysis_text}"
            
            # 3. 마크다운으로 저장 (필요한 경우)
            if save_markdown:
                markdown_path = output_subdir / f"{pdf_name}_analysis.md"
                self._save_as_markdown(result, str(markdown_path))
                result['markdown_path'] = str(markdown_path)
            
            # 처리 완료
            elapsed_time = time.time() - start_time
            result['metadata']['total_time'] = elapsed_time
            self.logger.info(f"PDF 처리 완료 (소요 시간: {elapsed_time:.2f}초)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"PDF 처리 중 오류 발생: {str(e)}", exc_info=True)
            raise DocumentProcessorError(f"PDF 처리 중 오류 발생: {str(e)}") from e
    
    def _format_analysis_results(self, analysis_results: Dict[str, Dict[str, Any]]) -> str:
        """이미지 분석 결과를 마크다운 형식으로 포맷팅"""
        if not analysis_results:
            return "분석된 이미지가 없습니다."
            
        markdown = []
        for img_name, result in analysis_results.items():
            markdown.append(f"### 이미지: {img_name}\n")
            
            if 'error' in result and result.get('success', True) == False:
                markdown.append(f"**오류**: {result['error']}\n")
            else:
                extracted_text = result.get('text', '')
                if extracted_text.strip():
                    markdown.append(f"**인식된 텍스트**:\n```\n{extracted_text}\n```\n")
                else:
                    markdown.append("**인식된 텍스트**: (없음)\n")
                    
                if 'confidence' in result:
                    confidence = result['confidence']
                    confidence_str = f"{confidence:.2f}" if isinstance(confidence, float) else str(confidence)
                    markdown.append(f"**신뢰도**: {confidence_str}\n")
            
            markdown.append("---\n")
        
        return "\n".join(markdown)
    
    def _save_as_markdown(self, result: Dict[str, Any], output_path: str) -> None:
        """분석 결과를 마크다운 파일로 저장"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # 기본 텍스트
                f.write(f"# PDF 분석 결과\n\n")
                f.write(f"## 문서 정보\n")
                f.write(f"- 파일명: {Path(result['pdf_path']).name}\n")
                f.write(f"- 처리 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"- 이미지 수: {result['metadata']['image_count']}\n\n")
                
                # 본문 텍스트
                f.write("## 문서 내용\n\n")
                content_text = result.get('text_with_analysis', result['text'])
                f.write(content_text + "\n\n")
                
                # 메타데이터
                f.write("## 처리 정보\n")
                f.write(f"- 추출 시간: {result['metadata']['extraction_time']:.2f}초\n")
                if 'total_time' in result['metadata']:
                    f.write(f"- 총 처리 시간: {result['metadata']['total_time']:.2f}초\n")
            
            self.logger.info(f"분석 결과가 마크다운 파일로 저장되었습니다: {output_path}")
            
        except Exception as e:
            self.logger.error(f"마크다운 파일 저장 실패: {str(e)}", exc_info=True)
            raise
    
    def _setup_file_logging(self, log_path: str) -> None:
        """파일 로깅 설정"""
        file_handler = logging.FileHandler(log_path, mode='w', encoding='utf-8')
        file_handler.setLevel(self.logger.level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # 기존 파일 핸들러 제거 후 추가
        for handler in self.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                self.logger.removeHandler(handler)
        
        self.logger.addHandler(file_handler)
