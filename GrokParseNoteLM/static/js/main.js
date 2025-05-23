// GrokParseNoteLM 웹 인터페이스 JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - GrokParseNoteLM JS initialized');
    console.log('DEBUG: Starting initialization sequence');
    
    // URL 매개변수 확인
    const urlParams = new URLSearchParams(window.location.search);
    const loadDocs = urlParams.get('load_docs');
    const lastDocId = sessionStorage.getItem('lastDocId');
    
    // 문서 목록 표시 여부 확인
    if (loadDocs === 'true') {
        console.log('Loading documents view');
        // URL에 load_docs=true가 있으면 문서 목록을 표시하고 처리된 문서 표시
        if (lastDocId) {
            console.log('Loading last document:', lastDocId);
            // 저장된 문서 ID가 있으면 해당 문서 표시
            setTimeout(() => {
                const docItem = document.querySelector(`.document-item[data-id="${lastDocId}"]`);
                if (docItem) {
                    docItem.click();
                }
            }, 500);
        }
    } else {
        // 그렇지 않으면 초기화 화면 표시
        initializeInterface();
    }
    
    // 파일 업로드 관련 코드는 file-upload.js로 이동했습니다.
    
    // 파일 업로드 이벤트 리스너 (업로드 성공 후 처리)
    document.addEventListener('fileUploaded', function(e) {
        const data = e.detail;
        
        if (data.success) {
            // 알림 팝업 제거하고 풋터에 상태 표시
            const statusMessage = document.querySelector('.status-message');
            if (statusMessage) {
                statusMessage.textContent = '파일이 성공적으로 업로드되었습니다.';
                statusMessage.style.display = 'block';
                statusMessage.style.color = '#4CAF50';
                
                // 3초 후 상태 메시지 숨기기
                setTimeout(() => {
                    statusMessage.style.display = 'none';
                }, 3000);
            }
            
            if (data.file_info) {
                // 새로운 문서 추가
                addDocumentToList(data.file_info);
                
                // 처리 완료 메시지 표시
                if (data.auto_processed) {
                    showToast('문서가 업로드되었으며 자동으로 처리되었습니다.');
                } else {
                    showToast('문서 업로드 완료');
                }
            }
            
            // 처리 작업 ID가 있으면 상태 확인 시작
            if (data.task_id) {
                showUploadStatus('문서 처리 중... 잠시만 기다려주세요.', 'info');
                // 처리 완료 후 로드 될 URL 저장
                const redirectUrl = data.redirect_url || '/?load_docs=true';
                checkProcessingStatus(data.task_id, false, redirectUrl);
            }
        } else {
            showToast('업로드 실패: ' + (data.message || '오류가 발생했습니다.'));
        }
    });
    
    // 토스트 메시지 표시 함수
    function showToast(message, duration = 3000) {
        // 기존 토스트 제거
        const existingToast = document.querySelector('.toast-message');
        if (existingToast) {
            existingToast.remove();
        }
        
        const toast = document.createElement('div');
        toast.className = 'toast-message';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        // 토스트 표시
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        // 지정된 시간 후 토스트 제거
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, duration);
    }
    
    // 업로드 상태 표시 함수
    function showUploadStatus(message, status = 'info') {
        const uploadStatus = document.getElementById('upload-status');
        if (uploadStatus) {
            uploadStatus.textContent = message;
            uploadStatus.className = `upload-status ${status}`;
        }
    }
    
    // 문서 삭제 버튼 이벤트 핸들러
    const deleteButtons = document.querySelectorAll('.delete-btn');
    if (deleteButtons.length > 0) {
        deleteButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation(); // 문서 항목 클릭 이벤트 전파 방지
                
                const docId = this.getAttribute('data-id');
                const docName = this.getAttribute('data-name');
                
                if (confirm(`"${docName}" 문서를 삭제하시겠습니까?`)) {
                    fetch(`/api/document/${docId}`, {
                        method: 'DELETE'
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('문서가 삭제되었습니다.');
                            window.location.reload();
                        } else {
                            alert(`삭제 실패: ${data.error || '알 수 없는 오류'}`);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('문서 삭제 중 오류가 발생했습니다.');
                    });
                }
            });
        });
    }
    
    // 문서 항목 클릭 이벤트 (문서 선택 및 내용 표시)
    const documentItems = document.querySelectorAll('.document-item');
    if (documentItems.length > 0) {
        documentItems.forEach(item => {
            item.addEventListener('click', function() {
                // 선택 상태 토글
                documentItems.forEach(i => i.classList.remove('selected'));
                this.classList.add('selected');
                
                const docId = this.getAttribute('data-id');
                
                // 처리된 문서 내용 로드 (OpenAI 분석 결과)
                loadProcessedDocument(docId);
            });
        });
    }
    
    // 인터페이스 초기화 함수
    function initializeInterface() {
        // 가운데 패널 초기화
        const mainContent = document.querySelector('.document-content');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="welcome-screen">
                    <div class="welcome-icon">
                        <span class="material-icons">psychology</span>
                    </div>
                    <h2>GrokParseNoteLM에 오신 것을 환영합니다</h2>
                    <p>PDF와 텍스트 문서를 업로드하고 OpenAI GPT-4로 분석해보세요.</p>
                    <p>왼쪽 사이드바의 + 버튼을 클릭하여 시작하세요.</p>
                </div>
            `;

            // 환영 화면 스타일 추가
            const style = document.createElement('style');
            style.textContent = `
                .welcome-screen {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                    padding: 2rem;
                    text-align: center;
                    animation: fadeIn 0.8s ease-in-out;
                }
                
                .welcome-icon {
                    font-size: 3rem;
                    margin-bottom: 1.5rem;
                    color: #0066cc;
                    animation: pulse 2s infinite;
                }
                
                .welcome-icon .material-icons {
                    font-size: 4rem;
                }
                
                @keyframes pulse {
                    0% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.1); opacity: 0.8; }
                    100% { transform: scale(1); opacity: 1; }
                }
                
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    // OpenAI 모델로 처리된 문서 내용 로드
    function loadProcessedDocument(docId) {
        // 중앙 패널에 로딩 상태 표시
        const mainContent = document.querySelector('.document-content');
        if (mainContent) {
            mainContent.innerHTML = '<div class="loading-indicator"><span class="material-icons spin">autorenew</span><span>OpenAI GPT-4 모델을 통해 문서를 처리하는 중...</span></div>';
            
            // 로딩 애니메이션 스타일 추가
            const style = document.createElement('style');
            style.textContent = `
                .loading-indicator {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                    color: #0066cc;
                    font-size: 1.2rem;
                    text-align: center;
                    animation: fadeIn 0.5s ease-in-out;
                }
                
                .loading-indicator .material-icons {
                    font-size: 2.5rem;
                    margin-bottom: 1rem;
                }
                
                .spin {
                    animation: spin 1.5s linear infinite;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }
        
        // 문서 데이터 요청
        fetch(`/api/document/${docId}/processed`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load processed document');
                }
                return response.json();
            })
            .then(data => {
                console.log("Processed document data:", data);
                
                if (data.success && data.content) {
                    // 문서 제목 업데이트
                    const docTitle = document.querySelector('.document-title');
                    if (docTitle && data.title) {
                        docTitle.textContent = data.title;
                    }
                    
                    // 마크다운 변환 및 내용 표시
                    if (mainContent) {
                        // 요약 및 분석 결과 표시
                        let htmlContent = '<div class="processed-document">';
                        
                        // 파서와 모델 정보를 포함한 헤더 추가
                        const parserName = data.parser || '업스테이지 PDF 파서';
                        const modelType = data.model_type?.toUpperCase() || 'OPENAI';
                        const modelName = data.model_name ? ` - ${data.model_name}` : '';
                        
                        htmlContent += `
                            <div class="ai-analysis-header">
                                <div class="ai-badge">
                                    <span class="material-icons">psychology</span>
                                    <span>${parserName} + ${modelType}${modelName}</span>
                                </div>
                                <div class="analysis-timestamp">처리 시간: ${new Date().toLocaleString()}</div>
                            </div>`;
                        
                        // 요약 섹션 추가
                        if (data.summary) {
                            htmlContent += `
                                <div class="document-section">
                                    <h3>핵심 요약</h3>
                                    <div class="summary-content">${data.summary.replace(/\n/g, '<br>')}</div>
                                </div>`;
                        }
                        
                        // 문서 내용 추가
                        if (data.content) {
                            htmlContent += `
                                <div class="document-section">
                                    <h3>문서 내용</h3>
                                    <div class="content-text">${data.content.replace(/\n/g, '<br>')}</div>
                                </div>`;
                        }
                        
                        // 이미지 분석 결과 추가
                        if (data.images && data.images.length > 0) {
                            htmlContent += `
                                <div class="document-section">
                                    <h3>이미지 분석 (총 ${data.images.length}개)</h3>
                                    <div class="image-gallery">`;
                            
                            data.images.forEach((image, index) => {
                                htmlContent += `
                                    <div class="image-item">
                                        <div class="image-container">
                                            <img src="/images/${image.filename}" alt="추출 이미지 ${index + 1}">
                                        </div>
                                        <div class="image-info">
                                            <span class="image-number">Image ${index + 1}</span>
                                            ${image.ocr_text ? `<div class="ocr-text">${image.ocr_text.replace(/\n/g, '<br>')}</div>` : ''}
                                        </div>
                                    </div>`;
                            });
                            
                            htmlContent += `</div></div>`;
                        }
                        
                        htmlContent += '</div>';
                        mainContent.innerHTML = htmlContent;
                        
                        // GPT-4 분석 헤더에 대한 스타일 추가
                        const style = document.createElement('style');
                        style.textContent = `
                            .ai-analysis-header {
                                display: flex;
                                justify-content: space-between;
                                align-items: center;
                                padding: 10px 15px;
                                background-color: #f0f7ff;
                                border-radius: 8px;
                                margin-bottom: 20px;
                                border-left: 4px solid #0066cc;
                            }
                            
                            .ai-badge {
                                display: flex;
                                align-items: center;
                                color: #0066cc;
                                font-weight: bold;
                            }
                            
                            .ai-badge .material-icons {
                                margin-right: 8px;
                            }
                            
                            .analysis-timestamp {
                                color: #666;
                                font-size: 0.85em;
                            }
                        `;
                        document.head.appendChild(style);
                    }
                } else {
                    console.log("Falling back to basic document view");
                    // 처리된 결과가 없는 경우 기본 문서 내용 표시
                    fetch(`/view/${docId}`)
                        .then(response => response.text())
                        .then(html => {
                            const parser = new DOMParser();
                            const doc = parser.parseFromString(html, 'text/html');
                            const content = doc.querySelector('.document-content');
                            
                            if (content && mainContent) {
                                mainContent.innerHTML = content.innerHTML;
                            }
                        })
                        .catch(error => {
                            console.error('Error loading document:', error);
                            if (mainContent) {
                                mainContent.innerHTML = '<div class="error-message">문서 내용을 불러오는 중 오류가 발생했습니다.</div>';
                            }
                        });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (mainContent) {
                    mainContent.innerHTML = '<div class="error-message">처리된 문서를 불러오는 중 오류가 발생했습니다.</div>';
                }
            });
    }
    
    // 처리 작업 상태 확인
    function checkProcessingStatus(taskId, shouldReload = false, redirectUrl = null) {
        let checkCount = 0;
        const maxChecks = 60; // 최대 확인 횟수 (60회 = 약 3분)
        
        // 처리 중 UI 표시 (processing.js의 함수 사용)
        if (!shouldReload && typeof window.showProcessingUI === 'function') {
            window.showProcessingUI();
        }
        
        function checkStatus() {
            fetch(`/api/task/${taskId}`)
                .then(response => response.json())
                .then(data => {
                    checkCount++;
                    console.log(`Task status check ${checkCount}:`, data);
                    
                    // 진행률 계산 (checkCount를 이용한 임의 값)
                    let percentage = Math.min(Math.round((checkCount / maxChecks) * 100), 95);
                    
                    // 단계 설정 (임의로 설정, 실제로는 서버에서 상태를 받는 것이 좋음)
                    let step = 'extract';
                    if (checkCount > 3) step = 'images';
                    if (checkCount > 6) step = 'analyze';
                    
                    // UI 업데이트 (processing.js의 함수 사용)
                    if (typeof window.updateProcessingStep === 'function') {
                        window.updateProcessingStep(step, percentage);
                    }
                    
                    if (data.status === 'completed') {
                        // 처리 완료 시 문서 내용 가져오기
                        if (typeof window.updateProcessingStep === 'function') {
                            window.updateProcessingStep('complete', 100);
                        }
                        
                        // 지연 후 결과 표시 (애니메이션 효과를 위해)
                        setTimeout(() => {
                            const docId = data.doc_id;
                            if (docId) {
                                // 완료 후 문서 목록이 포함된 페이지로 이동
                                if (redirectUrl) {
                                    console.log('Redirecting to:', redirectUrl);
                                    // 문서 정보 저장
                                    sessionStorage.setItem('lastDocId', docId);
                                    window.location.href = redirectUrl;
                                    return; // 이후 코드 실행 방지
                                }
                                
                                // 리다이렉트가 없을 경우 기존 방식으로 처리
                                // 문서 내용 로드
                                loadProcessedDocument(docId);
                                
                                // 문서 선택 상태 업데이트
                                const documentItems = document.querySelectorAll('.document-item');
                                documentItems.forEach(item => {
                                    item.classList.remove('selected');
                                    if (item.getAttribute('data-id') === docId) {
                                        item.classList.add('selected');
                                    }
                                });
                                
                                // 상태 메시지 표시
                                const statusDiv = document.querySelector('.footer-status');
                                if (statusDiv) {
                                    statusDiv.textContent = 'OpenAI GPT-4 모델을 통해 문서가 성공적으로 처리되었습니다.';
                                    statusDiv.className = 'footer-status success';
                                    
                                    // 3초 후 상태 메시지 초기화
                                    setTimeout(() => {
                                        statusDiv.textContent = 'NotebookLM과 유사하게 구현된 웹 UI가 제공됩니다.';
                                        statusDiv.className = 'footer-status';
                                    }, 3000);
                                }
                            } else {
                                // 문서 ID가 없는 경우
                                if (redirectUrl) {
                                    window.location.href = redirectUrl;
                                } else {
                                    window.location.reload();
                                }
                            }
                        }, 1500);
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
