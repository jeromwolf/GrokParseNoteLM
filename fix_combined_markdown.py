#!/usr/bin/env python3
import os
import re
import json
from datetime import datetime
from pathlib import Path

def fix_combined_markdown(workspace_dir="workspace"):
    """
    기존 요약 결과를 읽고 요약 중복을 제거한 새 통합 문서를 생성합니다.
    """
    workspace_dir = Path(workspace_dir)
    output_dir = workspace_dir / "output"
    
    # 처리된 모든 문서 디렉토리 찾기
    doc_dirs = []
    for item in os.listdir(output_dir):
        full_path = output_dir / item
        if full_path.is_dir():
            doc_dirs.append(full_path)
    
    if not doc_dirs:
        print("처리된 문서 디렉토리를 찾을 수 없습니다.")
        return
    
    # 통합 마크다운 시작
    markdown = "# 통합 문서 분석 결과 (수정됨)\n\n"
    markdown += f"처리 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    markdown += f"총 문서 수: {len(doc_dirs)}\n\n"
    
    # 문서 목록
    markdown += "## 문서 목록\n\n"
    for i, doc_dir in enumerate(doc_dirs, 1):
        doc_name = doc_dir.name.split('_')[0]  # 디렉토리 이름에서 문서 이름 추출
        markdown += f"{i}. **{doc_name}**\n"
    markdown += "\n"
    
    # 각 문서 처리
    for i, doc_dir in enumerate(doc_dirs, 1):
        doc_name = doc_dir.name.split('_')[0]
        doc_type = "pdf" if "PDF" in doc_dir.name else "text"
        
        markdown += f"## 문서 {i}: {doc_name}\n\n"
        
        # 문서 정보 추가
        markdown += f"### 문서 정보\n"
        markdown += f"- **파일명**: {doc_name}\n"
        markdown += f"- **타입**: {doc_type}\n"
        markdown += f"- **출력 디렉토리**: {doc_dir}\n\n"
        
        # 요약 파일 찾기
        summary_content = None
        
        # summary.txt 또는 summary.md 파일 찾기
        for ext in ["txt", "md"]:
            summary_file = doc_dir / f"summary.{ext}"
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 요약 섹션 찾기
                summary_match = re.search(r'## 텍스트 요약\s+(.*?)(?=##|\Z)', content, re.DOTALL)
                if summary_match:
                    summary_content = summary_match.group(1).strip()
                else:
                    # 요약 섹션이 없으면 전체 내용을 1000자까지만 사용
                    content_clean = re.sub(r'```.*?```', '', content, flags=re.DOTALL)  # 코드 블록 제거
                    if len(content_clean) > 1000:
                        summary_content = content_clean[:1000] + "...\n\n(내용이 너무 깁니다. 일부만 표시합니다.)"
                    else:
                        summary_content = content_clean
                
                break
        
        # 요약 내용 추가 (단 한 번만)
        if summary_content:
            markdown += f"### 요약\n```\n{summary_content}\n```\n\n"
        else:
            markdown += "### 요약\n요약 정보를 찾을 수 없습니다.\n\n"
        
        # 이미지 정보 추가
        images_dir = doc_dir / "images"
        if images_dir.exists() and os.listdir(images_dir):
            image_count = len([f for f in os.listdir(images_dir) if f.endswith(('.png', '.jpg', '.jpeg'))])
            markdown += f"### 이미지 정보\n"
            markdown += f"- **이미지 수**: {image_count}개\n\n"
        else:
            markdown += f"### 이미지 정보\n"
            markdown += f"- **이미지 수**: 0개\n\n"
    
    # 통합 결과 저장
    combined_path = workspace_dir / "combined_results_fixed.md"
    with open(combined_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"통합 마크다운 생성 완료: {combined_path}")
    return combined_path

if __name__ == "__main__":
    fixed_path = fix_combined_markdown()
    if fixed_path:
        print(f"중복이 제거된 통합 마크다운을 생성했습니다: {fixed_path}")
    else:
        print("문제가 발생했습니다.")
