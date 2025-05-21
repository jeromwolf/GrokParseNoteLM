# GrokParseNoteLM

## 📋 프로젝트 소개
GrokParseNoteLM은 다양한 AI 모델을 활용한 다중 문서 파싱 및 요약 도구입니다. PDF 및 텍스트 문서에서 텍스트와 이미지를 추출하고, 여러 AI 모델(OpenAI, Llama, Upstage, Gemini)을 사용하여 한국어로 요약합니다. 업스테이지 Document Parser API를 주요 파서로 사용하며, 실패 시 PyMuPDF를 백업 파서로 활용하는 견고한 아키텍처를 갖추고 있습니다. 또한 여러 문서를 동시에 처리하고 통합 분석할 수 있는 노트북 기능을 제공합니다.

## 🚀 프로젝트 개요

### 📌 최신 업데이트 (2025-05-21)
- **다중 문서 분석 기능 추가**
  - `DocumentsManager` 클래스를 통한 다중 문서 관리 기능 구현
  - 여러 문서의 분석 결과를 하나의 마크다운으로 통합하는 기능
  - 문서별 메타데이터 관리 및 추적

- **질의 엔진 개선**
  - `QueryEngine`을 통한 LLM 기반 질의 기능 구현
  - 문서 컨텍스트를 고려한 정확한 응답 생성
  - 쿼리 결과를 마크다운 및 JSON 형식으로 저장

- **문서 처리 개선**
  - `generate_combined_markdown` 메서드 개선으로 문서 요약 정보 강화
  - 이미지 분석 결과를 포함한 통합 마크다운 생성
  - 문서 처리 파이프라인 안정성 향상

- **프로젝트 관리**
  - `workspace` 디렉토리를 `.gitignore`에 추가
  - 불필요한 `output` 디렉토리 제거
  - 코드 리팩토링 및 문서화 개선

### 📌 이전 업데이트 (2025-05-20)
- **다중 모델 지원**
  - OpenAI (GPT-4 Turbo): 상세하고 구조화된 한국어 요약 생성
  - Llama (llama3): 로컬에서 실행되는 빠른 한국어 요약 생성 (한국어 프롬프트 최적화)
  - Upstage (Solar): 고품질 한국어 요약 생성
  - Gemini 모델 지원 준비 중
- **이중 PDF 파서 시스템**
  - 업스테이지 Document Parser API: 주요 파서
  - PyMuPDF: 백업 파서 (API 실패 시 자동 전환)
- **PDF 처리 기능 강화**
  - 긴 PDF 문서를 청크로 분할하여 처리
  - 각 청크별 요약 후 최종 병합
  - 모델별 최적 청크 크기 자동 설정
- **개선된 디버깅 및 로깅**
  - 상세한 진행 상황 표시
  - 처리 시간 측정 및 표시
  - 사용된 파서 정보 로깅
  - 오류 발생 시 명확한 메시지 제공

### 📅 개발 일정
- **개발 기간**: 6일 (5/20 ~ 5/25)
- **현재 진행 상황**:
  - [x] PDF 파싱 및 이미지 추출 기능 구현
  - [x] 다중 AI 모델 지원 (OpenAI, Llama, Upstage)
  - [x] 긴 PDF 문서 처리 기능 개선
  - [x] 이중 PDF 파서 시스템 구현 (업스테이지 API + PyMuPDF 백업)
  - [x] Llama 모델 한국어 요약 최적화
  - [x] 이미지 분석 기능 구현 (OCR 서버)
  - [x] 여러 문서 통합 처리 및 분석 기능 구현
  - [x] 문서 기반 질의응답 기능 구현
  - [ ] 웹 인터페이스 개발

### ✨ 주요 기능
- **이중 PDF 파싱 시스템**
  - **업스테이지 Document Parser API**: 고정확도 PDF 텍스트 및 이미지 추출 (주요 파서)
  - **PyMuPDF**: 빠르고 안정적인 로컬 PDF 처리 (백업 파서)
  - 자동 전환 메커니즘: API 실패 시 자동으로 PyMuPDF로 전환
- **다중 AI 모델 지원**
  - **OpenAI (GPT-4 Turbo)**: 상세하고 구조화된 한국어 요약
  - **Llama (llama3)**: 로컬에서 실행되는 빠른 한국어 요약 (한국어 프롬프트 최적화)
  - **Upstage (Solar)**: 고품질 한국어 요약
  - Gemini 모델 지원 준비 중
