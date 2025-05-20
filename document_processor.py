import os
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('document_processing.log')
    ]
)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """PDF 문서를 처리하는 클래스"""
    
    def __init__(self, output_dir: str = "output"):
        """
        초기화 메서드
        
        Args:
            output_dir (str): 출력 디렉토리 경로
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"출력 디렉토리: {self.output_dir.absolute()}")
    
    def process_pdf(self, pdf_path: str, chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """
        PDF 문서를 처리하고 텍스트를 추출합니다.
        
        Args:
            pdf_path (str): 처리할 PDF 파일 경로
            chunk_size (int): 텍스트 청크 크기 (문자 수 기준)
            
        Returns:
            List[Dict[str, Any]]: 추출된 텍스트 청크 목록
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        logger.info(f"PDF 처리 시작: {pdf_path.name} (크기: {pdf_path.stat().st_size / 1024:.2f} KB)")
        
        chunks = []
        doc = fitz.open(pdf_path)
        
        try:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # 페이지에서 텍스트 추출
                text = page.get_text()
                
                # 이미지 추출 (있는 경우)
                images = page.get_images(full=True)
                image_paths = []
                
                if images:
                    image_dir = self.output_dir / "images" / f"{pdf_path.stem}_p{page_num+1}"
                    image_dir.mkdir(parents=True, exist_ok=True)
                    
                    for img_index, img in enumerate(images, 1):
                        try:
                            xref = img[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            
                            # 이미지 확장자 결정 (기본값: jpg)
                            image_ext = base_image.get("ext", "jpg")
                            if image_ext.lower() not in ["jpg", "jpeg", "png", "gif", "bmp", "tiff"]:
                                image_ext = "jpg"
                                
                            # 이미지 저장
                            image_filename = f"{pdf_path.stem}_p{page_num+1}_img{img_index}.{image_ext}"
                            image_path = image_dir / image_filename
                            
                            with open(image_path, "wb") as f:
                                f.write(image_bytes)
                            
                            image_paths.append(str(image_path.relative_to(self.output_dir)))
                            logger.debug(f"이미지 추출됨: {image_path}")
                            
                        except Exception as e:
                            logger.error(f"이미지 추출 중 오류 (페이지 {page_num+1}, 이미지 {img_index}): {str(e)}")
                
                # 텍스트를 청크로 나누기
                for i in range(0, len(text), chunk_size):
                    chunk = {
                        "document": pdf_path.name,
                        "page": page_num + 1,
                        "chunk_id": len(chunks) + 1,
                        "text": text[i:i + chunk_size],
                        "has_images": bool(images),
                        "image_paths": image_paths if images else []
                    }
                    chunks.append(chunk)
                    
                logger.info(f"페이지 {page_num + 1} 처리 완료 (텍스트: {len(text)}자, 이미지: {len(images)}개)")
            
            # 청크 정보 저장
            chunks_file = self.output_dir / f"{pdf_path.stem}_chunks.json"
            with open(chunks_file, "w", encoding="utf-8") as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
                
            logger.info(f"PDF 처리 완료: {len(chunks)}개의 청크가 {chunks_file}에 저장됨")
            
            return chunks
            
        except Exception as e:
            logger.error(f"PDF 처리 중 오류 발생: {str(e)}")
            raise
            
        finally:
            doc.close()
    
    @staticmethod
    def get_pdf_metadata(pdf_path: str) -> Dict[str, Any]:
        """
        PDF 파일의 메타데이터를 추출합니다.
        
        Args:
            pdf_path (str): PDF 파일 경로
            
        Returns:
            Dict[str, Any]: PDF 메타데이터
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        try:
            metadata = {
                "file_name": pdf_path.name,
                "file_size": pdf_path.stat().st_size,
                "num_pages": len(doc),
                "author": doc.metadata.get("author", ""),
                "title": doc.metadata.get("title", pdf_path.stem),
                "subject": doc.metadata.get("subject", ""),
                "keywords": doc.metadata.get("keywords", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "creation_date": doc.metadata.get("creationDate", ""),
                "modification_date": doc.metadata.get("modDate", "")
            }
            return metadata
            
        except Exception as e:
            logger.error(f"PDF 메타데이터 추출 중 오류 발생: {str(e)}")
            return {}
            
        finally:
            doc.close()


# 사용 예시
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("사용법: python document_processor.py <PDF 파일 경로> [출력 디렉토리]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    
    try:
        # 문서 처리기 초기화
        processor = DocumentProcessor(output_dir=output_dir)
        
        # PDF 메타데이터 추출
        print("\nPDF 메타데이터:")
        metadata = processor.get_pdf_metadata(pdf_path)
        for key, value in metadata.items():
            print(f"- {key}: {value}")
        
        # PDF 처리
        print(f"\nPDF 처리 중: {pdf_path}")
        chunks = processor.process_pdf(pdf_path)
        
        print(f"\n처리 완료: {len(chunks)}개의 텍스트 청크가 생성되었습니다.")
        print(f"출력 디렉토리: {output_dir}")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}", file=sys.stderr)
        sys.exit(1)
