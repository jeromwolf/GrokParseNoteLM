#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
문서 처리 테스트 스크립트
- PDF 및 MD 파일 처리
- 업스테이지 Document Parser 사용
- OpenAI LLM을 통한 요약 생성
- 중복 요약 문제 검증
"""

import os
import json
import shutil
import logging
import requests
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('test_comparison')

# 설정
BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
DATA_DIR = BASE_DIR / 'Data'
WORKSPACE_DIR = BASE_DIR / 'workspace'
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = WORKSPACE_DIR / f'output_{TIMESTAMP}'

# 업스테이지 API 설정
UPSTAGE_API_BASE = "https://api.upstage.ai/v1/apps"
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")
UPSTAGE_DOC_PARSER_ENDPOINT = f"{UPSTAGE_API_BASE}/document-parser"

# OpenAI API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def create_output_dirs():
    """출력 디렉토리 생성"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR / "text", exist_ok=True)
    os.makedirs(OUTPUT_DIR / "images", exist_ok=True)
    os.makedirs(OUTPUT_DIR / "summaries", exist_ok=True)
    return OUTPUT_DIR


def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """업스테이지 Document Parser를 사용하여 PDF에서 텍스트 추출"""
    logger.info(f"PDF 텍스트 추출 시작: {pdf_path}")
    
    if not UPSTAGE_API_KEY:
        raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")
    
    # PDF 파일 읽기
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    
    # 업스테이지 API 호출 헤더
    headers = {
        "Authorization": f"Bearer {UPSTAGE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # API 요청 데이터
    payload = {
        "inputs": {
            "file": base64.b64encode(pdf_data).decode("utf-8"),
            "parse_image": True,
            "extract_text": True
        }
    }
    
    # API 호출
    response = requests.post(UPSTAGE_DOC_PARSER_ENDPOINT, headers=headers, json=payload)
    
    if response.status_code != 200:
        logger.error(f"API 오류: {response.status_code}, {response.text}")
        raise Exception(f"업스테이지 API 호출 실패: {response.text}")
    
    # 응답 처리
    result = response.json()
    
    extracted_text = result["outputs"]["text"]
    logger.info(f"텍스트 추출 완료: {len(extracted_text)} 자")
    
    # 이미지 처리
    images = result["outputs"].get("images", [])
    logger.info(f"이미지 추출 완료: {len(images)}개")
    
    return {
        "text": extracted_text,
        "images": images,
        "raw_response": result
    }


def extract_text_from_md(md_path: str) -> Dict[str, Any]:
    """마크다운 파일에서 텍스트 추출"""
    logger.info(f"마크다운 파일 읽기: {md_path}")
    
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        
        return {
            "text": md_content,
            "images": [],
            "raw_response": {"source": "markdown"}
        }
    except Exception as e:
        logger.error(f"마크다운 파일 읽기 실패: {str(e)}")
        raise


def generate_summary_with_openai(text: str, model_name: str = "gpt-4-turbo-preview") -> str:
    """OpenAI 모델을 사용하여 텍스트 요약 생성"""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
    
    import openai
    openai.api_key = OPENAI_API_KEY
    
    # 텍스트가 너무 길면 앞부분만 사용
    max_tokens = 12000  # GPT-4-turbo 토큰 제한 고려
    truncated_text = text[:max_tokens * 4]  # 대략적인 토큰 수 계산 (영어 기준 4자당 1토큰)
    
    logger.info(f"OpenAI 요약 생성 시작 (모델: {model_name})")
    
    try:
        response = openai.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "다음 내용을 객관적이고 정보가 풍부하게 요약해주세요. 원문의 핵심 내용만 추출하여 400-600자 내외로 요약하세요."},
                {"role": "user", "content": truncated_text}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        summary = response.choices[0].message.content.strip()
        logger.info(f"요약 생성 완료: {len(summary)} 자")
        return summary
    
    except Exception as e:
        logger.error(f"OpenAI 요약 생성 실패: {str(e)}")
        raise


