import os
import requests
from pathlib import Path

def download_file(url: str, save_path: Path) -> bool:
    """URL에서 파일을 다운로드하여 지정된 경로에 저장"""
    try:
        # 디렉토리 생성
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # GitHub의 경우 User-Agent를 설정해야 할 수 있음
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 파일 다운로드
        response = requests.get(url, stream=True, timeout=30, headers=headers)
        response.raise_for_status()  # 오류가 발생하면 예외 발생
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # 필터링하여 keep-alive와 같은 청크를 무시
                    f.write(chunk)
        
        file_size = save_path.stat().st_size / 1024
        print(f"파일이 성공적으로 다운로드되었습니다: {save_path} ({file_size:.2f} KB)")
        return True
        
    except Exception as e:
        print(f"다운로드 실패 ({url}): {str(e)}")
        return False

def main():
    # GitHub의 샘플 PDF 파일 URL (이미지가 포함된 샘플 PDF)
    github_raw_base = "https://raw.githubusercontent.com"
    test_pdf_urls = [
        f"{github_raw_base}/mozilla/pdf.js/ba2ede0/web/compressed.tracemonkey-pldi-09.pdf",  # PDF.js 데모 문서 (이미지 포함)
        f"{github_raw_base}/mozilla/pdf.js/ba2ede0/web/images/foxit.pdf",  # PDF.js 예제 문서
        "https://www.africau.edu/images/default/sample.pdf",  # 일반적으로 사용되는 샘플 PDF (이미지 포함)
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",  # W3C 테스트 PDF
        "https://www.africau.edu/images/default/sample.pdf"  # 중복 다운로드를 방지하기 위해 다른 URL 추가
    ]
    
    # 다운로드 디렉토리 설정
    download_dir = Path("test_pdfs_with_images")
    download_dir.mkdir(exist_ok=True)
    
    # 각 PDF 파일 다운로드 (중복 제거)
    downloaded_files = []
    for i, url in enumerate(test_pdf_urls, 1):
        # URL에서 파일명 추출
        filename = url.split("/")[-1]
        if not filename.lower().endswith('.pdf'):
            filename = f"document_{i}.pdf"
            
        save_path = download_dir / filename
        
        # 이미 다운로드한 파일은 건너뜀
        if save_path.exists():
            print(f"파일이 이미 존재합니다: {save_path}")
            downloaded_files.append(save_path)
            continue
            
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
