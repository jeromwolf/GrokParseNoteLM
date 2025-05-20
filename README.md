# GrokParseNoteLM

## 📋 프로젝트 소개
GrokParseNoteLM은 업스테이지 Document Parse API를 활용한 NotebookLM 스타일의 문서 파싱 도구입니다. PDF 문서를 자동으로 파싱하여 NotebookLM과 유사한 UI로 결과를 표시합니다.

## 🚀 프로젝트 개요

### 📌 최신 업데이트 (2025-05-20)
- **PDF 파싱 기능**
  - PDF에서 텍스트 및 이미지 추출
  - 업스테이지 Solar API를 활용한 한국어 요약
  - `output/{PDF이름}_{타임스탬프}/` 형식으로 자동 저장
  - 이미지 파일은 `images/` 하위 폴더에 저장
  - 요약 결과는 `summary.txt`로 저장
  - `.gitignore`에 `output/` 디렉토리 추가

### 📅 개발 일정
- **개발 기간**: 6일 (5/20 ~ 5/25)
- **현재 진행 상황**:
  - [x] PDF 파싱 및 요약 기능 구현
  - [ ] 웹 인터페이스 개발
  - [ ] 추가 기능 구현

### ✨ 주요 기능
- **PDF 파싱**
  - 업스테이지 Document Parse API를 통한 고정확도 PDF 파싱
  - 빠른 처리 속도
- **문서 요약**
  - 업스테이지 Solar API를 활용한 한국어 요약
  - 구조화된 형식의 요약 결과 제공
- **이미지 처리**
  - PDF 내 이미지 추출 및 저장
  - 이미지별 분류 및 관리

## 🛠️ 기술 스택
- **백엔드**: Python (Flask)
- **프론트엔드**: HTML, CSS (Tailwind CSS)
- **API**: 업스테이지 Document Parse API
- **추가 라이브러리**: requests, spaCy

## 📋 주요 기능
- **문서 파싱**:
  - 업스테이지 Document Parse API를 통한 고정확도 PDF 파싱
  - 빠른 처리 속도
- **UI/UX**:
  - 좌측: 소스 업로드 패널
  - 우측: 파싱 결과 표시
  - 직관적이고 사용자 친화적인 인터페이스

## 🎯 향후 계획
- 질문 응답 시스템 추가
- 오디오 요약 기능 구현
- 웹 소스 검색 기능 확장
- UI/UX 개선