def process_document(file_path: str, output_dir: Path, use_openai: bool = True):
    """문서 처리 메인 함수"""
    file_path = Path(file_path)
    filename = file_path.name
    ext = file_path.suffix.lower()
    
    doc_output_dir = output_dir / filename.replace('.', '_')
    os.makedirs(doc_output_dir, exist_ok=True)
    os.makedirs(doc_output_dir / "images", exist_ok=True)
    
    logger.info(f"====== 문서 처리 시작: {filename} ======")
    
    # 문서 타입에 따른 처리
    if ext == '.pdf':
        extracted = extract_text_from_pdf(str(file_path))
    elif ext in ['.md', '.markdown']:
        extracted = extract_text_from_md(str(file_path))
    else:
        logger.error(f"지원하지 않는 파일 형식: {ext}")
        return None
    
    # 텍스트 저장
    text_file = doc_output_dir / "text.txt"
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(extracted["text"])
    logger.info(f"텍스트 저장 완료: {text_file}")
    
    # 이미지 저장
    for i, img_data in enumerate(extracted["images"]):
        img_path = doc_output_dir / "images" / f"image_{i+1}.png"
        try:
            img_bytes = base64.b64decode(img_data["image"])
            with open(img_path, "wb") as f:
                f.write(img_bytes)
            logger.info(f"이미지 저장 완료: {img_path}")
        except Exception as e:
            logger.error(f"이미지 저장 실패: {str(e)}")
    
    # 요약 생성
    summary = None
    if use_openai and extracted["text"]:
        try:
            summary = generate_summary_with_openai(extracted["text"])
            summary_file = doc_output_dir / "summary.md"
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(f"# {filename} 요약\n\n{summary}")
            logger.info(f"요약 저장 완료: {summary_file}")
        except Exception as e:
            logger.error(f"요약 생성 실패: {str(e)}")
    
    # 전체 결과 저장
    results = {
        "filename": filename,
        "text_length": len(extracted["text"]),
        "image_count": len(extracted["images"]),
        "summary": summary,
        "processing_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    results_file = doc_output_dir / "results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"====== 문서 처리 완료: {filename} ======\n")
    return results


def generate_combined_markdown(processed_docs: List[Dict[str, Any]], output_dir: Path):
    """처리된 모든 문서의 결과를 하나의 마크다운 파일로 통합"""
    logger.info("통합 마크다운 생성 시작")
    
    combined_markdown = "# 문서 처리 결과 통합 보고서\n\n"
    combined_markdown += f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    combined_markdown += f"처리된 문서: {len(processed_docs)}개\n\n"
    
    # 문서별 결과 추가
    for doc in processed_docs:
        combined_markdown += f"## {doc['filename']}\n\n"
        combined_markdown += f"### 문서 정보\n"
        combined_markdown += f"- **파일명**: {doc['filename']}\n"
        combined_markdown += f"- **텍스트 길이**: {doc['text_length']} 자\n"
        combined_markdown += f"- **이미지 수**: {doc['image_count']}개\n"
        combined_markdown += f"- **처리 시간**: {doc['processing_time']}\n\n"
        
        # 요약 내용 추가 (한 번만)
        if doc.get('summary'):
            combined_markdown += f"### 요약\n```\n{doc['summary']}\n```\n\n"
    
    # 파일 저장
    output_file = output_dir / "combined_results.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(combined_markdown)
    
    logger.info(f"통합 마크다운 생성 완료: {output_file}")
    return output_file


def main():
    """메인 함수"""
    import base64  # PDF 처리에 필요
    
    parser = argparse.ArgumentParser(description='문서 처리 테스트')
    parser.add_argument('--files', nargs='+', help='처리할 파일 경로')
    parser.add_argument('--no-openai', action='store_true', help='OpenAI 요약 비활성화')
    args = parser.parse_args()
    
    # 출력 디렉토리 생성
    output_dir = create_output_dirs()
    logger.info(f"출력 디렉토리: {output_dir}")
    
    # 처리할 파일 목록 생성
    files_to_process = []
    if args.files:
        for file_path in args.files:
            files_to_process.append(Path(file_path))
    else:
        # 기본적으로 Data 디렉토리의 PDF와 MD 파일 모두 처리
        for ext in ['.pdf', '.md']:
            files_to_process.extend(list(DATA_DIR.glob(f'*{ext}')))
    
    logger.info(f"처리할 파일: {[f.name for f in files_to_process]}")
    
    # 문서 처리
    processed_results = []
    for file_path in files_to_process:
        try:
            result = process_document(file_path, output_dir, use_openai=not args.no_openai)
            if result:
                processed_results.append(result)
        except Exception as e:
            logger.error(f"{file_path.name} 처리 중 오류 발생: {str(e)}")
    
    # 통합 마크다운 생성
    if processed_results:
        generate_combined_markdown(processed_results, output_dir)
    
    logger.info("테스트 완료!")

if __name__ == "__main__":
    main()
