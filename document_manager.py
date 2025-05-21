import os
import json
import shutil
import logging
import uuid
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('document_manager')

class Document:
    """문서 클래스 (PDF, 텍스트 등)"""
    
    def __init__(self, path: str, doc_type: str = None, doc_id: str = None):
        """
        문서 객체 초기화
        
        Args:
            path: 문서 파일 경로
            doc_type: 문서 타입 (자동 감지되지 않은 경우 지정)
            doc_id: 문서 ID (지정되지 않은 경우 자동 생성)
        """
        # Path 객체로 변환하여 경로 처리 안정성 향상
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")
            
        self.filename = self.path.name
        self.doc_id = doc_id or str(uuid.uuid4())
        self.doc_type = doc_type or self._detect_doc_type()
        self.processed = False
        self.processed_data = {
            "markdown": None,  # 마크다운 형식 결과
            "text": None,      # 추출된 텍스트
            "images": [],      # 이미지 정보
            "summary": None    # 요약 정보
        }
        self.output_dir = None  # 처리 결과가 저장된 디렉토리
        self.added_date = datetime.now()
        
        logger.info(f"문서 객체 생성: {self.filename} (ID: {self.doc_id}, 타입: {self.doc_type})")
    
    def _detect_doc_type(self) -> str:
        """파일 확장자를 기반으로 문서 타입 감지"""
        ext = self.path.suffix.lower()
        if ext == '.pdf':
            return 'pdf'
        elif ext in ['.txt', '.md', '.markdown']:
            return 'text'
        elif ext in ['.docx', '.doc']:
            return 'word'
        else:
            return 'unknown'
    
    def to_dict(self) -> Dict[str, Any]:
        """문서 정보를 딕셔너리로 변환"""
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "path": str(self.path),
            "doc_type": self.doc_type,
            "processed": self.processed,
            "output_dir": self.output_dir,
            "added_date": self.added_date.isoformat()
        }
    
    def __str__(self) -> str:
        status = "처리됨" if self.processed else "미처리"
        return f"{self.filename} (타입: {self.doc_type}, 상태: {status}, ID: {self.doc_id})"

