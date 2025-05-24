// 간단하고 직접적인 문서 선택 이벤트 처리
document.addEventListener('DOMContentLoaded', function() {
    console.log('간단한 문서 선택 스크립트가 로드되었습니다.');
    
    // 문서 내용 로드 함수
    function loadDocument(docId, isProcessed) {
        console.log('문서 로드 시작:', docId, '처리 상태:', isProcessed ? '처리됨' : '미처리');
        
        // 문서 내용 영역
        const mainContent = document.querySelector('.document-content');
        if (!mainContent) {
            console.error('문서 내용을 표시할 영역을 찾을 수 없습니다.');
            return;
        }
        
        // 미처리 문서인 경우 처리 시작
        if (!isProcessed) {
            console.log('미처리 문서 처리 시작:', docId);
            
            // 처리 애니메이션 표시
            if (typeof window.showProcessingUI === 'function') {
                window.showProcessingUI();
            } else {
                mainContent.innerHTML = `
                    <div class="processing-container">
                        <div class="processing-animation">
                            <div class="brain-icon">
                                <span class="material-icons">psychology</span>
                            </div>
                            <div class="processing-glow"></div>
                        </div>
                        <p class="processing-text">문서를 처리하고 있습니다...</p>
                    </div>
                `;
            }
            
            // 처리 요청 API 호출 - 서버에서 자동으로 처리 시작
            console.log('미처리 문서의 처리된 내용 요청. 서버에서 자동으로 처리됨');
            
            // '/api/document/{docId}/processed' API는 미처리 문서인 경우 자동으로 처리를 시작함
            fetch(`/api/document/${docId}/processed`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('문서 처리 요청 실패');
                }
                return response.json();
            })
            .then(data => {
                console.log('문서 요청 결과:', data);
                
                if (data.success) {
                    // 처리가 완료된 경우 - 바로 표시
                    displayProcessedDocument(data);
                } else if (data.task_id) {
                    // 처리가 진행 중인 경우 - 상태 확인
                    if (typeof window.checkProcessingStatus === 'function') {
                        window.checkProcessingStatus(data.task_id, false, null);
                    } else {
                        // 5초 후 페이지 새로고침
                        setTimeout(() => {
                            window.location.reload();
                        }, 5000);
                    }
                } else {
                    // 오류 발생
                    mainContent.innerHTML = `<div class="error-message">문서 처리 시작 오류: ${data.error || '알 수 없는 오류'}</div>`;
                }
            })
            .catch(error => {
                console.error('문서 처리 요청 오류:', error);
                mainContent.innerHTML = `<div class="error-message">오류: ${error.message}</div>`;
            });
            
            return; // 미처리 문서인 경우 여기서 함수 종료
        }
        
        // 잘리된 문서 표시 함수
        function displayProcessedDocument(data) {
            console.log('처리된 문서 표시:', data);
            
            // 문서 제목 업데이트
            const docTitle = document.querySelector('.document-title');
            if (docTitle && data.title) {
                docTitle.textContent = data.title;
            }
            
            // 문서 내용 생성
            let htmlContent = '<div class="processed-document">';
            
            // 모델 정보 헤더
            htmlContent += `
                <div class="model-header">
                    <span class="model-badge">
                        <span class="material-icons">psychology</span>
                        <span>${data.parser || '업스테이지 PDF 파서'} + ${data.model_type?.toUpperCase() || 'OPENAI'}${data.model_name ? ' - ' + data.model_name : ''}</span>
                    </span>
                </div>
            `;
            
            // 요약 정보
            if (data.summary) {
                htmlContent += `
                    <div class="summary-section">
                        <h3>📝 요약</h3>
                        <div class="summary-content">${data.summary.replace(/\n/g, '<br>')}</div>
                    </div>
                `;
            }
            
            // 본문 내용
            htmlContent += `<div class="document-text">${data.content.replace(/\n/g, '<br>')}</div>`;
            
            // 이미지 갤러리
            if (data.images && data.images.length > 0) {
                htmlContent += '<div class="image-gallery">';
                data.images.forEach((img, index) => {
                    htmlContent += `
                        <div class="image-item">
                            <div class="image-container">
                                <img src="${img.path}" alt="Image ${index + 1}">
                            </div>
                            <div class="image-info">
                                <span class="image-title">Image ${index + 1}</span>
                                ${img.ocr_text ? `<div class="ocr-text">${img.ocr_text.replace(/\n/g, '<br>')}</div>` : ''}
                            </div>
                        </div>
                    `;
                });
                htmlContent += '</div>';
            }
            
            htmlContent += '</div>'; // processed-document 닫기
            
            // 모든 내용을 한 번에 DOM에 추가
            mainContent.innerHTML = htmlContent;
        }
        
        // 로딩 표시
        mainContent.innerHTML = '<div class="loading-indicator"><span class="material-icons spin">autorenew</span><span>문서를 로드하는 중...</span></div>';
        
        // 로딩 스타일 추가
        const style = document.createElement('style');
        style.textContent = `
            .loading-indicator {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%;
                padding: 2rem;
                color: #0066cc;
                text-align: center;
            }
            
            .loading-indicator .material-icons {
                font-size: 3rem;
                margin-bottom: 1rem;
                animation: spin 1.5s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
        
        // 처리된 문서 데이터 가져오기
        fetch(`/api/document/${docId}/processed`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('문서 데이터를 가져오는데 실패했습니다.');
                }
                return response.json();
            })
            .then(data => {
                console.log('문서 데이터 수신:', data);
                
                if (data.success && data.content) {
                    // 문서 제목 업데이트
                    const docTitle = document.querySelector('.document-title');
                    if (docTitle && data.title) {
                        docTitle.textContent = data.title;
                    }
                    
                    // 문서 내용 생성
                    let htmlContent = '<div class="processed-document">';
                    
                    // 모델 정보 헤더
                    htmlContent += `
                        <div class="model-header">
                            <span class="model-badge">
                                <span class="material-icons">psychology</span>
                                <span>${data.parser || '업스테이지 PDF 파서'} + ${data.model_type?.toUpperCase() || 'OPENAI'}${data.model_name ? ' - ' + data.model_name : ''}</span>
                            </span>
                        </div>
                    `;
                    
                    // 요약 정보
                    if (data.summary) {
                        htmlContent += `
                            <div class="summary-section">
                                <h3>📝 요약</h3>
                                <div class="summary-content">${data.summary.replace(/\n/g, '<br>')}</div>
                            </div>
                        `;
                    }
                    
                    // 본문 내용
                    htmlContent += `<div class="document-text">${data.content.replace(/\n/g, '<br>')}</div>`;
                    
                    // 이미지 갤러리
                    if (data.images && data.images.length > 0) {
                        htmlContent += '<div class="image-gallery">';
                        data.images.forEach((img, index) => {
                            htmlContent += `
                                <div class="image-item">
                                    <div class="image-container">
                                        <img src="${img.path}" alt="Image ${index + 1}">
                                    </div>
                                    <div class="image-info">
                                        <span class="image-title">Image ${index + 1}</span>
                                        ${img.ocr_text ? `<div class="ocr-text">${img.ocr_text.replace(/\n/g, '<br>')}</div>` : ''}
                                    </div>
                                </div>
                            `;
                        });
                        htmlContent += '</div>';
                    }
                    
                    htmlContent += '</div>'; // processed-document 닫기
                    
                    // 모든 내용을 한 번에 DOM에 추가
                    mainContent.innerHTML = htmlContent;
                } else {
                    mainContent.innerHTML = '<div class="error-message">문서 내용을 가져오지 못했습니다.</div>';
                }
            })
            .catch(error => {
                console.error('문서 로드 오류:', error);
                mainContent.innerHTML = `<div class="error-message">오류: ${error.message}</div>`;
            });
    }
    
    // 문서 클릭 핸들러 (이벤트 위임)
    function handleDocumentClick(event) {
        // 문서 항목 또는 하위 요소 찾기
        let target = event.target;
        let documentItem = null;
        
        // 클릭된 요소가 문서 항목이거나 그 하위 요소인지 확인
        while (target && target !== this) {
            if (target.classList.contains('document-item')) {
                documentItem = target;
                break;
            }
            target = target.parentElement;
        }
        
        // 문서 항목이 발견되면 처리
        if (documentItem) {
            const docId = documentItem.getAttribute('data-id');
            // 문서 처리 상태 확인 (체크박스 또는 상태 클래스로 확인)
            let isProcessed = false;
            
            // 1. 체크박스로 확인
            const checkbox = documentItem.querySelector('.doc-checkbox');
            if (checkbox) {
                isProcessed = checkbox.checked;
            }
            
            // 2. 상태 클래스로 확인 (체크박스가 없는 경우)
            if (!checkbox) {
                const statusElement = documentItem.querySelector('.doc-status');
                if (statusElement) {
                    isProcessed = statusElement.classList.contains('processed');
                }
            }
            
            console.log('문서 클릭됨:', docId, '처리 상태:', isProcessed ? '처리됨' : '미처리');
            
            // 선택 상태 변경
            const allItems = document.querySelectorAll('.document-item');
            allItems.forEach(i => i.classList.remove('selected'));
            documentItem.classList.add('selected');
            
            // 문서 내용 로드 (처리 상태 전달)
            loadDocument(docId, isProcessed);
        }
    }
    
    // 문서 목록에 대한 이벤트 리스너 설정
    function setupDocumentListeners() {
        // 문서 목록 컨테이너에 이벤트 위임 방식 적용
        const documentList = document.getElementById('document-list');
        if (!documentList) {
            console.error('문서 목록 요소를 찾을 수 없습니다');
            return;
        }
        
        console.log('문서 목록 컨테이너에 이벤트 설정');
        documentList.addEventListener('click', handleDocumentClick);
        
        // 현재 목록 로그 출력
        const items = documentList.querySelectorAll('.document-item');
        console.log(`현재 문서 목록에 ${items.length}개 항목이 있습니다`);
        items.forEach((item, i) => {
            console.log(`- 문서 ${i+1}: ID=${item.getAttribute('data-id')}, 제목=${item.querySelector('.doc-title')?.textContent}`);
        });
    }
    
    // URL에서 문서 ID 확인하기
    function checkInitialUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        const docId = urlParams.get('doc_id');
        if (docId) {
            console.log('URL에서 문서 ID 발견:', docId);
            const docItem = document.querySelector(`.document-item[data-id="${docId}"]`);
            if (docItem) {
                docItem.click();
            }
        }
    }
    
    // 새로고침 버튼 이벤트 설정
    function setupInitializeButton() {
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', function() {
                window.location.reload();
            });
        }
    }
    
    // 문서 추가 버튼 이벤트 설정
    function setupAddDocumentButton() {
        console.log('문서 추가 버튼 이벤트 설정');
        
        // 문서 추가 버튼
        const addBtn = document.getElementById('add-doc-btn');
        if (addBtn) {
            console.log('문서 추가 버튼 발견');
            
            addBtn.addEventListener('click', function() {
                console.log('문서 추가 버튼 클릭됨');
                
                // 파일 선택 대화상자 열기
                const fileInput = document.getElementById('file-upload');
                if (fileInput) {
                    fileInput.click();
                } else {
                    // 파일 입력 요소가 없는 경우 생성
                    const input = document.createElement('input');
                    input.type = 'file';
                    input.id = 'file-upload';
                    input.accept = '.pdf,.txt';
                    input.style.display = 'none';
                    
                    // 파일 선택 이벤트 처리
                    input.addEventListener('change', function() {
                        if (this.files && this.files.length > 0) {
                            handleFileUpload(this.files[0]);
                        }
                    });
                    
                    document.body.appendChild(input);
                    input.click();
                }
            });
        } else {
            console.error('문서 추가 버튼(.add-button)을 찾을 수 없습니다');
        }
    }
    
    // 파일 업로드 처리
    function handleFileUpload(file) {
        console.log('파일 업로드:', file.name);
        
        // FormData 생성
        const formData = new FormData();
        formData.append('file', file);
        
        // 업로드 상태 표시
        const statusElement = document.querySelector('.upload-status') || document.querySelector('.status-message');
        if (statusElement) {
            statusElement.textContent = `파일 업로드 중: ${file.name}`;
            statusElement.style.display = 'block';
        }
        
        // 파일 업로드 API 호출
        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('업로드 결과:', data);
            
            if (data.success) {
                if (statusElement) {
                    statusElement.textContent = `파일 업로드 성공: ${file.name}`;
                    statusElement.style.color = '#4CAF50';
                    
                    // 3초 후 상태 메시지 숨기기
                    setTimeout(() => {
                        statusElement.style.display = 'none';
                    }, 3000);
                }
                
                // 페이지 새로고침 (문서 목록 업데이트)
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            } else {
                if (statusElement) {
                    statusElement.textContent = `업로드 오류: ${data.message || '알 수 없는 오류'}`;
                    statusElement.style.color = '#F44336';
                }
            }
        })
        .catch(error => {
            console.error('업로드 오류:', error);
            
            if (statusElement) {
                statusElement.textContent = `업로드 오류: ${error.message}`;
                statusElement.style.color = '#F44336';
            }
        });
    }
    
    // 초기화 함수 호출 - 모든 기능을 설정합니다
    setupDocumentListeners();
    setupInitializeButton();
    setupAddDocumentButton();
    checkInitialUrl();
    
    // MutationObserver를 사용하여 DOM 변경 감지 후 리스너 재설정
    const documentList = document.getElementById('document-list');
    if (documentList) {
        const observer = new MutationObserver(function(mutations) {
            setupDocumentListeners();
        });
        
        observer.observe(documentList, { 
            childList: true,
            subtree: true 
        });
    }
});