- **이미지 처리**
  - PDF 내 이미지 자동 추출 및 저장
  - **OCR 서버**: FastAPI와 Tesseract를 활용한 이미지 텍스트 추출
  - 이미지 분석 결과를 마크다운 형식으로 통합
- **다중 문서 처리**
  - 여러 PDF 및 텍스트 문서 동시 처리
  - 문서 관리 시스템: 추가, 제거, 목록 조회 기능
  - 처리된 문서의 통합 결과 생성
- **문서 기반 질의응답**
  - 처리된 여러 문서의 통합 결과를 바탕으로 LLM에 질의
  - 컨텍스트 길이 자동 조절
  - 질의와 응답 결과 저장
- **오류 처리 및 로깅**
  - API 호출 실패 시 자세한 오류 메시지 제공
  - 사용된 파서 정보 로깅
  - 처리 과정 상세 로깅

## 🛠️ 기술 스택
- **백엔드**: Python
- **PDF 처리**:
  - 업스테이지 Document Parser API (주요 파서)
  - PyMuPDF (백업 파서)
- **AI 모델**:
  - OpenAI API (GPT-4 Turbo)
  - Ollama API (Llama3)
  - Upstage API (Solar)
  - Google Gemini API
- **이미지 처리**: MCP 이미지 리더 (개발 중)
- **추가 라이브러리**: requests, os, datetime, dotenv, json, fitz (PyMuPDF)

## 📋 사용 방법

### 1. 단일 PDF 처리 (기존 기능)
```bash
python main.py <PDF경로> --model <모델명> --output-dir <출력디렉토리>
```

#### 예시
```bash
# OpenAI 모델 사용
python main.py Data/sample.pdf --model openai --model-name gpt-4-turbo-preview --output-dir output/openai_test

# Llama 모델 사용
python main.py Data/sample.pdf --model llama --model-name llama3:latest --output-dir output/llama_test
```

#### 주요 파라미터
- `--model`: 사용할 모델 (openai, llama, upstage, gemini)
- `--model-name`: 모델 이름 (선택적)
- `--output-dir`: 출력 디렉토리 (기본값: output/)
- `--parser`: 사용할 PDF 파서 (upstage, pymupdf) - 미지정 시 업스테이지 API 우선 사용, 실패 시 PyMuPDF 자동 전환
- `--language`: 요약 언어 (ko, en) - 기본값: ko (한국어)

### 2. 다중 문서 처리 (새로운 기능)

#### 문서 관리
```bash
# 문서 추가
python notebook_app.py add <문서경로1> <문서경로2> ...

# 문서 목록 조회
python notebook_app.py list

# 문서 제거
python notebook_app.py remove <문서_ID>
```

#### 문서 처리
```bash
# 모든 문서 처리
python notebook_app.py process --model-type openai --model-name gpt-4-turbo-preview

# 특정 문서만 처리
python notebook_app.py process --doc-ids <문서_ID1> <문서_ID2> --model-type openai
```

#### 통합 결과 생성
```bash
# 처리된 모든 문서의 통합 결과 생성
python notebook_app.py combine
```

#### 문서 기반 질의응답
```bash
# 처리된 문서를 바탕으로 질의
python notebook_app.py query "여기에 질문을 입력하세요" --model-type openai
```

#### 주요 파라미터
- `--workspace`: 작업 디렉토리 (기본값: workspace)
- `--model-type`: 사용할 모델 타입 (openai, llama, upstage, gemini)
- `--model-name`: 사용할 모델 이름
- `--parser`: PDF 파서 (auto, upstage, pymupdf)
- `--language`: 언어 (ko, en)
- `--ocr-language`: OCR 언어 (kor+eng, eng 등)

## 🎯 향후 계획
- **이미지 분석 기능 구현**
  - MCP 이미지 리더를 활용한 이미지 OCR 및 분석
  - 이미지 내용을 요약에 통합
- **병렬 처리 최적화**
  - 여러 청크를 동시에 처리하여 속도 향상
  - 다중 모델 병렬 처리
- **웹 인터페이스 개발**
  - PDF 업로드 및 모델 선택 UI
  - 요약 결과 시각화
  - 이미지 갤러리 뷰
- **추가 모델 지원**
  - Claude, Mistral 등 다양한 모델 통합
  - 모델 성능 비교 기능

## 📊 성능 비교

