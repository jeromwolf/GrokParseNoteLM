# GrokParseNoteLM

## 📋 프로젝트 소개
GrokParseNoteLM은 다양한 AI 모델을 활용한 PDF 문서 파싱 및 요약 도구입니다. PDF 문서에서 텍스트와 이미지를 추출하고, 여러 AI 모델(OpenAI, Llama, Upstage, Gemini)을 사용하여 한국어로 요약합니다.

## 🚀 프로젝트 개요

### 📌 최신 업데이트 (2025-05-20)
- **다중 모델 지원**
  - OpenAI (GPT-4 Turbo): 상세하고 구조화된 한국어 요약 생성
  - Llama (llama3): 로컬에서 실행되는 빠른 한국어 요약 생성
  - Upstage, Gemini 모델 지원 준비 중
- **PDF 처리 기능 강화**
  - 긴 PDF 문서를 청크로 분할하여 처리
  - 각 청크별 요약 후 최종 병합
  - 모델별 최적 청크 크기 자동 설정
- **개선된 디버깅 및 로깅**
  - 상세한 진행 상황 표시
  - 처리 시간 측정 및 표시
  - 청크 분할 및 병합 과정 로깅

### 📅 개발 일정
- **개발 기간**: 6일 (5/20 ~ 5/25)
- **현재 진행 상황**:
  - [x] PDF 파싱 및 이미지 추출 기능 구현
  - [x] 다중 AI 모델 지원 (OpenAI, Llama)
  - [x] 긴 PDF 문서 처리 기능 개선
  - [ ] 이미지 분석 기능 구현 (MCP 이미지 리더)
  - [ ] 웹 인터페이스 개발

### ✨ 주요 기능
- **PDF 파싱**
  - 업스테이지 Document Parser API를 활용한 고정확도 PDF 텍스트 및 이미지 추출
  - 빠른 처리 속도와 정확한 문서 구조 분석
- **다중 AI 모델 지원**
  - OpenAI (GPT-4 Turbo): 상세하고 구조화된 한국어 요약
  - Llama (llama3): 로컬에서 실행되는 빠른 한국어 요약
  - Upstage, Gemini 모델 지원 준비 중
- **이미지 처리**
  - PDF 내 이미지 자동 추출 및 저장
  - 이미지 분석 기능 개발 중 (MCP 이미지 리더)

## 🛠️ 기술 스택
- **백엔드**: Python
- **PDF 처리**: 업스테이지 Document Parser API
- **AI 모델**:
  - OpenAI API (GPT-4 Turbo)
  - Ollama API (Llama3)
  - Upstage API (Solar)
  - Google Gemini API
- **이미지 처리**: MCP 이미지 리더 (개발 중)
- **추가 라이브러리**: requests, os, datetime, dotenv

## 📋 사용 방법

### 기본 사용법
```bash
python main.py <PDF경로> --model <모델명> --output-dir <출력디렉토리>
```

### 예시
```bash
# OpenAI 모델 사용
python main.py Data/sample.pdf --model openai --model-name gpt-4-turbo-preview --output-dir output/openai_test

# Llama 모델 사용
python main.py Data/sample.pdf --model llama --model-name llama3:latest --output-dir output/llama_test
```

### 주요 파라미터
- `--model`: 사용할 모델 (openai, llama, upstage, gemini)
- `--model-name`: 모델 이름 (선택적)
- `--output-dir`: 출력 디렉토리 (기본값: output/)

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
- **OpenAI (GPT-4 Turbo)**: 상세하고 구조화된 요약, 높은 정확도
- **Llama (llama3)**: 간결한 요약, 빠른 처리 속도, 로컬 실행

### 처리 시간 (MCPregister.pdf 기준)
- **OpenAI**: 약 1분 30초
- **Llama**: 약 1분 30초
