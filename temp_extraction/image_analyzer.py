import os
import requests
import logging
from typing import List, Dict, Any, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('image_analyzer')

class ImageAnalyzer:
    """PDF에서 추출된 이미지를 분석하는 클래스"""
    
    def __init__(self, server_url: str = "http://localhost:5050"):
        """
        초기화 함수
        
        Args:
            server_url: 이미지 분석 서버 URL
        """
        self.server_url = server_url.rstrip('/')
        logger.info(f"이미지 분석기 초기화 완료 (서버 URL: {self.server_url})")
    
    def check_server_health(self) -> bool:
        """
        이미지 분석 서버 상태를 확인합니다.
        
        Returns:
            서버가 정상 작동 중이면 True, 그렇지 않으면 False
        """
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("이미지 분석 서버 연결 성공")
                return True
            else:
                logger.warning(f"이미지 분석 서버 응답 오류: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"이미지 분석 서버 연결 실패: {str(e)}")
            return False
    
    def analyze_image(self, image_path: str, lang: str = "kor+eng") -> Dict[str, Any]:
        """
        단일 이미지를 분석합니다.
        
        Args:
            image_path: 이미지 파일 경로
            lang: OCR 언어 (기본값: kor+eng)
            
        Returns:
            이미지 분석 결과 딕셔너리
        """
        if not os.path.exists(image_path):
            logger.warning(f"이미지 파일을 찾을 수 없음: {image_path}")
            return {"path": image_path, "error": "파일을 찾을 수 없음", "ocr_text": ""}
        
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
                response = requests.post(
                    f"{self.server_url}/analyze/ocr",
                    files=files,
                    params={'lang': lang},
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"이미지 분석 성공: {os.path.basename(image_path)}")
                return {
                    "path": image_path,
                    "filename": os.path.basename(image_path),
                    "ocr_text": result.get("text", ""),
                    "language": result.get("language", lang),
                    "process_time": result.get("process_time_seconds", 0)
                }
            else:
                logger.error(f"이미지 분석 API 오류: {response.status_code}")
                return {
                    "path": image_path, 
                    "filename": os.path.basename(image_path),
                    "error": f"API 오류: {response.status_code}",
                    "ocr_text": ""
                }
        except Exception as e:
            logger.error(f"이미지 분석 중 오류 발생: {str(e)}")
            return {
                "path": image_path, 
                "filename": os.path.basename(image_path),
                "error": str(e),
                "ocr_text": ""
            }
    
    def analyze_images(self, image_paths: List[str], lang: str = "kor+eng") -> List[Dict[str, Any]]:
        """
        여러 이미지를 분석합니다.
        
        Args:
            image_paths: 이미지 파일 경로 목록
            lang: OCR 언어 (기본값: kor+eng)
            
        Returns:
            이미지 분석 결과 목록
        """
        if not image_paths:
            logger.warning("분석할 이미지가 없습니다.")
            return []
        
        # 서버 상태 확인
        if not self.check_server_health():
            logger.error("이미지 분석 서버가 응답하지 않습니다.")
            return [{"path": path, "filename": os.path.basename(path), "error": "서버 연결 실패", "ocr_text": ""} for path in image_paths]
        
        # 개별 이미지 분석
        results = []
        for image_path in image_paths:
            result = self.analyze_image(image_path, lang)
            results.append(result)
        
        logger.info(f"총 {len(results)}개 이미지 분석 완료")
        return results
    
    def extract_page_info(self, filename: str) -> Dict[str, Any]:
        """
        파일명에서 페이지 및 이미지 번호 정보를 추출합니다.
        
        Args:
            filename: 이미지 파일명 (예: page1_img2.png)
            
        Returns:
            페이지 및 이미지 번호 정보
        """
        try:
            # 파일명 형식이 'pageX_imgY.ext'인 경우
            if filename.startswith('page') and '_img' in filename:
                parts = filename.split('_')
                page_part = parts[0]
                img_part = parts[1].split('.')[0]
                
                page_num = int(page_part.replace('page', ''))
                img_num = int(img_part.replace('img', ''))
                
                return {
                    "page": page_num,
                    "image_num": img_num,
                    "valid": True
                }
            else:
                return {"valid": False}
        except Exception:
            return {"valid": False}
    
    def format_results_markdown(self, results: List[Dict[str, Any]]) -> str:
        """
        이미지 분석 결과를 마크다운 형식으로 변환합니다.
        
        Args:
            results: 이미지 분석 결과 목록
            
        Returns:
            마크다운 형식의 결과 문자열
        """
        if not results:
            return "## 이미지 분석 결과\n\n이미지가 없거나 분석에 실패했습니다.\n"
        
        # 페이지별로 이미지 그룹화
        pages = {}
        for result in results:
            filename = result.get("filename", "")
            page_info = self.extract_page_info(filename)
            
            if page_info["valid"]:
                page_num = page_info["page"]
                if page_num not in pages:
                    pages[page_num] = []
                pages[page_num].append(result)
            else:
                # 페이지 정보가 없는 이미지는 페이지 0으로 분류
                if 0 not in pages:
                    pages[0] = []
                pages[0].append(result)
        
        # 마크다운 형식으로 변환
        markdown = "## 이미지 분석 결과\n\n"
        
        # 페이지 순서대로 정렬
        for page_num in sorted(pages.keys()):
            if page_num == 0:
                markdown += "### 기타 이미지\n\n"
            else:
                markdown += f"### 페이지 {page_num}\n\n"
            
            for result in pages[page_num]:
                filename = result.get("filename", "알 수 없음")
                ocr_text = result.get("ocr_text", "").strip()
                
                if "error" in result:
                    markdown += f"- **{filename}**: 분석 오류 - {result['error']}\n\n"
                elif not ocr_text:
                    markdown += f"- **{filename}**: 텍스트 없음\n\n"
                else:
                    markdown += f"- **{filename}**:\n  ```\n  {ocr_text}\n  ```\n\n"
        
        return markdown

# 사용 예시
def analyze_pdf_images(image_paths: List[str], lang: str = "kor+eng") -> str:
    """
    PDF에서 추출된 이미지를 분석하고 마크다운 형식으로 결과를 반환합니다.
    
    Args:
        image_paths: 이미지 파일 경로 목록
        lang: OCR 언어 (기본값: kor+eng)
        
    Returns:
        마크다운 형식의 분석 결과
    """
    analyzer = ImageAnalyzer()
    results = analyzer.analyze_images(image_paths, lang)
    return analyzer.format_results_markdown(results)
