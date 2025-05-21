import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('query_engine')

class QueryEngine:
    """
    여러 문서의 통합 결과를 바탕으로 LLM에 질의하는 엔진
    """
    
    def __init__(self, model_type: str = "openai", model_name: Optional[str] = None):
        """
        쿼리 엔진 초기화
        
        Args:
            model_type: 사용할 모델 타입 (openai, upstage, gemini 등)
            model_name: 사용할 모델 이름 (기본값은 모델 타입에 따라 자동 설정)
        """
        self.model_type = model_type
        self.model_name = model_name
        
        # 모델 핸들러 초기화
        try:
            from model_handler import ModelHandler
            self.model_handler = ModelHandler(
                model_type=model_type,
                model_name=model_name
            )
            logger.info(f"모델 핸들러 초기화 완료: {model_type} - {model_name or '기본값'}")
        except Exception as e:
            logger.error(f"모델 핸들러 초기화 실패: {str(e)}")
            raise
    
    def _truncate_context(self, context: str, max_tokens: int = 8000) -> str:
        """
        컨텍스트가 너무 길 경우 적절히 자르기
        
        Args:
            context: 원본 컨텍스트 문자열
            max_tokens: 최대 토큰 수 (대략적인 추정)
            
        Returns:
            적절히 잘린 컨텍스트
        """
        # 간단한 토큰 수 추정 (영어 기준 단어당 약 1.3 토큰)
        estimated_tokens = len(context) / 3
        
        if estimated_tokens <= max_tokens:
            return context
        
        # 컨텍스트가 너무 길면 중요 부분 우선 포함
        logger.warning(f"컨텍스트가 너무 깁니다. 약 {estimated_tokens:.0f} 토큰 -> {max_tokens} 토큰으로 축소합니다.")
        
        # 문서를 섹션으로 분할
        sections = context.split("## 문서 ")
        header = sections[0]  # 전체 헤더 부분
        
        # 각 문서 섹션 처리
        processed_sections = [header]
        remaining_tokens = max_tokens - (len(header) / 3)
        
        for section in sections[1:]:
            if not section.strip():
                continue
                
            # 섹션 크기 추정
            section_tokens = len(section) / 3
            
            if section_tokens < remaining_tokens:
                # 섹션 전체를 포함할 수 있는 경우
                processed_sections.append("## 문서 " + section)
                remaining_tokens -= section_tokens
            else:
                # 섹션을 축소해야 하는 경우
                # 요약 부분 우선 포함
                if "### 요약" in section:
                    summary_part = "### 요약" + section.split("### 요약")[1].split("###")[0]
                    summary_tokens = len(summary_part) / 3
                    
                    if summary_tokens < remaining_tokens:
                        # 문서 정보와 요약만 포함
                        doc_info = section.split("###")[0]
                        truncated_section = "## 문서 " + doc_info + summary_part
                        processed_sections.append(truncated_section)
                        remaining_tokens -= (len(truncated_section) / 3)
                    else:
                        # 요약도 너무 길면 일부만 포함
                        truncated_summary = summary_part[:int(remaining_tokens * 3)]
                        truncated_section = "## 문서 " + section.split("###")[0] + truncated_summary
                        processed_sections.append(truncated_section)
                        break  # 토큰 한도 도달
                else:
                    # 요약이 없으면 문서 정보만 포함
                    doc_info = "## 문서 " + section.split("###")[0]
                    if (len(doc_info) / 3) < remaining_tokens:
                        processed_sections.append(doc_info)
                        remaining_tokens -= (len(doc_info) / 3)
                    else:
                        break  # 토큰 한도 도달
            
            # 토큰 한도에 도달하면 중단
            if remaining_tokens <= 0:
                break
        
        # 잘린 컨텍스트 표시 추가
        if len(sections) > len(processed_sections):
            processed_sections.append("\n\n(컨텍스트가 너무 길어 일부 문서는 표시되지 않았습니다.)\n")
        
        return "".join(processed_sections)
    
    def query(self, question: str, context: str, max_tokens: int = 8000) -> Dict[str, Any]:
        """
        LLM에 질의하기
        
        Args:
            question: 질문 내용
            context: 질문의 컨텍스트 (여러 문서의 통합 결과)
            max_tokens: 최대 컨텍스트 토큰 수
            
        Returns:
            질의 결과 딕셔너리
        """
        try:
            # 컨텍스트가 너무 길면 적절히 자르기
            truncated_context = self._truncate_context(context, max_tokens)
            
            # 프롬프트 구성
            prompt = f"""다음은 여러 문서를 분석한 결과입니다. 이 정보를 바탕으로 질문에 답변해주세요.

{truncated_context}

질문: {question}

답변:"""
            
            # 모델 핸들러를 통해 응답 생성
            # generate_summary 메서드를 사용하지만, 실제로는 응답 생성용으로 사용
            response = self.model_handler.generate_summary(prompt)
            
            return {
                "question": question,
                "answer": response,
                "model": f"{self.model_type}/{self.model_name or '기본값'}",
                "success": True
            }
            
        except Exception as e:
            error_msg = f"질의 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            
            return {
                "question": question,
                "error": error_msg,
                "success": False
            }
    
    def query_with_documents(self, question: str, documents_manager) -> Dict[str, Any]:
        """
        문서 관리자의 문서들을 사용하여 질의하기
        
        Args:
            question: 질문 내용
            documents_manager: DocumentsManager 인스턴스
            
        Returns:
            질의 결과 딕셔너리
        """
        try:
            # 통합 마크다운 생성
            combined_markdown = documents_manager.generate_combined_markdown()
            
            # 질의 실행
            return self.query(question, combined_markdown)
            
        except Exception as e:
            error_msg = f"문서 기반 질의 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            
            return {
                "question": question,
                "error": error_msg,
                "success": False
            }
    
    def save_query_result(self, result: Dict[str, Any], output_dir: str, filename: str = "query_result") -> str:
        """
        질의 결과 저장
        
        Args:
            result: 질의 결과 딕셔너리
            output_dir: 출력 디렉토리
            filename: 파일 이름 (확장자 제외)
            
        Returns:
            저장된 파일 경로
        """
        try:
            # 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            
            # 마크다운 형식으로 저장
            markdown_content = f"""# 질의 결과

## 질문
{result['question']}

## 답변
{result.get('answer', '오류: ' + result.get('error', '알 수 없는 오류'))}

## 모델 정보
{result.get('model', '정보 없음')}
"""
            
            markdown_path = os.path.join(output_dir, f"{filename}.md")
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # JSON 형식으로도 저장
            json_path = os.path.join(output_dir, f"{filename}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"질의 결과 저장 완료: {markdown_path}")
            return markdown_path
            
        except Exception as e:
            error_msg = f"질의 결과 저장 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            return ""

# 사용 예시
if __name__ == "__main__":
    import argparse
    from document_manager import DocumentsManager
    
    parser = argparse.ArgumentParser(description='문서 기반 질의 엔진')
    parser.add_argument('--workspace', type=str, default='workspace', help='작업 디렉토리')
    parser.add_argument('--model-type', type=str, default='openai', help='모델 타입 (openai, upstage, gemini 등)')
    parser.add_argument('--model-name', type=str, help='모델 이름')
    parser.add_argument('--question', type=str, required=True, help='질문 내용')
    
    args = parser.parse_args()
    
    # 문서 관리자 초기화
    manager = DocumentsManager(workspace_dir=args.workspace)
    
    # 문서가 있는지 확인
    documents = manager.get_all_documents()
    if not documents:
        print("추가된 문서가 없습니다. 먼저 문서를 추가해주세요.")
        exit(1)
    
    # 처리된 문서가 있는지 확인
    processed_docs = [doc for doc in documents if doc.processed]
    if not processed_docs:
        print("처리된 문서가 없습니다. 먼저 문서를 처리해주세요.")
        exit(1)
    
    # 쿼리 엔진 초기화
    engine = QueryEngine(model_type=args.model_type, model_name=args.model_name)
    
    # 질의 실행
    result = engine.query_with_documents(args.question, manager)
    
    # 결과 출력
    if result['success']:
        print(f"\n질문: {result['question']}\n")
        print(f"답변: {result['answer']}\n")
        print(f"모델: {result['model']}")
        
        # 결과 저장
        output_path = engine.save_query_result(result, manager.workspace_dir)
        if output_path:
            print(f"\n결과가 저장되었습니다: {output_path}")
    else:
        print(f"오류 발생: {result.get('error', '알 수 없는 오류')}")
