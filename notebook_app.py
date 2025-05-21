import os
import sys
import json
import logging
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('notebook_app')

# 필요한 모듈 임포트
try:
    from document_manager import DocumentsManager, Document
    from query_engine import QueryEngine
except ImportError as e:
    logger.error(f"필요한 모듈을 임포트할 수 없습니다: {str(e)}")
    logger.error("프로젝트 루트 디렉토리에서 실행하고 있는지 확인하세요.")
    sys.exit(1)

class NotebookApp:
    """
    여러 문서를 관리하고 분석할 수 있는 노트북 앱
    """
    
    def __init__(self, workspace_dir: str = "workspace"):
        """
        노트북 앱 초기화
        
        Args:
            workspace_dir: 작업 디렉토리 경로
        """
        self.workspace_dir = Path(workspace_dir)
        self.documents_manager = DocumentsManager(workspace_dir=workspace_dir)
        self.query_engine = None  # 필요할 때 초기화
        
        # 작업 디렉토리 생성
        self.workspace_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"노트북 앱 초기화 완료 (작업 디렉토리: {self.workspace_dir})")
    
    def _initialize_query_engine(self, model_type: str, model_name: Optional[str] = None) -> None:
        """
        쿼리 엔진 초기화
        
        Args:
            model_type: 사용할 모델 타입
            model_name: 사용할 모델 이름 (선택적)
        """
        try:
            self.query_engine = QueryEngine(model_type=model_type, model_name=model_name)
            logger.info(f"쿼리 엔진 초기화 완료: {model_type}/{model_name or '기본값'}")
        except Exception as e:
            logger.error(f"쿼리 엔진 초기화 실패: {str(e)}")
            raise
    
    def add_documents(self, paths: List[str]) -> List[Dict[str, Any]]:
        """
        여러 문서 추가
        
        Args:
            paths: 문서 파일 경로 목록
            
        Returns:
            추가 결과 목록
        """
        results = []
        for path in paths:
            try:
                # 경로가 존재하는지 확인
                if not os.path.exists(path):
                    results.append({
                        "path": path,
                        "success": False,
                        "error": "파일을 찾을 수 없습니다."
                    })
                    continue
                
                # 디렉토리인 경우 지원하는 파일 확장자만 추가
                if os.path.isdir(path):
                    added_files = []
                    for root, _, files in os.walk(path):
                        for file in files:
                            if file.lower().endswith(('.pdf', '.txt', '.md')):
                                file_path = os.path.join(root, file)
                                doc_id = self.documents_manager.add_document(file_path)
                                added_files.append({
                                    "path": file_path,
                                    "doc_id": doc_id,
                                    "success": True
                                })
                    
                    if added_files:
                        results.append({
                            "path": path,
                            "success": True,
                            "added_files": added_files,
                            "count": len(added_files)
                        })
                    else:
                        results.append({
                            "path": path,
                            "success": False,
                            "error": "지원하는 파일이 없습니다."
                        })
                
                # 파일인 경우 직접 추가
                else:
                    doc_id = self.documents_manager.add_document(path)
                    results.append({
                        "path": path,
                        "doc_id": doc_id,
                        "success": True
                    })
            
            except Exception as e:
                results.append({
                    "path": path,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        추가된 문서 목록 조회
        
        Returns:
            문서 정보 목록
        """
        documents = self.documents_manager.get_all_documents()
        return [doc.to_dict() for doc in documents]
    
    def remove_document(self, doc_id: str) -> Dict[str, Any]:
        """
        문서 제거
        
        Args:
            doc_id: 제거할 문서 ID
            
        Returns:
            제거 결과
        """
        try:
            success = self.documents_manager.remove_document(doc_id)
            return {
                "doc_id": doc_id,
                "success": success,
                "error": None if success else "문서를 찾을 수 없거나 제거할 수 없습니다."
            }
        except Exception as e:
            return {
                "doc_id": doc_id,
                "success": False,
                "error": str(e)
            }
    
    def process_documents(self, doc_ids: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """
        문서 처리
        
        Args:
            doc_ids: 처리할 문서 ID 목록 (None이면 모든 문서)
            **kwargs: 추가 처리 옵션
            
        Returns:
            처리 결과
        """
        try:
            if doc_ids:
                # 지정된 문서만 처리
                results = {}
                for doc_id in doc_ids:
                    results[doc_id] = self.documents_manager.process_document(doc_id, **kwargs)
            else:
                # 모든 문서 처리
                results = self.documents_manager.process_all_documents(**kwargs)
            
            return {
                "success": True,
                "results": results,
                "processed_count": sum(1 for r in results.values() if r.get('success', False))
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_combined_markdown(self) -> Dict[str, Any]:
        """
        모든 처리된 문서의 결과를 통합하여 마크다운 형식으로 생성
        
        Returns:
            생성 결과
        """
        try:
            markdown = self.documents_manager.generate_combined_markdown()
            output_path = self.workspace_dir / "combined_results.md"
            
            return {
                "success": True,
                "markdown": markdown,
                "output_path": str(output_path)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def query(self, question: str, model_type: str = "openai", model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        문서 기반 질의
        
        Args:
            question: 질문 내용
            model_type: 사용할 모델 타입
            model_name: 사용할 모델 이름 (선택적)
            
        Returns:
            질의 결과
        """
        try:
            # 쿼리 엔진 초기화 (필요한 경우)
            if not self.query_engine or self.query_engine.model_type != model_type or (model_name and self.query_engine.model_name != model_name):
                self._initialize_query_engine(model_type, model_name)
            
            # 질의 실행
            result = self.query_engine.query_with_documents(question, self.documents_manager)
            
            # 결과 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.workspace_dir / f"query_results_{timestamp}"
            output_path = self.query_engine.save_query_result(result, str(output_dir))
            
            return {
                "success": True,
                "question": question,
                "answer": result.get('answer', ''),
                "model": result.get('model', ''),
                "output_path": output_path
            }
        except Exception as e:
            return {
                "success": False,
                "question": question,
                "error": str(e)
            }

def main():
    """
    명령행 인터페이스 메인 함수
    """
    parser = argparse.ArgumentParser(description='GrokParseNoteLM - 여러 문서를 분석하고 질의할 수 있는 노트북 앱')
    parser.add_argument('--workspace', type=str, default='workspace', help='작업 디렉토리')
    
    subparsers = parser.add_subparsers(dest='command', help='명령')
    
    # 문서 추가 명령
    add_parser = subparsers.add_parser('add', help='문서 추가')
    add_parser.add_argument('paths', nargs='+', help='추가할 문서 경로 (여러 개 가능)')
    
    # 문서 목록 명령
    subparsers.add_parser('list', help='문서 목록 보기')
    
    # 문서 제거 명령
    remove_parser = subparsers.add_parser('remove', help='문서 제거')
    remove_parser.add_argument('doc_id', help='제거할 문서 ID')
    
    # 문서 처리 명령
    process_parser = subparsers.add_parser('process', help='문서 처리')
    process_parser.add_argument('--doc-ids', nargs='*', help='처리할 문서 ID (지정하지 않으면 모든 문서)')
    process_parser.add_argument('--model-type', default='openai', help='사용할 모델 타입 (openai, upstage, gemini 등)')
    process_parser.add_argument('--model-name', help='사용할 모델 이름')
    process_parser.add_argument('--parser', default='auto', help='PDF 파서 (auto, upstage, pymupdf)')
    process_parser.add_argument('--language', default='ko', help='언어 (ko, en 등)')
    process_parser.add_argument('--ocr-language', default='kor+eng', help='OCR 언어 (kor+eng, eng 등)')
    
    # 통합 마크다운 생성 명령
    subparsers.add_parser('combine', help='통합 마크다운 생성')
    
    # 질의 명령
    query_parser = subparsers.add_parser('query', help='문서 기반 질의')
    query_parser.add_argument('question', help='질문 내용')
    query_parser.add_argument('--model-type', default='openai', help='사용할 모델 타입 (openai, upstage, gemini 등)')
    query_parser.add_argument('--model-name', help='사용할 모델 이름')
    
    args = parser.parse_args()
    
    # 명령이 지정되지 않은 경우 도움말 표시
    if not args.command:
        parser.print_help()
        return
    
    # 노트북 앱 초기화
    app = NotebookApp(workspace_dir=args.workspace)
    
    # 명령 실행
    if args.command == 'add':
        results = app.add_documents(args.paths)
        success_count = sum(1 for r in results if r.get('success', False))
        print(f"총 {len(results)}개 경로 중 {success_count}개 추가 성공")
        
        for result in results:
            if result.get('success'):
                if 'added_files' in result:
                    print(f"디렉토리 '{result['path']}'에서 {result['count']}개 파일 추가됨")
                else:
                    print(f"파일 '{result['path']}' 추가됨 (ID: {result.get('doc_id')})")
            else:
                print(f"오류: '{result['path']}' - {result.get('error')}")
    
    elif args.command == 'list':
        documents = app.list_documents()
        if not documents:
            print("추가된 문서가 없습니다.")
        else:
            print(f"총 {len(documents)}개 문서:")
            for i, doc in enumerate(documents, 1):
                status = "처리됨" if doc.get('processed', False) else "미처리"
                print(f"{i}. {doc.get('filename')} (타입: {doc.get('doc_type')}, 상태: {status}, ID: {doc.get('doc_id')})")
    
    elif args.command == 'remove':
        result = app.remove_document(args.doc_id)
        if result.get('success'):
            print(f"문서 제거됨: {args.doc_id}")
        else:
            print(f"문서 제거 실패: {result.get('error')}")
    
    elif args.command == 'process':
        process_options = {
            'model_type': args.model_type,
            'model_name': args.model_name,
            'parser': args.parser,
            'language': args.language,
            'ocr_language': args.ocr_language
        }
        
        result = app.process_documents(args.doc_ids, **process_options)
        
        if result.get('success'):
            print(f"문서 처리 완료: {result.get('processed_count')}개 문서 처리됨")
            
            # 개별 문서 처리 결과 출력
            for doc_id, doc_result in result.get('results', {}).items():
                if doc_result.get('success'):
                    print(f"- '{doc_result.get('filename')}' 처리 성공 (ID: {doc_id})")
                    print(f"  결과 디렉토리: {doc_result.get('output_dir')}")
                else:
                    print(f"- '{doc_result.get('filename')}' 처리 실패: {doc_result.get('error')}")
        else:
            print(f"문서 처리 실패: {result.get('error')}")
    
    elif args.command == 'combine':
        result = app.generate_combined_markdown()
        if result.get('success'):
            print(f"통합 마크다운 생성 완료: {result.get('output_path')}")
        else:
            print(f"통합 마크다운 생성 실패: {result.get('error')}")
    
    elif args.command == 'query':
        result = app.query(args.question, args.model_type, args.model_name)
        if result.get('success'):
            print(f"\n질문: {result.get('question')}\n")
            print(f"답변: {result.get('answer')}\n")
            print(f"모델: {result.get('model')}")
            print(f"\n결과가 저장되었습니다: {result.get('output_path')}")
        else:
            print(f"질의 실패: {result.get('error')}")

if __name__ == "__main__":
    main()
