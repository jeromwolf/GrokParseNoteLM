from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import os
import sys
import json
import uuid
import time
import threading
from datetime import datetime
from werkzeug.utils import secure_filename
from pathlib import Path

# 현재 디렉토리를 시스템 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 기존 모듈 import
from document_manager import Document, DocumentsManager
from query_engine import QueryEngine

# 템플릿 및 정적 파일 디렉터리 설정
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GrokParseNoteLM/templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GrokParseNoteLM/static')

# 디렉터리가 존재하는지 확인 및 디버깅 정보 출력
if not os.path.exists(template_dir):
    print(f"경고: 템플릿 디렉터리가 존재하지 않습니다: {template_dir}")
    # 상대 경로로 시도
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    print(f"대체 경로 시도: {template_dir}")

if not os.path.exists(static_dir):
    print(f"경고: 정적 파일 디렉터리가 존재하지 않습니다: {static_dir}")
    # 상대 경로로 시도
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    print(f"대체 경로 시도: {static_dir}")

# 정적 파일 디렉터리 구조 확인
img_dir = os.path.join(static_dir, 'img')
if os.path.exists(img_dir):
    print(f"이미지 디렉터리 존재: {img_dir}")
    img_files = os.listdir(img_dir)
    print(f"이미지 파일 리스트: {img_files}")
else:
    print(f"이미지 디렉터리가 존재하지 않습니다: {img_dir}")
    # 이미지 디렉터리 생성 시도
    try:
        os.makedirs(img_dir, exist_ok=True)
        print(f"이미지 디렉터리 생성 완료: {img_dir}")
    except Exception as e:
        print(f"이미지 디렉터리 생성 실패: {str(e)}")


app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = 'dev_key'  # 실제 환경에서는 환경변수로 관리

# 애플리케이션 설정
app.config['WORKSPACE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GrokParseNoteLM/workspace')
app.config['UPLOAD_FOLDER'] = os.path.join(app.config['WORKSPACE_DIR'], 'documents')
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB 제한

# 데이터 디렉토리 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 문서 관리자 초기화 (기존 문서 무시 옵션 추가)
documents_manager = DocumentsManager(workspace_dir=app.config['WORKSPACE_DIR'])

# 기존 문서 목록 비우기 (시작 시 기존 문서 표시하지 않기 위해)
documents_manager.documents = {}

# 쿼리 엔진 초기화 (OpenAI 모델 사용)
query_engine = QueryEngine(model_type="openai")

# 처리 작업 상태 저장
processing_tasks = {}

@app.route('/')
def index():
    # URL 파라미터로 문서 로드 여부 확인
    load_docs = request.args.get('load_docs', default='false')
    
    if load_docs == 'true':
        # 문서 추가 후 로드시에는 목록 표시
        documents = documents_manager.get_all_documents()
        doc_list = [doc.to_dict() for doc in documents]
    else:
        # 초기 로드시에는 문서 목록 표시하지 않음
        doc_list = []
    
    return render_template('index.html', documents=doc_list)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '파일이 없습니다'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '파일 이름이 없습니다'}), 400
    
    if file and file.filename.endswith(('.pdf', '.txt', '.md', '.markdown')):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # 문서 추가
            doc_id = documents_manager.add_document(file_path)
            
            # 비동기 문서 처리 시작
            task_id = str(uuid.uuid4())
            processing_tasks[task_id] = {
                'status': 'processing',
                'doc_id': doc_id,
                'start_time': time.time()
            }
            
            # 자동으로 문서 처리 시작 (비동기)
            threading.Thread(target=process_document_async, args=(doc_id, task_id)).start()
            
            return jsonify({
                'success': True, 
                'message': '파일이 성공적으로 업로드되었습니다.',
                'task_id': task_id,
                'doc_id': doc_id,
                'redirect_url': '/?load_docs=true'
            })
        except Exception as e:
            return jsonify({'error': f'문서 추가 실패: {str(e)}'}), 500
    
    return jsonify({'error': '지원하지 않는 파일 형식입니다'}), 400

