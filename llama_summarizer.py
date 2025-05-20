import os
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Optional, List
from datetime import datetime

def clean_text(text: str) -> str:
    """텍스트 정제"""
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', ' ', text)
    # 여러 공백을 하나의 공백으로 변환
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def load_upstage_result(file_path: str) -> str:
    """업스테이지 파서 결과에서 텍스트 추출"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 업스테이지 파서 결과에서 텍스트 추출 (구조에 따라 수정 필요)
        text_parts = []
        if 'elements' in data:
            for elem in data['elements']:
                if 'content' in elem and 'text' in elem['content'] and elem['content']['text'].strip():
                    text_parts.append(elem['content']['text'].strip())
                elif 'content' in elem and 'html' in elem['content'] and elem['content']['html'].strip():
                    # HTML에서 텍스트만 추출
                    text = clean_text(elem['content']['html'])
                    if text:
                        text_parts.append(text)
        
        return "\n".join(text_parts)
    
    except Exception as e:
        print(f"파일 로드 중 오류: {e}")
        return ""

def generate_summary(text, model_name="llama3.1:8b"):
    """Generate a structured summary using the specified model."""
    try:
        prompt = """
        다음 텍스트를 한국어로 체계적으로 요약해주세요. 반드시 다음 구조를 따라주세요:
        
        1. [주요 내용] 핵심 주제와 결론을 2-3문장으로 요약
        2. [주요 통계] 문서에 언급된 구체적인 수치와 통계 (없는 경우 생략)
        3. [주요 사례] 대표적인 사례 2-3개 (없는 경우 생략)
        4. [시사점] 문서가 제시하는 주요 시사점이나 인사이트
        5. [추가 정보] 자세히 알아볼 만한 키워드 3-5개
        
        요약 시 다음 사항을 유의해주세요:
        - 핵심 내용을 빠짐없이 포함할 것
        - 구체적인 수치와 사례가 있다면 반드시 포함할 것
        - 간결하고 명확한 문장을 사용할 것
        - 전문 용어는 정확하게 사용할 것
        
        텍스트:
        {}
        
        요약:""".format(text)

        response = subprocess.run(
            ["ollama", "run", model_name, prompt],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300  # 5분 타임아웃
        )
        
        if response.returncode == 0:
            return response.stdout.strip()
        else:
            print(f"요약 생성 중 오류 (코드 {response.returncode}): {response.stderr}")
            return ""
            
    except subprocess.TimeoutExpired:
        print("요청 시간 초과: 5분이 지났습니다.")
        return ""
    except Exception as e:
        print(f"요약 생성 중 오류 발생: {e}")
        return ""

def chunk_text(text: str, max_chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """텍스트를 작은 청크로 나눔"""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + max_chunk_size, text_length)
        
        # 문장 경계를 찾아서 자르기
        if end < text_length:
            # 다음 문장 부호나 공백을 찾아서 자름
            chunk_end = text.rfind('. ', start, end)
            if chunk_end == -1:
                chunk_end = text.rfind(' ', start, end)
            if chunk_end == -1 or chunk_end < start + max_chunk_size // 2:
                chunk_end = end
        else:
            chunk_end = end
            
        chunks.append(text[start:chunk_end].strip())
        
        # 다음 청크 시작 위치 설정 (중복을 피하기 위해 overlap 만큼 뒤로 이동)
        if chunk_end == text_length:
            break
            
        start = max(chunk_end - overlap, start + 1)
    
    return chunks

def summarize_with_llama(chunk: str, model: str = "llama3.1:8b") -> str:
    """Ollama를 사용해 텍스트 요약"""
    # 프롬프트 설정 (Llama3에 맞게 조정)
    prompt = f"""
    다음 텍스트를 한국어로 요약해주세요. 주요 내용을 간결하게 정리하고, 핵심 포인트를 포함해주세요.
    
    [텍스트 시작]
    {chunk}
    [텍스트 끝]
    
    요약:"""
    
    try:
        # Ollama API 호출
        cmd = ["ollama", "run", model, prompt]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300  # 5분 타임아웃
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"Ollama 실행 중 오류 (코드 {result.returncode}): {result.stderr}")
            return ""
            
    except subprocess.TimeoutExpired:
        print("요청 시간 초과: 5분이 지났습니다.")
        return ""
    except Exception as e:
        print(f"요약 중 오류 발생: {str(e)}")
        return ""

def ensure_directory(directory):
    """디렉토리가 없으면 생성"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"디렉토리 생성: {directory}")

