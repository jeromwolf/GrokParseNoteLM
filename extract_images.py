import os
import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime

# 디버그 로깅을 위한 설정
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 디렉토리 설정
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "Data"
OUTPUT_DIR = BASE_DIR / "extracted_images"

# 출력 디렉토리 생성
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

def extract_images_from_pdf(pdf_path):
    """PDF 파일에서 이미지를 추출하는 함수"""
    logger.info(f"이미지 추출을 시작합니다: {pdf_path}")
    
    # PDF 파일 열기
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        logger.info(f"PDF 파일을 성공적으로 열었습니다. 총 {total_pages}페이지가 있습니다.")
    except Exception as e:
        logger.error(f"PDF 파일을 열 수 없습니다: {str(e)}")
        return []
    
    saved_images = []
    
    # 각 페이지에서 이미지 추출
    for page_num in range(total_pages):
        try:
            page = doc.load_page(page_num)  # 0-based 인덱스
            image_list = page.get_images(full=True)
            
            if not image_list:
                logger.info(f"  - {page_num + 1}페이지: 이미지가 없습니다.")
                continue
            
            logger.info(f"  - {page_num + 1}페이지: {len(image_list)}개의 이미지를 찾았습니다.")
            
            # 이미지 추출
            for img_index, img in enumerate(image_list, 1):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # 이미지 확장자 확인 (기본값: png)
                    image_ext = base_image.get("ext", "png")
                    if not image_ext.startswith('.'):
                        image_ext = f".{image_ext}"
                    
                    # 이미지 저장
                    img_filename = f"{Path(pdf_path).stem}_p{page_num + 1}_img{img_index}{image_ext}"
                    img_path = OUTPUT_DIR / img_filename
                    
                    with open(img_path, 'wb') as f:
                        f.write(image_bytes)
                    
                    saved_images.append(str(img_path))
                    logger.info(f"    - 이미지 저장됨: {img_filename} ({len(image_bytes):,} bytes)")
                    
                except Exception as img_e:
                    logger.error(f"    - 이미지 {img_index} 추출 중 오류: {str(img_e)}")
        
        except Exception as page_e:
            logger.error(f"  - {page_num + 1}페이지 처리 중 오류: {str(page_e)}")
    
    # 문서 닫기
    doc.close()
    
    logger.info(f"이미지 추출이 완료되었습니다. 총 {len(saved_images)}개의 이미지가 추출되었습니다.")
    return saved_images

def main():
    print("="*50)
    print("PDF에서 이미지 추출을 시작합니다...")
    print("="*50)
    
    # Data 디렉토리에서 PDF 파일 찾기
    pdf_files = list(DATA_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print("\n[경고] Data 디렉토리에 PDF 파일이 없습니다.")
        return
    
    total_images = 0
    
    # 각 PDF 파일에 대해 이미지 추출 실행
    for pdf_path in pdf_files:
        print(f"\n[처리 중] {pdf_path.name}")
        saved_images = extract_images_from_pdf(pdf_path)
        total_images += len(saved_images)
    
    # 요약 출력
    print("\n" + "="*50)
    print("이미지 추출이 완료되었습니다!")
    print(f"- 처리된 PDF 파일 수: {len(pdf_files)}")
    print(f"- 추출된 이미지 수: {total_images}")
    print(f"- 이미지 저장 경로: {OUTPUT_DIR.absolute()}")
    print("="*50)

if __name__ == "__main__":
    main()