@app.route('/document/<string:doc_id>')
def view_document(doc_id):
    document = documents_manager.get_document(doc_id)
    if document:
        # 문서 정보를 딕셔너리로 변환
        doc_dict = document.to_dict()
        
        # 처리된 문서가 있으면 내용 로드
        if document.processed and document.output_dir:
            # 마크다운 내용 로드
            try:
                markdown_path = os.path.join(document.output_dir, "markdown_result.md")
                if os.path.exists(markdown_path):
                    with open(markdown_path, 'r', encoding='utf-8') as f:
                        doc_dict['content'] = f.read()
                else:
                    doc_dict['content'] = "마크다운 결과 파일을 찾을 수 없습니다."
            except Exception as e:
                doc_dict['content'] = f"문서 내용 로드 실패: {str(e)}"
        else:
            doc_dict['content'] = "문서가 아직 처리되지 않았습니다. 처리가 완료되면 내용이 표시됩니다."
        
        # 모든 문서 목록 가져오기
        all_documents = documents_manager.get_all_documents()
        all_docs = [doc.to_dict() for doc in all_documents]
        
        return render_template('document.html', document=doc_dict, documents=all_docs)
    
    return redirect(url_for('index'))

@app.route('/api/query', methods=['POST'])
def process_query():
    data = request.get_json()
    question = data.get('question', '')
    doc_id = data.get('doc_id')
    doc_ids = data.get('doc_ids', [])
    
    if not question:
        return jsonify({'error': '질문을 입력해주세요', 'success': False}), 400
    
    try:
        # 특정 문서가 지정된 경우 (단일 문서)
        if doc_id:
            document = documents_manager.get_document(doc_id)
            if not document:
                return jsonify({'error': '문서를 찾을 수 없습니다', 'success': False}), 404
            
            if not document.processed:
                return jsonify({'error': '문서가 아직 처리되지 않았습니다', 'success': False}), 400
            
            # 단일 문서 기반 질의
            if document.processed_data.get("markdown"):
                context = document.processed_data["markdown"]
                result = query_engine.query(question, context)
            else:
                return jsonify({'error': '문서 처리 결과를 찾을 수 없습니다', 'success': False}), 404
        
        # 체크된 문서들이 있는 경우
        elif doc_ids and len(doc_ids) > 0:
            # 선택된 문서 유효성 검사
            valid_doc_ids = []
            for doc_id in doc_ids:
                doc = documents_manager.get_document(doc_id)
                if doc and doc.processed:
                    valid_doc_ids.append(doc_id)
            
            if not valid_doc_ids:
                return jsonify({'error': '선택된 문서 중 처리된 문서가 없습니다', 'success': False}), 400
            
            # 선택된 문서들만 기반으로 질의
            result = query_engine.query_with_documents(question, documents_manager, valid_doc_ids)
        else:
            # 모든 문서 기반 질의
            result = query_engine.query_with_documents(question, documents_manager)
        
        if result.get('success', False):
            return jsonify({
                'success': True,
                'answer': result['answer'],
                'model': result.get('model', 'Unknown'),
                'documents': result.get('documents', [])
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', '질의 처리 중 오류가 발생했습니다')
            }), 500
            
    except Exception as e:
        print(f"질의 처리 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'질의 처리 중 오류 발생: {str(e)}'
        }), 500

# 문서 처리 비동기 함수
def process_document_async(doc_id, task_id):
    try:
        # 문서 처리 (OpenAI 모델 사용)
        result = documents_manager.process_document(
            doc_id,
            model_type="openai",
            parser="pymupdf",  # 문서 파서 지정
            language="ko"      # 한국어 처리
        )
        
        # 처리 완료 상태 업데이트
        processing_tasks[task_id] = {
            'status': 'completed',
            'doc_id': doc_id,
            'result': result,
            'end_time': time.time()
        }
    except Exception as e:
        # 처리 실패 상태 업데이트
        processing_tasks[task_id] = {
            'status': 'failed',
            'doc_id': doc_id,
            'error': str(e),
            'end_time': time.time()
        }

