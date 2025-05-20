# pip install requests
import os
import requests
import json
from dotenv import load_dotenv
from pathlib import Path
import base64

# 환경 변수 로드
load_dotenv()

# API 키 확인
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
if not UPSTAGE_API_KEY:
    raise ValueError("UPSTAGE_API_KEY가 환경 변수에 설정되어 있지 않습니다.")

def analyze_document(file_path, is_image=False):
    """문서 또는 이미지를 분석하는 함수"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    file_type = "이미지" if is_image else "PDF"
    print(f"\n{'='*50}")
    print(f"{file_type} 파일 분석을 시작합니다...")
    print(f"파일: {file_path} (크기: {os.path.getsize(file_path) / 1024:.2f} KB)")
    
    # API 엔드포인트 설정 (이미지와 문서를 구분)
    url = "https://api.upstage.ai/v1/document-digitization"
    
    # 요청 헤더
    headers = {
        "Authorization": f"Bearer {UPSTAGE_API_KEY}"
    }
    
    # 파일 MIME 타입 설정
    mime_type = "image/jpeg" if is_image else "application/pdf"
    
    # 파일 열기 및 전송
    with open(file_path, "rb") as f:
        files = {"document": (os.path.basename(file_path), f, mime_type)}
        
        # 요청 파라미터 (이미지의 경우 OCR 강제 적용)
        data = {
            "ocr": "force",
            "model": "document-parse"
        }
        
        if is_image:
            # 이미지의 경우 OCR 강제 적용 (최소한의 파라미터만 사용)
            data = {
                "ocr": "force"
            }
        
        print(f"API에 요청을 보내는 중...")
        try:
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=120
            )
            
            # 응답 처리
            print(f"\n응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # 결과를 파일로 저장
                output_file = f"upstage_{'image' if is_image else 'doc'}_result.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"✅ 결과가 {output_file}에 저장되었습니다.")
                
                # 이미지 분석 결과가 있는지 확인
                if is_image and 'content' in result and 'images' in result['content']:
                    print("\n이미지 분석 결과:")
                    for i, img in enumerate(result['content']['images']):
                        print(f"  - 이미지 {i+1}: {img.get('type', '알 수 없는 유형')}")
                        if 'text' in img:
                            print(f"    추출된 텍스트: {img['text'][:100]}..." if len(img['text']) > 100 else img['text'])
                
                return result
                
            else:
                print(f"❌ API 요청 실패: {response.status_code}")
                print(f"응답 내용: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 요청 중 오류 발생: {str(e)}")
            return None

# 테스트 실행
if __name__ == "__main__":
    # 1. PDF 문서 분석 테스트
    test_pdf_path = "Data/ai-cities-r.pdf"
    analyze_document(test_pdf_path, is_image=False)
    
    # 2. 이미지 분석 테스트 (추출된 이미지 사용)
    test_image_path = "extracted_images/ai-cities-r_p1_img1.jpeg"  # 첫 번째 추출된 이미지 사용
    if os.path.exists(test_image_path):
        print(f"\n이미지 분석을 시작합니다: {test_image_path}")
        image_result = analyze_document(test_image_path, is_image=True)
        
        # 이미지 분석 결과를 LLM에 전달하여 설명 요청
        if image_result and 'content' in image_result and 'text' in image_result['content']:
            extracted_text = image_result['content']['text']
            print("\n추출된 텍스트:")
            print("-" * 50)
            print(extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text)
            print("-" * 50)
            
            # 여기에 LLM을 호출하여 이미지 설명을 생성하는 코드를 추가할 수 있습니다.
            # 예: generate_image_description(extracted_text)
    else:
        print(f"\n⚠️ 테스트 이미지 파일을 찾을 수 없습니다: {test_image_path}")
