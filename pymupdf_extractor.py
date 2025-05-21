import fitz  # PyMuPDF
import os
import sys
from datetime import datetime

def extract_from_pdf(pdf_path, output_dir):
    """PDF 파일에서 텍스트와 이미지를 추출합니다.
    
    Args:
        pdf_path (str): PDF 파일 경로
        output_dir (str): 출력 디렉토리
    """
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # PDF 열기
    doc = fitz.open(pdf_path)
    
    print(f"PDF 페이지 수: {len(doc)}")
    
    # 텍스트 추출
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += f"\n--- Page {page_num + 1} ---\n"
        text += page.get_text()
    
    # 텍스트 저장
    text_file = os.path.join(output_dir, "extracted_text.txt")
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"추출된 텍스트가 저장되었습니다: {text_file}")
    
    # 이미지 추출
    image_count = 0
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        image_list = page.get_images(full=True)
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            image_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
            image_path = os.path.join(images_dir, image_filename)
            
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            
            image_count += 1
            print(f"이미지 저장됨: {image_path}")
    
    print(f"\n총 {image_count}개의 이미지를 추출했습니다.")
    print(f"결과가 저장된 디렉토리: {output_dir}")
    
    doc.close()
    return text, image_count

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python pymupdf_extractor.py <PDF 파일 경로> [출력 디렉토리]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output_pymupdf"
    
    # 타임스탬프 추가
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{output_dir}_{timestamp}"
    
    extract_from_pdf(pdf_path, output_dir)