# 처리 작업 상태 확인 API
@app.route('/api/task/<string:task_id>', methods=['GET'])
def get_task_status(task_id):
    if task_id in processing_tasks:
        task = processing_tasks[task_id]
        return jsonify(task)
    return jsonify({'error': '작업을 찾을 수 없습니다'}), 404

# 이미지 파일 서빙
@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(os.path.join(app.config['WORKSPACE_DIR'], 'output/images'), filename)

# 문서 삭제 API
@app.route('/api/document/<string:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    try:
        # 문서 삭제 실행
        success = documents_manager.remove_document(doc_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '문서가 삭제되었습니다.'
            })
        else:
            return jsonify({
                'success': False,
                'error': '문서를 찾을 수 없습니다.'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'문서 삭제 중 오류 발생: {str(e)}'
        }), 500

# 통합 마크다운 생성 API
@app.route('/api/generate_combined', methods=['POST'])
def generate_combined_markdown():
    try:
        markdown = documents_manager.generate_combined_markdown()
        return jsonify({
            'success': True,
            'markdown': markdown
        })
    except Exception as e:
        return jsonify({'error': f'통합 마크다운 생성 실패: {str(e)}'}), 500

# 처리된 문서 내용 가져오기 API
@app.route('/api/document/<doc_id>/processed', methods=['GET'])
def get_processed_document(doc_id):
    try:
        # 문서 가져오기
        document = documents_manager.get_document(doc_id)
        if not document:
            return jsonify({
                'success': False,
                'error': '문서를 찾을 수 없습니다.'
            }), 404
            
        # 문서가 처리되지 않은 경우 처리 진행
        if not document.processed:
            result = documents_manager.process_document(
                doc_id,
                model_type="openai",
                parser="pymupdf",
                language="ko"
            )
        
        # 처리된 문서 데이터 반환
        response_data = {
            'success': True,
            'title': document.filename,
            'content': document.processed_data.get('text', ''),
            'summary': document.processed_data.get('summary', ''),
            'images': document.processed_data.get('images', [])
        }
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 메모/원본 추가 API
@app.route('/api/save_memo', methods=['POST'])
def save_memo():
    try:
        data = request.json
        if not data or 'content' not in data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': '필수 데이터가 누락되었습니다.'
            }), 400
        
        # 필수 정보 추출
        content = data['content']
        question = data['question']
        source_doc_ids = data.get('source_doc_ids', [])
        
        # 메모 파일 생성
        memo_filename = f"메모_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        memo_path = os.path.join(app.config['UPLOAD_FOLDER'], memo_filename)
        
        with open(memo_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 문서 관리자에 메모 추가
        doc_id = documents_manager.add_document(memo_path)
        
        # 메모 문서 처리 (즉시 처리하여 사용 가능하도록)
        result = documents_manager.process_document(
            doc_id,
            model_type="openai",
            parser="pymupdf",
            language="ko"
        )
        
        # 성공 응답 반환
        return jsonify({
            'success': True,
            'doc_id': doc_id,
            'filename': memo_filename,
            'message': '메모/원본이 성공적으로 저장되었습니다.'
        })
    except Exception as e:
        logger.error(f"메모 저장 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'메모 저장 중 오류 발생: {str(e)}'
        }), 500

# 문서 목록 API
@app.route('/api/documents', methods=['GET'])
def get_documents():
    try:
        documents = documents_manager.get_all_documents()
        doc_list = [doc.to_dict() for doc in documents]
        
        return jsonify({
            'success': True,
            'documents': doc_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'문서 목록 조회 중 오류 발생: {str(e)}'
        }), 500

if __name__ == "__main__":
    print(f"템플릿 디렉터리: {template_dir}")
    print(f"정적 파일 디렉터리: {static_dir}")
    app.run(debug=True, port=5007)
