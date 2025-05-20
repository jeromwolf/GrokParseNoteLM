import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
import base64
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('image_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

class MCPImageAnalyzer:
    """MCP 이미지 리더 서버를 사용하여 이미지에서 텍스트를 추출하는 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:5001", max_workers: int = 4):
        """
        초기화 메서드
        
        Args:
            base_url (str): MCP 이미지 리더 서버의 기본 URL
            max_workers (int): 병렬 처리를 위한 최대 워커 수
        """
        self.base_url = base_url.rstrip("/")
        self.max_workers = max_workers
        self.session = requests.Session()
    
    def read_image(self, image_path: Path) -> Optional[Dict[str, Any]]:
        """단일 이미지에서 텍스트를 추출"""
        if not image_path.exists():
            logger.error(f"이미지 파일을 찾을 수 없습니다: {image_path}")
            return None
            
        try:
            with open(image_path, 'rb') as img_file:
                files = {'file': (image_path.name, img_file, 'image/jpeg')}
                response = self.session.post(
                    f"{self.base_url}/read_image",
                    files=files,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        'image_path': str(image_path),
                        'text': result.get('text', ''),
                        'success': True
                    }
                else:
                    logger.error(f"이미지 분석 실패 ({image_path}): {response.status_code} - {response.text}")
                    return {
                        'image_path': str(image_path),
                        'error': f"HTTP {response.status_code}: {response.text}",
                        'success': False
                    }
                    
        except Exception as e:
            logger.error(f"이미지 처리 중 오류 발생 ({image_path}): {str(e)}")
            return {
                'image_path': str(image_path),
                'error': str(e),
                'success': False
            }
    
    def batch_read_images(self, image_dir: Path, recursive: bool = True) -> Dict[str, Any]:
        """디렉토리 내의 모든 이미지에서 텍스트를 일괄 추출"""
        if not image_dir.exists() or not image_dir.is_dir():
            logger.error(f"유효한 디렉토리가 아닙니다: {image_dir}")
            return {
                'success': False,
                'error': f"Directory not found: {image_dir}",
                'results': {}
            }
        
        # 이미지 파일 목록 수집
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
        image_files = []
        
        if recursive:
            for ext in image_extensions:
                image_files.extend(image_dir.glob(f'**/*{ext}'))
                image_files.extend(image_dir.glob(f'**/*{ext.upper()}'))
        else:
            for ext in image_extensions:
                image_files.extend(image_dir.glob(f'*{ext}'))
                image_files.extend(image_dir.glob(f'*{ext.upper()}'))
        
        # 중복 제거
        image_files = list(set(image_files))
        
        if not image_files:
            logger.warning(f"이미지 파일을 찾을 수 없습니다: {image_dir}")
            return {
                'success': True,
                'message': 'No image files found',
                'results': {}
            }
        
        logger.info(f"총 {len(image_files)}개의 이미지 파일을 찾았습니다.")
        
        # 병렬 처리로 이미지 분석
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {
                executor.submit(self.read_image, img_path): img_path 
                for img_path in image_files
            }
            
            for future in as_completed(future_to_path):
                img_path = future_to_path[future]
                try:
                    result = future.result()
                    if result:
                        results[str(img_path)] = result
                except Exception as e:
                    logger.error(f"이미지 처리 중 예외 발생 ({img_path}): {str(e)}")
                    results[str(img_path)] = {
                        'image_path': str(img_path),
                        'error': str(e),
                        'success': False
                    }
        
        return {
            'success': True,
            'total_images': len(image_files),
            'processed': len(results),
            'results': results
        }
    
    def analyze_document_images(self, pdf_path: Path, output_dir: Path = None) -> Dict[str, Any]:
        """PDF 문서에서 이미지를 추출하고 분석"""
        from document_processor import DocumentProcessor  # 순환 참조 방지를 위해 여기서 임포트
        
        if not output_dir:
            output_dir = Path("output") / "images"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. PDF에서 이미지 추출
        processor = DocumentProcessor(output_dir=str(output_dir.parent))
        processor.process_pdf(str(pdf_path))
        
        # 2. 추출된 이미지 분석
        image_dir = output_dir / "extracted"
        if image_dir.exists() and any(image_dir.iterdir()):
            return self.batch_read_images(image_dir)
        else:
            return {
                'success': False,
                'error': 'No images extracted from the document',
                'results': {}
            }
    
    def save_results(self, results: Dict[str, Any], output_file: Path) -> bool:
        """분석 결과를 JSON 파일로 저장"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"결과가 {output_file}에 저장되었습니다.")
            return True
        except Exception as e:
            logger.error(f"결과 저장 중 오류 발생: {str(e)}")
            return False


# 사용 예시
if __name__ == "__main__":
    # 이미지 분석기 초기화
    analyzer = MCPImageAnalyzer()
    
    # 단일 이미지 분석 예시
    # result = analyzer.read_image(Path("path/to/your/image.jpg"))
    # print(result)
    
    # 디렉토리 내 모든 이미지 일괄 분석 예시
    # results = analyzer.batch_read_images(Path("path/to/images/directory"))
    # analyzer.save_results(results, "image_analysis_results.json")
    
    # PDF 문서에서 이미지 추출 후 분석 예시
    # pdf_path = Path("path/to/your/document.pdf")
    # results = analyzer.analyze_document_images(pdf_path)
    # analyzer.save_results(results, "document_image_analysis.json")
