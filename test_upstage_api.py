import os
import base64
import requests
from dotenv import load_dotenv
from pathlib import Path

# 환경 변수 로드
load_dotenv()

# 업스테이지 API 키 설정
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
if not UPSTAGE_API_KEY:
    raise ValueError("UPSTAGE_API_KEY가 환경 변수에 설정되어 있지 않습니다.")

def test_upstage_api():
    """업스테이지 API 연결을 테스트하는 함수"""
    print("업스테이지 API 연결을 테스트합니다...")
    
    # 테스트용 PDF 파일 경로 (간단한 PDF 파일)
    test_pdf_path = "Data/ai-cities-r.pdf"
    
    if not os.path.exists(test_pdf_path):
        print(f"테스트용 PDF 파일을 찾을 수 없습니다: {test_pdf_path}")
        return False
    
    # 파일을 base64로 인코딩
    with open(test_pdf_path, 'rb') as f:
        file_content = f.read()
    
    base64_content = base64.b64encode(file_content).decode('utf-8')
    
    # API 요청 본문
    payload = {
        "document": f"data:application/pdf;base64,{base64_content}",
        "extract_image": False,  # 이미지 추출 없이 텍스트만 추출
        "image_quality": "high"
    }
    
    # API 엔드포인트 (이전에 성공했던 버전)
    url = "https://api.upstage.ai/v1/document-ai/v1/ocr"
    
    # 요청 헤더
    headers = {
        "Authorization": f"Bearer {UPSTAGE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        print("API에 요청을 보내는 중...")
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # 응답 확인
        print(f"응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 업스테이지 API에 성공적으로 연결되었습니다!")
            print("응답 샘플:", response.text[:200] + "...")  # 응답의 처음 200자만 출력
            return True
        else:
            print(f"❌ API 요청 실패 (상태 코드: {response.status_code}): {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 중 오류 발생: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        return False

if __name__ == "__main__":
    test_upstage_api()
