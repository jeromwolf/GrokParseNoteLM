// 선택된 문서를 기반으로 질의하는 JS 기능
// 알림 표시 함수
function showNotification(message, type = 'info', duration = 3000) {
    // 기존 알림 요소 제거
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => {
        notification.remove();
    });
    
    // 새 알림 요소 생성
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        padding: 12px 20px;
        background-color: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196F3'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
        transition: all 0.3s ease;
        transform: translateX(120%);
    `;
    
    // 아이콘 추가
    const icon = document.createElement('span');
    icon.className = 'material-icons';
    icon.style.cssText = 'margin-right: 8px;';
    icon.textContent = type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info';
    notification.appendChild(icon);
    
    // 메시지 추가
    const messageElement = document.createElement('span');
    messageElement.textContent = message;
    notification.appendChild(messageElement);
    
    // 닫기 버튼 추가
    const closeBtn = document.createElement('span');
    closeBtn.className = 'material-icons';
    closeBtn.textContent = 'close';
    closeBtn.style.cssText = 'margin-left: 8px; cursor: pointer; font-size: 18px;';
    closeBtn.addEventListener('click', () => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    });
    notification.appendChild(closeBtn);
    
    // body에 추가
    document.body.appendChild(notification);
    
    // 애니메이션 효과
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // 일정 시간 후 자동 삭제
    if (duration > 0) {
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(120%)';
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
    
    return notification;
}

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
                // 버튼 상태 복원
                if (saveMemoBtn) {
                    saveMemoBtn.disabled = false;
                    saveMemoBtn.innerHTML = '<span class="material-icons">note_add</span>';
                }
                
                // 새로고침 대신 알림 표시
                showNotification('메모/원본이 성공적으로 저장되었습니다.', 'success');
                
                // 3초 후 페이지 새로고침 (전체 페이지 새로고침)
                setTimeout(() => {
                    window.location.reload();
                }, 3000);
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
    
    // 문서 파일명 정보 저장을 위한 전역 변수
    window.originalDocumentNames = window.originalDocumentNames || {};
    
    // 문서 목록 새로고침
    // 파일명 저장을 위한 전역 객체
    window.originalFileNames = window.originalFileNames || {};
    
    // 문서 목록 새로고침
    function refreshDocumentList(newDocId) {
        // 클릭 후 다시 로드하지 않기
        if (window.isDocumentClicked) {
            console.log('문서 클릭 후 다시 로드하지 않음');
            return;
        }
        
        // 현재 선택된 문서 저장
        if (!newDocId) {
            const selectedDoc = document.querySelector('.document-item.selected');
            if (selectedDoc) {
                newDocId = selectedDoc.getAttribute('data-id');
            }
        }
        
        // 문서 목록 컨테이너 참조
        const documentList = document.getElementById('document-list');
        if (!documentList) return;
        
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
                            <div class="empty-documents-message" style="text-align:center; padding:30px; margin-top:20px; background-color:#f9f9f9; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1);">
                                <span class="material-icons" style="font-size:48px; color:#2196F3; margin-bottom:15px;">description</span>
                                <h3 style="margin:0 0 10px 0; color:#333; font-size:18px; font-weight:500;">문서 목록이 비어 있습니다</h3>
                                <p style="margin:0 0 20px 0; color:#666; font-size:14px;">처리할 문서를 추가하면 이 곳에 표시됩니다.</p>
                                <div style="display:inline-flex; align-items:center; background-color:#e3f2fd; padding:8px 16px; border-radius:4px; color:#0d47a1; font-size:14px;">
                                    <span class="material-icons" style="font-size:16px; margin-right:8px;">add</span>
                                    <span>왼쪽 상단의 <strong>+</strong> 버튼을 클릭하여 새 문서를 추가하세요</span>
                                </div>
                            </div>
                        `;
                        return;
                    }
                    
                    // 문서 파일명 캐싱 (파일명 변경 방지)
                    if (!window.documentFileNames) {
                        window.documentFileNames = {};
                    }
                    
                    // 문서 데이터 자체는 그대로 사용
                    data.documents.forEach(doc => {
                        // 이미 캐싱된 파일명이 있으면 그것을 사용, 없으면 현재 파일명 저장
                        if (!window.documentFileNames[doc.doc_id]) {
                            window.documentFileNames[doc.doc_id] = doc.filename;
                            console.log(`파일명 캐싱 추가: ${doc.doc_id} => ${doc.filename}`);
                        }
                    });
                    
                    // 가장 단순한 방법 - 이름과 형식 보존
                    // 그냥 서버에서 가져온 데이터 사용
                    const docList = data.documents || [];
                    
                    // 클릭 시 변경되지 않게 한 번만 그리기
                    // 서버 유형(PDF/TEXT) 보존
                    if (!window.documentListRendered) {
                        window.documentListRendered = true;
                        console.log('문서 목록 최초 렌더링 - 문서 수:', docList.length);
                    } else {
                        // 최초 렌더링 이후로는 중복 파일명 처리를 위해 클릭 이벤트만 바꿈
                        console.log('초기화 완료, 파일명 변경 방지 모드');
                        return; // 문서 목록 이미 그려져 있으면 이후로 다시 그리지 않음
                    }
                    
                    // 문서 그룹화 - 파일명 기준
                    const groupedDocuments = {};
                    
                    // 그룹화는 처음에만 실행
                    docList.forEach(doc => {
                        // 파일명에서 확장자를 제외한 기본 이름 추출
                        const baseFileName = doc.filename.substring(0, doc.filename.lastIndexOf('.')) || doc.filename;
                        
                        if (!groupedDocuments[baseFileName]) {
                            groupedDocuments[baseFileName] = [];
                        }
                        groupedDocuments[baseFileName].push(doc);
                    });
                    
                    console.log('그룹화된 문서:', groupedDocuments);
                    
                    // 원본 파일명 저장
                    data.documents.forEach(doc => {
                        // 처음 보는 파일이면 이름 저장
                        if (!window.originalDocumentNames[doc.doc_id]) {
                            window.originalDocumentNames[doc.doc_id] = doc.filename;
                            console.log(`원본 파일명 저장: ${doc.doc_id} => ${doc.filename}`);
                        }
                    });
                    
                    // 2. 그룹화된 문서 표시 - 중복 제거
                    const uniqueDocs = {};
                    
                    // 같은 파일명을 가진 문서 중 하나만 선택
                    data.documents.forEach(doc => {
                        // 저장된 원본 파일명 사용
                        const origFilename = window.originalDocumentNames[doc.doc_id] || doc.filename;
                        const simpleKey = origFilename.toLowerCase();
                        
                        // 처리된 문서 우선 저장
                        if (!uniqueDocs[simpleKey] || doc.processed) {
                            uniqueDocs[simpleKey] = doc;
                        }
                    });
                    
                    // 중복이 제거된 문서만 표시
                    Object.values(uniqueDocs).forEach(doc => {
                        // 원본 파일명 사용
                        const origFilename = window.originalDocumentNames[doc.doc_id] || doc.filename;
                        
                        const docElement = document.createElement('div');
                        docElement.className = `document-item ${doc.doc_id === newDocId ? 'selected' : ''} ${doc.selected ? 'selected' : ''}`;
                        docElement.setAttribute('data-id', doc.doc_id);
                        docElement.setAttribute('data-original-name', origFilename);
                        
                        // 문서 형식에 따른 아이콘 선택
                        const docIcon = doc.doc_type === 'pdf' ? 'picture_as_pdf' : 'description';
                        
                        docElement.innerHTML = `
                            <div class="doc-checkbox-container">
                                <input type="checkbox" class="doc-checkbox" data-id="${doc.doc_id}" ${doc.processed ? 'checked' : ''}>
                            </div>
                            <div class="doc-icon">
                                <span class="material-icons">
                                    ${docIcon}
                                </span>
                            </div>
                            <div class="doc-info">
                                <div class="doc-title" title="파일명: ${doc.filename}" data-original-name="${doc.filename}">${doc.filename}</div>
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
                    
                    // 문서 선택 이벤트 추가 - 문서 목록 위에 이벤트 위임 방식 적용
                    const docListContainer = document.getElementById('document-list');
                    if (docListContainer) {
                        // 기존 이벤트 제거 후 새로 이벤트 구성
                        docListContainer.onclick = function(e) {
                            // 삭제 버튼 또는 체크박스 클릭은 무시
                            if (
                                e.target.classList.contains('delete-btn') || 
                                e.target.closest('.delete-btn') ||
                                e.target.classList.contains('doc-checkbox') ||
                                e.target.closest('.doc-checkbox-container')
                            ) return;
                            
                            // 클릭한 문서 아이템 찾기
                            const docItem = e.target.closest('.document-item');
                            if (!docItem) return;
                            
                            // 문서 ID 가져오기
                            const docId = docItem.getAttribute('data-id');
                            if (!docId) return;
                            
                            // 이전에 선택된 아이템이 있으면 선택 상태 제거
                            document.querySelectorAll('.document-item.selected').forEach(selectedItem => {
                                if (selectedItem !== docItem) {
                                    selectedItem.classList.remove('selected');
                                }
                            });
                            
                            // 현재 아이템 선택
                            docItem.classList.add('selected');
                            
                            // 클릭 후에는 목록이 다시 그려지지 않도록 플래그 설정
                            window.isDocumentClicked = true;
                            
                            // 파일명 요소 찾기
                            const titleElement = docItem.querySelector('.doc-title');
                            const currentFilename = titleElement.textContent;
                            
                            // 파일명 고정: data-original-name 속성에서 원본 파일명 가져오기
                            const originalName = titleElement.getAttribute('data-original-name') || currentFilename;
                            
                            // 파일명 강제 고정 - 별도 함수로 파일명 복원 코드 분리
                            function maintainFilename() {
                                // 파일명이 변경되었으면 원래 이름으로 복원
                                if (titleElement.textContent !== originalName) {
                                    console.log(`파일명 복원: ${titleElement.textContent} -> ${originalName}`);
                                    titleElement.textContent = originalName;
                                }
                            }
                            
                            // 즉시 파일명 확인
                            maintainFilename();
                            
                            // 일정 시간 후에도 파일명 확인 (비동기 변경 대응)
                            setTimeout(maintainFilename, 100);
                            setTimeout(maintainFilename, 500);
                            
                            console.log(`문서 선택: ${docId}, 파일명 고정: ${originalName}`);
                            
                            // 추가 이벤트 처리가 필요한 경우 여기에 추가
                        };
                        
                        console.log('문서 목록 이벤트 처리기 설정 완료');
                    }
                    
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
