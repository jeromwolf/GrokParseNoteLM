// GrokParseNoteLM 웹 인터페이스 JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // 파일 업로드 처리
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('file-input');
            const file = fileInput.files[0];
            
            if (!file) {
                showUploadStatus('파일을 선택해주세요.', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            // 업로드 상태 표시
            showUploadStatus('업로드 중...', 'loading');
            
            // 서버에 업로드 요청
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showUploadStatus(data.message, 'success');
                    
                    // 문서 처리 상태 주기적으로 확인
                    if (data.task_id) {
                        checkProcessingStatus(data.task_id);
                    }
                } else {
                    showUploadStatus(data.error, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showUploadStatus('업로드 중 오류가 발생했습니다.', 'error');
            });
        });
    }
    
    // 질의 처리
    const queryBtn = document.getElementById('query-btn');
    if (queryBtn) {
        queryBtn.addEventListener('click', function() {
            const queryInput = document.getElementById('query-input');
            const queryText = queryInput.value.trim();
            
            if (!queryText) {
                alert('질문을 입력해주세요.');
                return;
            }
            
            const responseContainer = document.querySelector('.response-container');
            responseContainer.innerHTML = '<div class="loading-indicator">처리 중...</div>';
            
            // 문서 상세 페이지에서 질의인 경우
            const docId = this.getAttribute('data-id');
            const selectedDocs = Array.from(document.querySelectorAll('.doc-checkbox:checked')).map(el => el.getAttribute('data-id'));
            
            const requestData = {
                query: queryText,
                doc_id: docId,
                doc_ids: selectedDocs
            };
            
            // 서버에 질의 요청
            fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: queryText })
            })
            .then(response => response.json())
            .then(data => {
                if (data.response) {
                    responseContainer.innerHTML = `
                        <div class="response-text">
                            <div class="response-header">
                                <h3>응답:</h3>
                                <span class="model-info">모델: ${data.model || 'Unknown'}</span>
                            </div>
                            <div class="response-content">${data.response.replace(/\n/g, '<br>')}</div>
                        </div>
                    `;
                } else {
                    responseContainer.innerHTML = `<div class="error-message">${data.error || '질의 처리 중 오류가 발생했습니다.'}</div>`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                responseContainer.innerHTML = '<div class="error-message">질의 처리 중 오류가 발생했습니다.</div>';
            });
        });
    }
    
    // 도구 액션 설정
    function setupToolsActions() {
        // 통합 마크다운 생성 버튼
        domElements.generateCombinedBtn.addEventListener('click', function() {
            this.disabled = true;
            this.textContent = '생성 중...';
            
            fetch('/api/generate_combined', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('통합 마크다운이 생성되었습니다.');
                    // 마크다운 다운로드 또는 표시 기능 추가 가능
                } else {
                    alert(data.error || '통합 마크다운 생성 중 오류가 발생했습니다.');
                }
                
                this.disabled = false;
                this.textContent = '통합 마크다운 생성';
            })
            .catch(error => {
                console.error('Error:', error);
                alert('통합 마크다운 생성 중 오류가 발생했습니다.');
                this.disabled = false;
                this.textContent = '통합 마크다운 생성';
            });
        });
    }
    
    // 탭 기능 (문서 상세 페이지)
    const tabBtns = document.querySelectorAll('.tab-btn');
    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                // 활성 탭 버튼 변경
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                // 탭 내용 변경
                const tabId = this.getAttribute('data-tab');
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.add('hidden');
                });
                document.getElementById(`${tabId}-content`).classList.remove('hidden');
            });
        });
    }
    
    // 헬퍼 함수: 업로드 상태 표시
    function showUploadStatus(message, type) {
        const statusDiv = document.getElementById('upload-status');
        if (!statusDiv) return;
        
        statusDiv.textContent = message;
        statusDiv.className = `status-message ${type}`;
    }
    
    // 헬퍼 함수: 처리 상태 확인
    function checkProcessingStatus(taskId, shouldReload = false) {
        let checkCount = 0;
        const maxChecks = 60; // 최대 확인 횟수 (60회 = 약 3분)
        
        function checkStatus() {
            fetch(`/api/task/${taskId}`)
                .then(response => response.json())
                .then(data => {
                    checkCount++;
                    
                    if (data.status === 'completed') {
                        if (shouldReload) {
                            // 처리 완료 후 페이지 새로고침
                            window.location.reload();
                        } else {
                            // 문서 목록 페이지일 경우 해당 문서 링크 표시
                            showUploadStatus('처리 완료! 문서를 확인하세요.', 'success');
                            // 목록 새로고침을 위한 딜레이 후 페이지 리로드
                            setTimeout(() => window.location.reload(), 2000);
                        }
                    } else if (data.status === 'failed') {
                        if (shouldReload) {
                            alert(`문서 처리 실패: ${data.error || '알 수 없는 오류'}`);
                            const processBtn = document.getElementById('process-btn');
                            const processingIndicator = document.getElementById('processing-indicator');
                            if (processBtn) processBtn.disabled = false;
                            if (processingIndicator) processingIndicator.classList.add('hidden');
                        } else {
                            showUploadStatus(`처리 실패: ${data.error || '알 수 없는 오류'}`, 'error');
                        }
                    } else if (checkCount < maxChecks) {
                        // 아직 처리 중이면 3초 후 다시 확인
                        setTimeout(checkStatus, 3000);
                    } else {
                        // 최대 확인 횟수 초과 시
                        if (shouldReload) {
                            alert('처리 상태 확인 시간이 초과되었습니다. 나중에 다시 확인해주세요.');
                            const processBtn = document.getElementById('process-btn');
                            const processingIndicator = document.getElementById('processing-indicator');
                            if (processBtn) processBtn.disabled = false;
                            if (processingIndicator) processingIndicator.classList.add('hidden');
                        } else {
                            showUploadStatus('처리 중입니다. 나중에 다시 확인해주세요.', 'info');
                        }
                    }
                })
                .catch(error => {
                    console.error('Error checking task status:', error);
                    if (shouldReload) {
                        alert('처리 상태 확인 중 오류가 발생했습니다.');
                        const processBtn = document.getElementById('process-btn');
                        const processingIndicator = document.getElementById('processing-indicator');
                        if (processBtn) processBtn.disabled = false;
                        if (processingIndicator) processingIndicator.classList.add('hidden');
                    } else {
                        showUploadStatus('처리 상태 확인 중 오류가 발생했습니다.', 'error');
                    }
                });
        }
        
        // 최초 상태 확인 시작
        checkStatus();
    }
});
