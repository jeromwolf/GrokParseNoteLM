import requests
import json
import os

# 서버 URL 설정
SERVER_URL = "http://localhost:5050"

# 분석할 디렉토리 경로
IMAGE_DIR = "/Users/kelly/Desktop/Space/[2025]/GrokParseNoteLM/output/pdftest_OPENAI_20250520_223432/images"

# 디렉토리 분석 API 호출
response = requests.post(
    f"{SERVER_URL}/analyze/ocr/directory",
    params={
        'directory_path': IMAGE_DIR,
        'lang': 'kor+eng',
        'extensions': ['png', 'jpg', 'jpeg']
    }
)

# 응답 확인
if response.status_code == 200:
    results = response.json()
    
    # 결과 저장
    with open('ocr_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"분석 완료! 총 {results['file_count']}개 이미지 처리됨")
    print("결과가 ocr_results.json에 저장되었습니다.")
    
    # 일부 결과 출력
    for i, result in enumerate(results['results']):
        if i < 3:  # 처음 3개만 출력
            print(f"\n파일: {result['filename']}")
            if 'error' in result:
                print(f"오류: {result['error']}")
            else:
                text = result['text'].strip()
                print(f"텍스트: {text[:100]}..." if len(text) > 100 else f"텍스트: {text}")
        else:
            break
    
    print("\n모든 결과는 ocr_results.json 파일에서 확인하세요.")
else:
    print(f"오류 발생: {response.status_code}")
    print(response.text)
