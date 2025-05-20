import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI
from typing import List, Optional, Tuple, Dict, Any
import json
from datetime import datetime

# 환경 변수 로드
load_dotenv()

class ModelHandler:
    """
    A handler class for different AI models to generate summaries from text.
    Supports multiple AI models including OpenAI, Google Gemini, Upstage, and local Llama models via Ollama.
    """
    def __init__(self, model_type: str, model_name: Optional[str] = None):
        """
        Initialize the model handler with the specified model type and name.
        
        Args:
            model_type: Type of model to use ('upstage', 'llama', 'openai', 'gemini')
            model_name: Specific model name/version (e.g., 'gpt-4', 'gemini-pro', 'llama3:latest')
        """
        self.model_type = model_type.lower()
        self.model_name = model_name or self._get_default_model_name()
        self.client = None
        self.model = None
        self.api_url = None
        
        # Initialize the appropriate model client
        if self.model_type == "openai":
            self._init_openai()
        elif self.model_type == "gemini":
            self._init_gemini()
        elif self.model_type == "llama":
            self._init_llama()
        elif self.model_type == "upstage":
            self._init_upstage()
        else:
            raise ValueError(f"지원하지 않는 모델 타입입니다: {model_type}")
    
    def _get_default_model_name(self) -> str:
        """Get the default model name based on model type."""
        defaults = {
            'openai': 'gpt-4-turbo-preview',
            'gemini': 'gemini-pro',
            'llama': 'llama3:latest',
            'upstage': 'solar-1-mini'  # Upstage의 기본 모델 (최신 버전)
        }
        return defaults.get(self.model_type, '')
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        print(f"Using OpenAI model: {self.model_name}")
    
    def _init_gemini(self):
        """Initialize Google Gemini client."""
        if not os.getenv('GEMINI_API_KEY'):
            raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel(self.model_name)
        print(f"Using Gemini model: {self.model_name}")
    
    def _init_llama(self):
        """Initialize Llama model settings."""
        self.api_url = "http://localhost:11434/api/generate"
        print(f"Using Ollama model: {self.model_name}")
    
    def _init_upstage(self):
        """Initialize Upstage API settings."""
        if not os.getenv('UPSTAGE_API_KEY'):
            raise ValueError("UPSTAGE_API_KEY 환경 변수가 설정되지 않았습니다.")
        print(f"Using Upstage model: {self.model_name}")
        
    def split_text_into_chunks(self, text: str, chunk_size: int = 8000, overlap: int = 200) -> List[str]:
        """
        긴 텍스트를 작은 청크로 분할합니다.
        
        Args:
            text: 분할할 텍스트
            chunk_size: 각 청크의 최대 길이
            overlap: 청크 간 겹치는 길이
        Returns:
            분할된 텍스트 청크 리스트
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # 청크 끝부분 결정
            end = min(start + chunk_size, len(text))
            
            # 문장 끝에서 끝나도록 조정 (마침표, 줄바꿈 등)
            if end < len(text):
                # 문장 끝이나 단락 끝을 찾음
                for marker in [".", "!", "?", "\n\n", "\n"]:
                    pos = text.rfind(marker, start, end)
                    if pos > start + chunk_size // 2:  # 최소한 청크의 절반 이상이어야 함
                        end = pos + 1  # 문장 끝 기호 포함
                        break
            
            # 현재 청크 추가
            chunks.append(text[start:end])
            
            # 다음 청크 시작점 (겹치는 부분 고려)
            start = max(start + 1, end - overlap)
        
        return chunks
    
    def merge_summaries(self, summaries: List[str]) -> str:
        """
        여러 청크의 요약을 하나로 합칩니다.
        
        Args:
            summaries: 합칠 요약 리스트
        Returns:
            합쳐진 최종 요약
        """
        if not summaries:
            return ""
        
        if len(summaries) == 1:
            return summaries[0]
        
        # 요약들을 합치기 위한 프롬프트
        if self.model_type == "openai":
            combined_summaries = "\n\n".join([f"[Part {i+1}]\n{summary}" for i, summary in enumerate(summaries)])
            merge_prompt = f"""다음은 긴 문서의 여러 부분에 대한 요약입니다. 이 요약들을 하나의 일관된 요약으로 합쳐주세요. 중복되는 내용은 제거하고, 중요한 정보만 포함해주세요. 전체 문서의 주제와 핵심 내용을 포함하는 한국어 요약을 작성해주세요.