### 모델별 요약 품질
- **OpenAI (GPT-4 Turbo)**: 상세하고 구조화된 요약, 높은 정확도, 우수한 한국어 품질
- **Llama (llama3)**: 간결한 요약, 빠른 처리 속도, 로컬 실행, 한국어 프롬프트 최적화 후 품질 향상
- **Upstage (Solar)**: 한국어에 최적화된 요약, 중간 수준의 처리 속도

### PDF 파서 비교
- **업스테이지 Document Parser API**: 고품질 텍스트 추출, 정확한 이미지 추출, API 비용 발생
- **PyMuPDF**: 빠른 처리 속도, 안정적인 로컬 처리, 무료 사용, 복잡한 레이아웃에서 정확도 다소 낮음

### 처리 시간 (pdftest.pdf 기준)
- **OpenAI**: 약 1분 30초
- **Llama**: 약 1분 30초
- **Upstage**: 약 2분 (API 호출 시간 포함)

## 🧪 테스트 가이드

### 1. 기본 워크플로우 테스트 (notebook_app.py 사용)

#### 1-1. 문서 추가
```bash
# PDF나 MD 파일을 추가 
python notebook_app.py add [파일경로1] [파일경로2] ...

# 예시: Data 폴더의 PDF와 MD 추가
python notebook_app.py add Data/ontology.pdf Data/ontology.md
```

#### 1-2. 문서 목록 확인
```bash
python notebook_app.py list
```

#### 1-3. 문서 처리 (OpenAI LLM 사용)
```bash
# OpenAI 모델로 처리
python notebook_app.py process --parser upstage --model-type openai --model-name gpt-4-turbo-preview

# Llama 모델로 처리하려면
python notebook_app.py process --parser upstage --model-type llama --model-name llama-2-70b
```

#### 1-4. 처리 결과 통합
```bash
python notebook_app.py combine
# 결과는 workspace/combined_results.md에 저장됨
```

#### 1-5. 질의응답 생성
```bash
python notebook_app.py query "질문 내용" --model-type openai --model-name gpt-4-turbo-preview
# 결과는 workspace/query_results_[timestamp]/query_result.md에 저장됨
```

### 2. 이미지 분석 서버 테스트 (FastAPI/Tesseract OCR)

#### 2-1. 이미지 분석 서버 시작
```bash
# 포트 5050에서 FastAPI 서버 실행
python simple_image_reader.py
```

#### 2-2. 이미지 분석 API 테스트
```bash
# 단일 이미지 OCR
curl -X POST "http://localhost:5050/analyze_image" -F "file=@이미지경로.png"

# 디렉토리 일괄 분석
curl -X POST "http://localhost:5050/analyze_directory" -d '{"directory_path": "이미지디렉토리경로"}'
```

### 3. 특수 상황 테스트

#### 3-1. 문서 중복 요약 문제 검증
```bash
# 통합 마크다운 생성 후 결과 확인
python notebook_app.py combine
cat workspace/combined_results.md
# 각 문서마다 요약이 한 번만 표시되는지 확인
```

#### 3-2. 이미지가 없는 PDF 테스트
```bash
# 이미지가 없는 PDF 처리 테스트
python notebook_app.py add Data/ontology.pdf
python notebook_app.py process --parser upstage --model-type openai
# 결과: 이미지 0개 메시지 확인
```

#### 3-3. 대용량 PDF 테스트
```bash
# 대용량/이미지가 많은 PDF 처리 (큰 PDF가 있는 경우)
python main.py 대용량PDF경로 --model openai --parser upstage --output-dir 출력디렉토리
```

### 4. 디버깅 팁
- 로그 확인: 로깅이 INFO 레벨로 설정되어 있어 대부분의 진행 상황을 터미널에서 확인 가능
- 중간 결과 확인: workspace/output/ 디렉토리에서 각 문서별 중간 결과물 확인 가능
- API 키 문제: `.env` 파일에 UPSTAGE_API_KEY, OPENAI_API_KEY가 올바르게 설정되어 있는지 확인

### 5. 주의사항
- API 키 관리: UPSTAGE_API_KEY, OPENAI_API_KEY 환경변수 설정 필요
- 이미지 서버: 포트 5050 사용, 다른 서비스와 충돌 여부 확인
- 파일 경로: 상대 경로보다 절대 경로 사용 권장
- 요약 중복 문제: document_manager.py의 generate_combined_markdown 함수에서 해결됨
- OCR 결과: 이미지 품질에 따라 결과 변동 가능