def main():
    print("="*50)
    print("문서 요약을 시작합니다...")
    print("="*50)
    
    try:
        # 파일 경로 설정
        input_file = "processing_result.json"
        output_dir = "summaries"
        
        # 디렉토리 생성
        ensure_directory(output_dir)
        chunk_dir = os.path.join(output_dir, "chunks")
        summary_dir = os.path.join(output_dir, "summaries")
        ensure_directory(chunk_dir)
        ensure_directory(summary_dir)
        
        # 타임스탬프 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(summary_dir, f"llama_summary_{timestamp}.txt")
        
        # 1. 문서 로드
        print("\n[1/4] 문서를 로드하는 중...")
        text = load_upstage_result(input_file)
        
        if not text:
            raise ValueError("문서에서 텍스트를 추출할 수 없습니다.")
        
        print(f"✓ {len(text):,}자 텍스트 로드 완료")
        
        # 2. 텍스트 청크 분할
        print("\n[2/4] 텍스트를 청크로 분할하는 중...")
        chunks = chunk_text(text, max_chunk_size=3000, overlap=300)
        print(f"✓ 총 {len(chunks)}개의 청크로 분할 완료")
        
        # 3. 청크별 요약 생성
        print("\n[3/4] 청크별 요약을 생성하는 중...")
        print("이 작업은 시간이 오래 걸릴 수 있습니다.\n")
        
        summaries = []
        for i, chunk in enumerate(chunks, 1):
            print(f"\n[{i}/{len(chunks)}] 청크 처리 중...")
            summary = summarize_with_llama(chunk)
            
            if summary:
                # 청크 요약 저장
                chunk_file = os.path.join(chunk_dir, f"chunk_{i:03d}_summary.txt")
                with open(chunk_file, 'w', encoding='utf-8') as f:
                    f.write(f"## 원본 텍스트 (일부)\n\n{chunk[:1000]}...\n\n")
                    f.write(f"## 요약\n\n{summary}")
                
                summaries.append(summary)
                print(f"✓ 청크 {i} 요약 완료")
            else:
                print(f"✗ 청크 {i} 요약 실패")
        
        if not summaries:
            raise Exception("생성된 청크 요약이 없습니다.")
        
        # 4. 최종 요약 생성
        print("\n[4/4] 최종 요약을 생성하는 중...")
        final_summary = "\n\n---\n\n".join(summaries)
        
        # 5. 결과 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"원본 문서: {os.path.abspath(input_file)}\n")
            f.write(f"생성 모델: llama3.1:8b\n")
            f.write(f"원본 텍스트 길이: {len(text):,}자\n")
            f.write(f"처리된 청크 수: {len(chunks)}\n")
            f.write("-"*50 + "\n\n")
            f.write("# 문서 요약\n\n")
            f.write(final_summary)
        
        # 6. 완료 메시지
        print("\n" + "="*50)
        print("✓ 요약이 성공적으로 완료되었습니다!")
        print(f"- 저장 위치: {os.path.abspath(output_file)}")
        print(f"- 청크별 요약: {os.path.abspath(chunk_dir)}/")
        print("="*50)
        
    except Exception as e:
        print("\n" + "!"*50)
        print("오류가 발생했습니다:", str(e))
        print("\n요약 생성 중 오류가 발생했습니다. 다음 사항을 확인해주세요:")
        print("1. 입력 파일(processing_result.json)이 올바른 형식인지")
        print("2. 인터넷 연결 상태")
        print("3. Ollama 서비스 실행 여부")
        print("!"*50)
    finally:
        print("\n작업을 종료합니다.")

if __name__ == "__main__":
    main()
