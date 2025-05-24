// 선택된 문서를 기반으로 질의하는 JS 기능
document.addEventListener('DOMContentLoaded', function() {
    console.log('Query Engine JS loaded');
    
    // 문서 목록 초기 로드
    refreshDocumentList();
    
    // 질문 입력 필드와 전송 버튼
    const questionInput = document.getElementById('question-input');
    const sendBtn = document.querySelector('.send-btn');
    
    // 응답 컨테이너
    const rightSidebar = document.querySelector('.right-sidebar');
    const responseHistoryContainer = document.querySelector('.response-history-container');
    
    // 문서 체크박스
    const selectAllCheckbox = document.getElementById('select-all-sources');
    
    // 모든 소스 선택/해제 기능
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checked = this.checked;
            document.querySelectorAll('.doc-checkbox').forEach(checkbox => {
                checkbox.checked = checked;
            });
        });
    }
    
    // 질문 전송 처리
    if (sendBtn && questionInput) {
        sendBtn.addEventListener('click', function() {
            sendQuestion();
        });
        
        // Enter 키 처리
        questionInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendQuestion();
            }
        });
    }
    
    // 질문 전송 함수
    function sendQuestion() {
        const question = questionInput.value.trim();
        
        if (!question) {
            // 질문이 비어있으면 포커스
            questionInput.focus();
            return;
        }
        
        // 선택된 문서 ID 수집
        const selectedDocIds = getSelectedDocumentIds();
        
        if (selectedDocIds.length === 0) {
            alert('질문할 문서를 하나 이상 선택해주세요.');
            return;
        }
        
        // 로딩 상태 표시
        updateRightSidebar('loading', question);
        
        // 서버에 질문 전송
        fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                doc_ids: selectedDocIds
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Query response:', data);
            
            if (data.success) {
                // 응답 표시
                updateRightSidebar('response', question, data.answer);
                
                // 응답 기록에 추가
                addToResponseHistory(question, data.answer);
                
                // 입력 필드 초기화
                questionInput.value = '';
            } else {
                // 오류 표시
                updateRightSidebar('error', question, data.error || '응답을 받을 수 없습니다.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            updateRightSidebar('error', question, '서버 통신 중 오류가 발생했습니다.');
        });
    }
    
    // 선택된 문서 ID 가져오기
    function getSelectedDocumentIds() {
        const checkboxes = document.querySelectorAll('.doc-checkbox:checked');
        return Array.from(checkboxes).map(checkbox => checkbox.getAttribute('data-id'));
    }
    
    // 오른쪽 사이드바 업데이트
    function updateRightSidebar(state, question, content = '') {
        if (!rightSidebar) return;
        
        const aiResponseArea = rightSidebar.querySelector('.ai-response-area') || 
                               document.createElement('div');
        
        aiResponseArea.className = 'ai-response-area';
        
        if (state === 'loading') {
            aiResponseArea.innerHTML = `
                <div class="ai-response-header">
                    <div class="ai-badge">
                        <span class="material-icons">psychology</span>
                        <span>AI 응답 생성 중...</span>
                    </div>
                </div>
                <div class="ai-response-content loading">
                    <div class="loading-indicator">
                        <span class="material-icons spin">autorenew</span>
                        <span>문서를 분석하고 응답을 생성하는 중...</span>
                    </div>
                </div>
            `;
        } else if (state === 'response') {
            aiResponseArea.innerHTML = `
                <div class="ai-response-header">
                    <div class="ai-badge">
                        <span class="material-icons">psychology</span>
                        <span>AI 응답</span>
                    </div>
                    <div class="ai-actions">
                        <button class="copy-btn" title="복사">
                            <span class="material-icons">content_copy</span>
                        </button>
                        <button class="save-memo-btn" title="메모/원본 추가">
                            <span class="material-icons">note_add</span>
                        </button>
                    </div>
                </div>
                <div class="ai-question">
                    <strong>질문:</strong> ${question}
                </div>
                <div class="ai-response-content">
                    ${formatResponse(content)}
                </div>
            `;
            
            // 복사 버튼 이벤트 처리
            const copyBtn = aiResponseArea.querySelector('.copy-btn');
            if (copyBtn) {
                copyBtn.addEventListener('click', function() {
                    copyTextToClipboard(content);
                    alert('응답이 클립보드에 복사되었습니다.');
                });
            }
            
            // 메모/원본 추가 버튼 이벤트 처리
            const saveMemoBtn = aiResponseArea.querySelector('.save-memo-btn');
            if (saveMemoBtn) {
                saveMemoBtn.addEventListener('click', function() {
                    saveMemoAndSource(question, content);
                });
            }
        } else if (state === 'error') {
            aiResponseArea.innerHTML = `
                <div class="ai-response-header">
                    <div class="ai-badge error">
                        <span class="material-icons">error</span>
                        <span>오류 발생</span>
                    </div>
                </div>
                <div class="ai-question">
                    <strong>질문:</strong> ${question}
                </div>
                <div class="ai-response-content error">
                    <p>${content}</p>
                </div>
            `;
        }
        
        // 응답 영역 추가 (없는 경우)
        if (!rightSidebar.querySelector('.ai-response-area')) {
            rightSidebar.prepend(aiResponseArea);
        }
    }
    
    // 응답 기록에 추가
    function addToResponseHistory(question, answer) {
        if (!responseHistoryContainer) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const responseItem = document.createElement('div');
        responseItem.className = 'response-item';
        responseItem.innerHTML = `
            <div class="response-title">${question}</div>
            <div class="response-timestamp">${timestamp}</div>
        `;
        
        // 클릭 시 응답 표시
        responseItem.addEventListener('click', function() {
            updateRightSidebar('response', question, answer);
        });
        
        // 기록 컨테이너에 추가
        responseHistoryContainer.prepend(responseItem);
    }
    
    // 응답 텍스트 포맷팅
    function formatResponse(text) {
        return text.replace(/\n/g, '<br>');
    }
    
    // 텍스트를 클립보드에 복사
    function copyTextToClipboard(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }
    
    // 메모와 원본을 저장하는 함수
    function saveMemoAndSource(question, answer) {
        // 로딩 표시
        const saveMemoBtn = document.querySelector('.save-memo-btn');
        if (saveMemoBtn) {
            saveMemoBtn.disabled = true;
            saveMemoBtn.innerHTML = '<span class="material-icons spin">autorenew</span>';
        }
        
        // 선택된 문서 ID 가져오기
        const selectedDocIds = getSelectedDocumentIds();
        
        // 메모 내용 구성
        const memoContent = `# ${question}\n\n${answer}`;
        
        // 서버에 저장 요청
        fetch('/api/save_memo', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: memoContent,
                question: question,
                source_doc_ids: selectedDocIds
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Memo saved:', data);
            
            if (data.success) {
                // 문서 목록 새로고침
                refreshDocumentList(data.doc_id);
                
                // 버튼 상태 복원
                if (saveMemoBtn) {
                    saveMemoBtn.disabled = false;
                    saveMemoBtn.innerHTML = '<span class="material-icons">note_add</span>';
                }
                
                alert('메모/원본이 성공적으로 저장되었습니다.');
            } else {
                // 오류 표시
                if (saveMemoBtn) {
                    saveMemoBtn.disabled = false;
                    saveMemoBtn.innerHTML = '<span class="material-icons">note_add</span>';
                }
                alert('메모/원본 저장 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            
            // 버튼 상태 복원
            if (saveMemoBtn) {
                saveMemoBtn.disabled = false;
                saveMemoBtn.innerHTML = '<span class="material-icons">note_add</span>';
            }
            
            alert('메모/원본 저장 중 오류가 발생했습니다.');
        });
    }
    
    // 문서 목록 새로고침
    function refreshDocumentList(newDocId) {
        // 문서 목록을 다시 로드
        fetch('/api/documents')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const documentList = document.getElementById('document-list');
                    if (!documentList) return;
                    
                    // 기존 문서 목록 비우기
                    documentList.innerHTML = '';
                    
                    // 문서가 없는 경우 메시지 표시
                    if (!data.documents || data.documents.length === 0) {
                        documentList.innerHTML = `
                            <div class="empty-documents-message">
                                <span class="material-icons">info</span>
                                <p>문서 목록이 비어 있습니다.</p>
                                <p class="empty-hint">왼쪽 상단의 + 버튼을 클릭하여 새 문서를 추가하세요.</p>
                            </div>
                        `;
                        return;
                    }
                    
                    // 문서 목록 생성
                    data.documents.forEach(doc => {
                        const docElement = document.createElement('div');
                        docElement.className = `document-item ${doc.doc_id === newDocId ? 'selected' : ''} ${doc.selected ? 'selected' : ''}`;
                        docElement.setAttribute('data-id', doc.doc_id);
                        
                        docElement.innerHTML = `
                            <div class="doc-checkbox-container">
                                <input type="checkbox" class="doc-checkbox" data-id="${doc.doc_id}" ${doc.processed ? 'checked' : ''}>
                            </div>
                            <div class="doc-icon">
                                <span class="material-icons">
                                    ${doc.doc_type === 'pdf' ? 'picture_as_pdf' : 'description'}
                                </span>
                            </div>
                            <div class="doc-info">
                                <div class="doc-title">${doc.filename}</div>
                                <div class="doc-meta">
                                    <span class="doc-type">${doc.doc_type.toUpperCase()}</span>
                                    <span class="doc-status ${doc.processed ? 'processed' : 'unprocessed'}">
                                        ${doc.processed ? '처리됨' : '미처리'}
                                    </span>
                                </div>
                            </div>
                            <div class="doc-actions">
                                <button class="icon-btn delete-btn" data-id="${doc.doc_id}" title="삭제">
                                    <span class="material-icons">delete</span>
                                </button>
                            </div>
                        `;
                        
                        documentList.appendChild(docElement);
                    });
                    
                    // 체크박스 이벤트 추가
                    document.querySelectorAll('.doc-checkbox').forEach(checkbox => {
                        checkbox.addEventListener('change', function() {
                            // 선택된 문서 개수 업데이트
                            updateSelectedDocsCount();
                        });
                    });
                    
                    // 문서 선택 이벤트 추가
                    document.querySelectorAll('.document-item').forEach(item => {
                        item.addEventListener('click', function(e) {
                            // 삭제 버튼 또는 체크박스 클릭은 무시
                            if (
                                e.target.classList.contains('delete-btn') || 
                                e.target.closest('.delete-btn') ||
                                e.target.classList.contains('doc-checkbox') ||
                                e.target.closest('.doc-checkbox-container')
                            ) return;
                            
                            // 문서 선택 상태 토글
                            this.classList.toggle('selected');
                        });
                    });
                    
                    // 삭제 버튼 이벤트 추가
                    document.querySelectorAll('.delete-btn').forEach(btn => {
                        btn.addEventListener('click', function() {
                            const docId = this.getAttribute('data-id');
                            if (confirm('정말로 이 문서를 삭제하시겠습니까?')) {
                                deleteDocument(docId);
                            }
                        });
                    });
                    
                    // 선택된 문서 개수 업데이트
                    updateSelectedDocsCount();
                }
            })
            .catch(error => console.error('Error loading documents:', error));
    }
    
    // 선택된 문서 개수 업데이트
    function updateSelectedDocsCount() {
        const selectedCount = document.querySelectorAll('.doc-checkbox:checked').length;
        const countElement = document.getElementById('selected-docs-count');
        if (countElement) {
            countElement.textContent = selectedCount;
        }
    }
    
    // 문서 삭제
    function deleteDocument(docId) {
        fetch(`/api/documents/${docId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 문서 목록 새로고침
                refreshDocumentList();
            } else {
                alert('문서 삭제 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('문서 삭제 중 오류가 발생했습니다.');
        });
    }
});
