import os
import requests
from pathlib import Path

def download_file(url: str, save_path: Path) -> bool:
    """URL에서 파일을 다운로드하여 지정된 경로에 저장"""
    try:
        # 디렉토리 생성
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 파일 다운로드
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()  # 오류가 발생하면 예외 발생
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # 필터링하여 keep-alive와 같은 청크를 무시
                    f.write(chunk)
        
        print(f"파일이 성공적으로 다운로드되었습니다: {save_path} ({(save_path.stat().st_size / 1024):.2f} KB)")
        return True
        
    except Exception as e:
        print(f"다운로드 실패 ({url}): {str(e)}")
        return False

def main():
    # 테스트용 PDF 파일 URL (이미지가 포함된 샘플 PDF)
    test_pdf_urls = [
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/drawing.pdf",  # 도면이 포함된 PDF
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/ocr/ocr-p1.png.pdf",  # 스캔된 문서 (OCR 대상)
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/ocr/ocr-p2.png.pdf",  # 스캔된 문서 2
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/ocr/ocr-p3.png.pdf",  # 스캔된 문서 3
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/ocr/ocr-p4.png.pdf",  # 스캔된 문서 4
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/ocr/ocr-p5.png.pdf"   # 스캔된 문서 5
    ]
    
    # 다운로드 디렉토리 설정
    download_dir = Path("test_images_pdf")
    download_dir.mkdir(exist_ok=True)
    
    # 각 PDF 파일 다운로드
    downloaded_files = []
    for i, url in enumerate(test_pdf_urls, 1):
        filename = f"image_document_{i}.pdf"
        save_path = download_dir / filename
        
        if download_file(url, save_path):
            downloaded_files.append(save_path)
    
    # 다운로드된 파일 목록 출력
    if downloaded_files:
        print("\n다운로드 완료된 파일 목록:")
        for file_path in downloaded_files:
            print(f"- {file_path} ({(file_path.stat().st_size / 1024):.2f} KB)")
    else:
        print("다운로드에 실패했습니다.")

if __name__ == "__main__":
    main()
