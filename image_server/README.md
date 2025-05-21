# FastAPI + Tesseract OCR 이미지 분석 서버

PDF에서 추출된 이미지를 분석하기 위한 FastAPI 기반 OCR 서버입니다.

## 기능

- 이미지 파일에서 텍스트 추출 (OCR)
- 단일 이미지 및 배치 처리 지원
- 서버 로컬 경로의 이미지 처리
- 디렉토리 내 모든 이미지 일괄 처리
- 다국어 OCR 지원 (영어, 한국어 등)

## 설치 방법

### 1. 요구 사항 설치

```bash
pip install -r requirements.txt
```

### 2. Tesseract OCR 설치

#### macOS:
```bash
brew install tesseract
# 한국어 지원을 위한 언어 데이터 설치 (선택 사항)
brew install tesseract-lang
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
# 한국어 지원을 위한 언어 데이터 설치 (선택 사항)
sudo apt-get install tesseract-ocr-kor
```

## 서버 실행

```bash
cd image_server
python server.py
```

서버는 기본적으로 http://localhost:5050 에서 실행됩니다.

## API 엔드포인트

- `GET /`: 서버 상태 확인
- `GET /health`: 서버 상태 체크
- `POST /analyze/ocr`: 단일 이미지 분석
- `POST /analyze/ocr/batch`: 여러 이미지 일괄 분석
- `POST /analyze/ocr/from_path`: 서버 로컬 경로의 이미지 분석
- `POST /analyze/ocr/directory`: 디렉토리 내 모든 이미지 분석

## 클라이언트 사용법

### 단일 이미지 분석
```bash
python client.py analyze path/to/image.jpg --lang eng
```

### 여러 이미지 일괄 분석
```bash
python client.py batch path/to/image1.jpg path/to/image2.jpg --lang eng
```

### 서버 로컬 경로의 이미지 분석
```bash
python client.py from_path /absolute/path/to/image.jpg --lang eng
```

### 디렉토리 내 모든 이미지 분석
```bash
python client.py directory /path/to/images/directory --lang eng
```

### 한국어 OCR 사용
```bash
python client.py analyze path/to/image.jpg --lang kor
```

### 결과를 파일로 저장
```bash
python client.py analyze path/to/image.jpg --output results.json
```

## PDF에서 추출된 이미지 분석 예시

PDF에서 추출된 이미지가 `output_pdftest/images/` 디렉토리에 있다고 가정할 때:

```bash
# 서버 실행
python server.py

# 다른 터미널에서 클라이언트 실행
python client.py directory /Users/kelly/Desktop/Space/[2025]/GrokParseNoteLM/output_pdftest/images --output ocr_results.json
```

## 참고사항

- 한국어 OCR을 사용하려면 Tesseract에 한국어 언어 데이터가 설치되어 있어야 합니다.
- 이미지 품질이 좋을수록 OCR 결과가 정확합니다.
- 대용량 이미지 처리 시 서버 메모리 사용량에 주의하세요.