class DocumentsManager:
    """여러 문서를 관리하는 클래스"""
    
    def __init__(self, workspace_dir: str = "workspace"):
        """
        문서 관리자 초기화
        
        Args:
            workspace_dir: 작업 디렉토리 경로
        """
        # Path 객체로 변환하여 경로 처리 안정성 향상
        self.workspace_dir = Path(workspace_dir)
        self.documents: Dict[str, Document] = {}  # doc_id -> Document
        self.output_dir = self.workspace_dir / "output"
        self.metadata_file = self.workspace_dir / "documents_metadata.json"
        
        # 디렉토리 생성
        self.workspace_dir.mkdir(exist_ok=True, parents=True)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # 기존 메타데이터 로드 (있는 경우)
        self._load_metadata()
        
        logger.info(f"문서 관리자 초기화 완료 (작업 디렉토리: {self.workspace_dir})")
    
    def _load_metadata(self) -> None:
        """저장된 문서 메타데이터 로드"""
        if not self.metadata_file.exists():
            logger.info("메타데이터 파일이 없습니다. 새로 생성됩니다.")
            return
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 문서 목록 복원
            for doc_data in metadata.get("documents", []):
                doc_path = doc_data.get("path")
                if not os.path.exists(doc_path):
                    logger.warning(f"문서 파일을 찾을 수 없습니다: {doc_path}")
                    continue
                
                try:
                    doc = Document(
                        path=doc_path,
                        doc_type=doc_data.get("doc_type"),
                        doc_id=doc_data.get("doc_id")
                    )
                    doc.processed = doc_data.get("processed", False)
                    doc.output_dir = doc_data.get("output_dir")
                    
                    # 날짜 복원 (ISO 형식)
                    added_date = doc_data.get("added_date")
                    if added_date:
                        try:
                            doc.added_date = datetime.fromisoformat(added_date)
                        except ValueError:
                            pass
                    
                    self.documents[doc.doc_id] = doc
                except Exception as e:
                    logger.error(f"문서 복원 중 오류 발생: {str(e)}")
            
            logger.info(f"메타데이터에서 {len(self.documents)}개 문서 로드 완료")
        except Exception as e:
            logger.error(f"메타데이터 로드 중 오류 발생: {str(e)}")
    
    def _save_metadata(self) -> None:
        """문서 메타데이터 저장"""
        try:
            metadata = {
                "last_updated": datetime.now().isoformat(),
                "documents": [doc.to_dict() for doc in self.documents.values()]
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"메타데이터 저장 완료: {len(self.documents)}개 문서")
        except Exception as e:
            logger.error(f"메타데이터 저장 중 오류 발생: {str(e)}")
    
    def add_document(self, path: str) -> str:
        """
        문서 추가
        
        Args:
            path: 문서 파일 경로
            
        Returns:
            추가된 문서의 ID
        """
        try:
            # 이미 동일한 경로의 문서가 있는지 확인
            path_obj = Path(path)
            for doc in self.documents.values():
                if Path(doc.path) == path_obj:
                    logger.info(f"이미 추가된 문서입니다: {path}")
                    return doc.doc_id
            
            # 새 문서 추가
            doc = Document(path)
            self.documents[doc.doc_id] = doc
            
            # 메타데이터 저장
            self._save_metadata()
            
            logger.info(f"문서 추가됨: {doc.filename} (ID: {doc.doc_id})")
            return doc.doc_id
        except Exception as e:
            logger.error(f"문서 추가 중 오류 발생: {str(e)}")
            raise
    
    def remove_document(self, doc_id: str) -> bool:
        """
        문서 제거
        
        Args:
            doc_id: 제거할 문서 ID
            
        Returns:
            제거 성공 여부
        """
        if doc_id not in self.documents:
            logger.warning(f"문서를 찾을 수 없습니다: {doc_id}")
            return False
        
        try:
            # 문서 객체 가져오기
            doc = self.documents[doc_id]
            
            # 처리 결과 디렉토리가 있으면 삭제
            if doc.output_dir and os.path.exists(doc.output_dir):
                try:
                    shutil.rmtree(doc.output_dir)
                    logger.info(f"문서 처리 결과 디렉토리 삭제: {doc.output_dir}")
                except Exception as e:
                    logger.warning(f"처리 결과 디렉토리 삭제 실패: {str(e)}")
            
            # 문서 목록에서 제거
            del self.documents[doc_id]
            
            # 메타데이터 저장
            self._save_metadata()
            
            logger.info(f"문서 제거됨: {doc.filename} (ID: {doc_id})")
            return True
        except Exception as e:
            logger.error(f"문서 제거 중 오류 발생: {str(e)}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        문서 ID로 문서 가져오기
        
        Args:
            doc_id: 문서 ID
            
        Returns:
            문서 객체 또는 None (문서가 없는 경우)
        """
        doc = self.documents.get(doc_id)
        if not doc:
            logger.warning(f"문서를 찾을 수 없습니다: {doc_id}")
        return doc
    
    def get_all_documents(self) -> List[Document]:
        """
        모든 문서 목록 가져오기
        
        Returns:
            문서 객체 목록
        """
        return list(self.documents.values())
    
    def process_document(self, doc_id: str, **kwargs) -> Dict[str, Any]:
        """
        단일 문서 처리
        
        Args:
            doc_id: 처리할 문서 ID
            **kwargs: 추가 처리 옵션
            
        Returns:
            처리 결과 딕셔너리
        """
        doc = self.get_document(doc_id)
        if not doc:
            raise ValueError(f"문서를 찾을 수 없습니다: {doc_id}")
        
        # 문서 파일 존재 확인
        if not os.path.exists(doc.path):
            raise FileNotFoundError(f"문서 파일을 찾을 수 없습니다: {doc.path}")
        
        logger.info(f"문서 처리 시작: {doc.filename} (ID: {doc_id})")
        
        try:
            # 문서 타입에 따라 적절한 처리 방법 선택
            if doc.doc_type == 'pdf':
                # PDF 분석기 임포트 (필요할 때만 임포트하여 의존성 최소화)
                from pdf_analyzer import analyze_pdf
                
                # 출력 디렉토리 설정
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_name = Path(doc.path).stem
                model_type = kwargs.get('model_type', 'none').upper()
                doc_output_dir = str(self.output_dir / f"{pdf_name}_{model_type}_{timestamp}")
                
                # PDF 분석 실행
                result_markdown = analyze_pdf(
                    pdf_path=str(doc.path),
                    output_dir=str(self.output_dir),
                    model_type=kwargs.get('model_type'),
                    model_name=kwargs.get('model_name'),
                    parser=kwargs.get('parser', 'auto'),
                    language=kwargs.get('language', 'ko'),
                    ocr_language=kwargs.get('ocr_language', 'kor+eng'),
                    save_json=True
                )
                
                # 결과 저장
                doc.processed = True
                doc.output_dir = doc_output_dir
                doc.processed_data["markdown"] = result_markdown
                
                # JSON 결과 파일에서 추가 정보 로드
                json_result_path = os.path.join(doc_output_dir, "summary.json")
                if os.path.exists(json_result_path):
                    try:
                        with open(json_result_path, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                            doc.processed_data["text"] = json_data.get("text_content", "")
                            doc.processed_data["summary"] = json_data.get("summary", "")
                            doc.processed_data["images"] = json_data.get("images", [])
                    except Exception as e:
                        logger.warning(f"JSON 결과 파일 로드 실패: {str(e)}")
                
                logger.info(f"PDF 문서 처리 완료: {doc.filename}")
                
            elif doc.doc_type == 'text':
                # 텍스트 파일 처리 로직
                try:
                    with open(doc.path, 'r', encoding='utf-8') as f:
                        text_content = f.read()
                    
                    # 출력 디렉토리 설정
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    text_name = Path(doc.path).stem
                    doc_output_dir = str(self.output_dir / f"{text_name}_TEXT_{timestamp}")
                    os.makedirs(doc_output_dir, exist_ok=True)
                    
                    # 마크다운 형식으로 결과 생성
                    markdown_result = f"""# 텍스트 파일 분석 결과: {doc.filename}

## 문서 정보
- **파일명**: {doc.filename}
- **처리 시간**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **텍스트 길이**: {len(text_content)} 자

## 텍스트 내용
```
{text_content[:2000]}{'...' if len(text_content) > 2000 else ''}
```
{f'전체 텍스트는 너무 깁니다. 위 내용은 처음 2000자만 표시한 것입니다.' if len(text_content) > 2000 else ''}
"""
                    
                    # 요약 생성 (선택적)
                    summary = ""
                    if kwargs.get('model_type') and kwargs.get('model_type') != 'none':
                        try:
                            # 모델 핸들러 임포트
                            from model_handler import ModelHandler
                            
                            # 모델 초기화 및 요약 생성
                            model_handler = ModelHandler(
                                model_type=kwargs.get('model_type'),
                                model_name=kwargs.get('model_name'),
                                language=kwargs.get('language', 'ko')
                            )
                            
                            summary = model_handler.generate_summary(text_content)
                            
                            # 요약 추가
                            if summary:
                                markdown_result += f"""
## 텍스트 요약
```
{summary}
```
"""
                            
                            logger.info(f"텍스트 요약 생성 완료: {doc.filename}")
                        except Exception as e:
                            logger.error(f"텍스트 요약 생성 실패: {str(e)}")
                    
                    # 결과 저장
                    markdown_path = os.path.join(doc_output_dir, "summary.md")
                    with open(markdown_path, 'w', encoding='utf-8') as f:
                        f.write(markdown_result)
                    
                    # 텍스트 파일로도 저장
                    text_path = os.path.join(doc_output_dir, "summary.txt")
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(markdown_result)
                    
                    # JSON 형식으로도 저장
                    json_data = {
                        "document_info": {
                            "filename": doc.filename,
                            "processing_time": datetime.now().isoformat(),
                            "text_length": len(text_content)
                        },
                        "text_content": text_content,
                        "summary": summary
                    }
                    
                    json_path = os.path.join(doc_output_dir, "summary.json")
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)
                    
                    # 결과 저장
                    doc.processed = True
                    doc.output_dir = doc_output_dir
                    doc.processed_data["markdown"] = markdown_result
                    doc.processed_data["text"] = text_content
                    doc.processed_data["summary"] = summary
                    
                    logger.info(f"텍스트 문서 처리 완료: {doc.filename}")
                    
                except Exception as e:
                    logger.error(f"텍스트 파일 처리 중 오류 발생: {str(e)}")
                    raise
            else:
                raise ValueError(f"지원하지 않는 문서 타입입니다: {doc.doc_type}")
            
            # 메타데이터 저장
            self._save_metadata()
            
            return {
                "doc_id": doc_id,
                "filename": doc.filename,
                "output_dir": doc.output_dir,
                "success": True
            }
            
        except Exception as e:
            error_msg = f"문서 처리 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            
            return {
                "doc_id": doc_id,
                "filename": doc.filename,
                "error": error_msg,
                "success": False
            }
    
    def process_all_documents(self, **kwargs) -> Dict[str, Dict[str, Any]]:
        """
        모든 문서 처리
        
        Args:
            **kwargs: 추가 처리 옵션
            
        Returns:
            문서 ID를 키로 하는 처리 결과 딕셔너리
        """
        results = {}
        for doc_id in self.documents:
            try:
                results[doc_id] = self.process_document(doc_id, **kwargs)
            except Exception as e:
                results[doc_id] = {
                    "doc_id": doc_id,
                    "error": str(e),
                    "success": False
                }
        return results

    def generate_combined_markdown(self) -> str:
        """
        처리된 모든 문서의 결과를 하나의 마크다운 파일로 통합
        
        Returns:
            str: 마크다운 형식의 통합 결과
        """
        logger.info("통합 마크다운 파일 생성 시작")
        
        # 처리된 문서만 선택
        processed_docs = [doc for doc in self.documents.values() if doc.processed]
        
        if not processed_docs:
            raise ValueError("처리된 문서가 없습니다. 먼저 문서를 처리해주세요.")
        
        markdown = "# 통합 문서 분석 결과\n\n"
        markdown += f"처리 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        markdown += f"총 문서 수: {len(processed_docs)}\n\n"
        
        # 문서 목록
        markdown += "## 문서 목록\n\n"
        for i, doc in enumerate(processed_docs, 1):
            markdown += f"{i}. **{doc.filename}** (타입: {doc.doc_type})\n"
        markdown += "\n"
        
        # 각 문서의 요약 정보
        for i, doc in enumerate(processed_docs, 1):
            markdown += f"## 문서 {i}: {doc.filename}\n\n"
            
            # 문서 정보 추가
            markdown += f"### 문서 정보\n"
            markdown += f"- **파일명**: {doc.filename}\n"
            markdown += f"- **타입**: {doc.doc_type}\n"
            
            # 출력 디렉토리가 있으면 추가
            if doc.output_dir:
                markdown += f"- **출력 디렉토리**: {doc.output_dir}\n"
            
            markdown += "\n"
            
            # 요약 정보 추가 (중복 없이 한 번만)
            summary_added = False
            summary_content = None
            
            # 1. processed_data에서 요약 정보 찾기
            if doc.processed_data.get("summary"):
                summary_content = doc.processed_data['summary']
                summary_added = True
            
            # 2. 출력 디렉토리에서 요약 파일 찾기 (아직 요약이 없는 경우에만)
            if not summary_added and doc.output_dir:
                summary_files = [
                    os.path.join(doc.output_dir, "summary.md"),
                    os.path.join(doc.output_dir, "summary.txt")
                ]
                
                for path in summary_files:
                    if os.path.exists(path):
                        try:
                            with open(path, "r", encoding="utf-8") as f:
                                content = f.read()
                            
                            # 요약 파일이 있고 내용이 있는 경우
                            if content.strip():
                                # 마크다운 파일은 헤더 이후 내용만 추출
                                if path.endswith(".md") and "#" in content:
                                    # 헤더 이후 내용 추출
                                    lines = content.split("\n")
                                    for i, line in enumerate(lines):
                                        if line.startswith("#"):
                                            # 헤더 다음 줄부터 포함
                                            if i+1 < len(lines):
                                                summary_content = "\n".join(lines[i+1:]).strip()
                                                summary_added = True
                                                break
                                else:
                                    # 텍스트 파일은 전체 내용 사용
                                    summary_content = content.strip()
                                    summary_added = True
                                break
                        except Exception as e:
                            logger.warning(f"요약 파일 읽기 실패: {path} - {str(e)}")
            
            # 3. 텍스트 내용 추가 (요약이 없는 경우)
            if not summary_added and doc.processed_data.get("text"):
                text = doc.processed_data["text"]
                if len(text) > 1000:
                    text = text[:1000] + "...\n\n(내용이 너무 깁니다. 일부만 표시합니다.)"
                summary_content = text
                summary_added = True
            
            # 최종 요약 내용 추가 (단 한 번만)
            if summary_content:
                markdown += f"### 요약\n```\n{summary_content}\n```\n\n"
            
            # 4. 이미지 분석 결과 추가
            if doc.processed_data.get("markdown") and "## 이미지 분석 결과" in doc.processed_data["markdown"]:
                markdown_content = doc.processed_data["markdown"]
                img_section = markdown_content.split("## 이미지 분석 결과")[1]
                if "##" in img_section:
                    img_section = img_section.split("##")[0]
                
                # 이미지 분석 결과가 너무 길면 일부만 포함
                if len(img_section) > 2000:
                    img_section = img_section[:2000] + "...\n\n(이미지 분석 결과가 너무 깁니다. 일부만 표시합니다.)\n\n"
                
                markdown += f"### 이미지 분석 결과\n{img_section.strip()}\n\n"
            elif doc.processed_data.get("images"):
                markdown += f"### 이미지 정보\n"
                markdown += f"- **이미지 수**: {len(doc.processed_data['images'])}\n\n"
        
        # 통합 결과 저장
        combined_path = self.workspace_dir / "combined_results.md"
        with open(combined_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        logger.info(f"통합 마크다운 생성 완료: {combined_path}")
        return markdown

# 사용 예시
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='문서 관리 시스템')
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
    
    args = parser.parse_args()
    
    # 문서 관리자 초기화
    manager = DocumentsManager(workspace_dir=args.workspace)
    
    if args.command == 'add':
        for path in args.paths:
            try:
                doc_id = manager.add_document(path)
                print(f"문서 추가됨: {os.path.basename(path)} (ID: {doc_id})")
            except Exception as e:
                print(f"문서 추가 실패: {path} - {str(e)}")
    
    elif args.command == 'list':
        documents = manager.get_all_documents()
        if not documents:
            print("추가된 문서가 없습니다.")
        else:
            print(f"총 {len(documents)}개 문서:")
            for i, doc in enumerate(documents, 1):
                status = "처리됨" if doc.processed else "미처리"
                print(f"{i}. {doc.filename} (타입: {doc.doc_type}, 상태: {status}, ID: {doc.doc_id})")
    
    elif args.command == 'remove':
        if manager.remove_document(args.doc_id):
            print(f"문서 제거됨: {args.doc_id}")
        else:
            print(f"문서 제거 실패: {args.doc_id}")
    
    else:
        parser.print_help()