{combined_summaries}"""
            return self._generate_openai(merge_prompt)
        elif self.model_type == "llama":
            combined_summaries = "\n\n".join([f"[Part {i+1}]\n{summary}" for i, summary in enumerate(summaries)])
            merge_prompt = f"[INST]\n다음은 긴 문서의 여러 부분에 대한 요약입니다. 이 요약들을 하나의 일관된 한국어 요약으로 합쳐주세요. 중복되는 내용은 제거하고, 중요한 정보만 포함해주세요.\n\n{combined_summaries}[/INST]"
            return self._generate_llama(merge_prompt)
        else:
            # 다른 모델은 단순히 요약들을 합치기
            return "\n\n".join([f"=== 부분 {i+1} ===\n{summary}" for i, summary in enumerate(summaries)])
    
    def generate_summary(self, text: str, image_paths: Optional[List[str]] = None) -> str:
        """
        Generate a summary of the given text using the specified model.
        
        Args:
            text: The text to summarize
            image_paths: List of image paths (not yet supported for all models)
        Returns:
            str: The generated summary
        """
        if image_paths:
            print(f"Note: Found {len(image_paths)} images. Image analysis is not yet implemented for {self.model_type.upper()}.")
        
        try:
            # 모델별 청크 크기 설정
            chunk_sizes = {
                "openai": 12000,  # GPT-4 Turbo는 비교적 큰 컨텍스트 처리 가능
                "llama": 8000,   # Llama는 로컬 모델이지만 제한적
                "gemini": 10000,  # Gemini는 중간 정도
                "upstage": 8000   # Upstage는 제한적
            }
            
            chunk_size = chunk_sizes.get(self.model_type, 8000)
            
            # 텍스트 길이 확인
            if len(text) > chunk_size:
                print(f"\n[디버그] 텍스트 길이: {len(text):,} 글자, 청크 크기 제한: {chunk_size:,} 글자")
                print(f"[진행] 텍스트가 너무 깁니다. 여러 청크로 분할하여 처리합니다...")
                
                # 텍스트를 청크로 분할
                print(f"[진행] 텍스트 분할 중...")
                chunks = self.split_text_into_chunks(text, chunk_size)
                print(f"[완료] 텍스트를 {len(chunks)}개의 청크로 분할했습니다.")
                print(f"[디버그] 각 청크 길이: {', '.join([str(len(chunk)) for chunk in chunks])}")
                
                # 각 청크를 개별적으로 요약
                print(f"\n[진행] 각 청크 요약 시작...")
                summaries = []
                for i, chunk in enumerate(chunks):
                    print(f"\n[진행] 청크 {i+1}/{len(chunks)} 요약 중... (길이: {len(chunk):,} 글자)")
                    print(f"[디버그] 청크 {i+1} 시작 부분: {chunk[:100]}...")
                    
                    start_time = datetime.now()
                    if self.model_type == "openai":
                        print(f"[API] OpenAI API 요청 중... (모델: {self.model_name})")
                        summary = self._generate_openai(chunk)
                    elif self.model_type == "gemini":
                        print(f"[API] Gemini API 요청 중... (모델: {self.model_name})")
                        summary = self._generate_gemini(chunk)
                    elif self.model_type == "llama":
                        print(f"[API] Llama API 요청 중... (모델: {self.model_name or 'llama3:latest'})")
                        summary = self._generate_llama(chunk)
                    elif self.model_type == "upstage":
                        print(f"[API] Upstage API 요청 중... (모델: {self.model_name})")
                        summary = self._generate_upstage(chunk)
                    else:
                        raise ValueError(f"Unsupported model type: {self.model_type}")
                    
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    print(f"[완료] 청크 {i+1} 요약 완료 (소요 시간: {duration:.2f}초)")
                    print(f"[디버그] 요약 길이: {len(summary)} 글자")
                    print(f"[디버그] 요약 시작 부분: {summary[:150]}...")
                    
                    summaries.append(summary)
                
                # 각 청크의 요약을 합치기
                print("\n[진행] 각 청크의 요약을 합치는 중...")
                merge_start_time = datetime.now()
                final_summary = self.merge_summaries(summaries)
                merge_end_time = datetime.now()
                merge_duration = (merge_end_time - merge_start_time).total_seconds()
                print(f"[완료] 요약 병합 완료 (소요 시간: {merge_duration:.2f}초)")
                print(f"[디버그] 최종 요약 길이: {len(final_summary)} 글자")
                return final_summary
            
            # 텍스트가 충분히 짧은 경우 일반적인 방식으로 요약
            if self.model_type == "openai":
                return self._generate_openai(text)
            elif self.model_type == "gemini":
                return self._generate_gemini(text)
            elif self.model_type == "llama":
                return self._generate_llama(text)
            elif self.model_type == "upstage":
                return self._generate_upstage(text)
            else:
                raise ValueError(f"Unsupported model type: {self.model_type}")
        except Exception as e:
            error_msg = f"Error generating summary with {self.model_type.upper()}: {str(e)}"
            print(error_msg)
            return error_msg

    
    def _generate_openai(self, text: str) -> str:
        """Generate a summary using OpenAI's API."""
        messages = [
            {
                "role": "system",
                "content": "당신은 문서를 명확하고 구조화된 형식으로 요약해주는 도우미입니다. "
                          "문서의 주요 포인트, 핵심 주장, 중요한 세부 사항을 한국어로 요약해주세요."
            },
            {
                "role": "user",
                "content": f"다음 문서를 한국어로 자세히 요약해주세요.\n\n문서 내용:\n{text}"
            }
        ]
        
        response = self.client.chat.completions.create(
            model=self.model_name or "gpt-4-turbo-preview",
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        return response.choices[0].message.content
    
    def _generate_gemini(self, text: str) -> str:
        """Generate a summary using Google's Gemini API."""
        prompt = f"""다음 문서를 한국어로 자세히 요약해주세요. 주요 포인트, 핵심 주장, 중요한 세부 사항을 포함해주세요.
        
        문서 내용:
        {text}
        
        한국어 요약:"""
        
        response = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2000,
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        
        return response.text
    
    def _generate_llama(self, text: str) -> str:
        """Generate a summary using a local Llama model via Ollama API."""
        # 텍스트가 너무 길면 잘라내기 (약 8000자 제한)
        max_length = 8000
        if len(text) > max_length:
            print(f"경고: 텍스트가 너무 깁니다. {len(text)}자에서 {max_length}자로 잘라냅니다.")
            text = text[:max_length] + "... (이하 생략)"
        
        # 단순화된 프롬프트 사용
        prompt = f"""[INST]
        다음 문서를 한국어로 요약해주세요. 반드시 한국어로 작성해야 합니다.
        
        문서:
        {text}
        [/INST]"""
        
        print(f"Ollama API 요청 중: {self.model_name or 'llama3:latest'}")
        try:
            # 요청 데이터 단순화
            payload = {
                "model": self.model_name or "llama3:latest",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 1000  # 응답 길이 제한
                }
            }
            
            # API 요청 디버깅
            print(f"Payload: {payload['model']}, 프롬프트 길이: {len(prompt)}")
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=300  # 5분 타임아웃
            )
            
            # 응답 디버깅
            print(f"Ollama API 응답 코드: {response.status_code}")
            
            # 오류 응답 확인
            if response.status_code != 200:
                print(f"응답 내용: {response.text[:500]}")
                return f"Ollama API 오류: HTTP {response.status_code} - {response.text[:200]}"
            
            result = response.json()
            
            # 응답 내용 확인
            if "response" not in result or not result["response"].strip():
                print("Ollama API가 빈 응답을 반환했습니다.")
                print(f"전체 응답: {result}")
                
                # 다른 모델 시도
                print("다른 모델(llama3.2:latest)로 재시도합니다...")
                backup_payload = payload.copy()
                backup_payload["model"] = "llama3.2:latest"
                
                backup_response = requests.post(
                    self.api_url,
                    json=backup_payload,
                    timeout=300
                )
                
                if backup_response.status_code == 200:
                    backup_result = backup_response.json()
                    if "response" in backup_result and backup_result["response"].strip():
                        return backup_result["response"]
                
                return "한국어 요약을 생성하지 못했습니다. 다른 모델을 사용해보세요."
            
            return result.get("response", "요약을 생성하지 못했습니다.")
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Ollama 서버 연결 오류: {str(e)}. Ollama가 실행 중인지 확인하세요."
            print(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Ollama API 요청 중 오류 발생: {str(e)}"
            print(error_msg)
            return error_msg
    
    def _generate_upstage(self, text: str) -> str:
        """Generate a summary using Upstage's chat/completions API."""
        try:
            # 텍스트가 너무 길면 잘라내기 (약 8000자 제한)
            max_length = 8000
            if len(text) > max_length:
                print(f"경고: 텍스트가 너무 깁니다. {len(text)}자에서 {max_length}자로 잘라냅니다.")
                text = text[:max_length] + "... (이하 생략)"
            
            headers = {
                "Authorization": f"Bearer {os.getenv('UPSTAGE_API_KEY')}",
                "Content-Type": "application/json"
            }
            
            # Upstage Solar API 형식에 맞게 메시지 구성
            messages = [
                {
                    "role": "system",
                    "content": "당신은 문서를 명확하고 구조화된 형식으로 요약해주는 도우미입니다. 반드시 한국어로만 답변해주세요."
                },
                {
                    "role": "user",
                    "content": f"다음 문서를 한국어로 자세히 요약해주세요. 주요 포인트, 핵심 주장, 중요한 세부 사항을 포함해주세요.\n\n문서 내용:\n{text}"
                }
            ]
            
            # Upstage API 요청 형식
            payload = {
                "model": self.model_name or "solar-1-mini",
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 2000,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }
            
            print(f"Upstage API 요청 중: {self.model_name or 'solar-1-mini'}")
            response = requests.post(
                "https://api.upstage.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=300
            )
            
            # 오류 디버깅을 위한 상태 코드 출력
            if response.status_code != 200:
                print(f"API 응답 코드: {response.status_code}")
                print(f"응답 내용: {response.text[:500]}")
            
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            error_msg = f"Upstage API 요청 중 오류 발생: {str(e)}"
            print(error_msg)
            return error_msg
