// 간단하고 직접적인 문서 선택 이벤트 처리
document.addEventListener('DOMContentLoaded', function() {
    console.log('간단한 문서 선택 스크립트가 로드되었습니다.');
    
    // 문서 클릭 이벤트 리스너 설정
    function setupDocumentListeners() {
        console.log('문서 클릭 이벤트 리스너 설정');
        
        // 문서 리스트 확인
        const documentList = document.getElementById('document-list');
        console.log('문서 목록 요소 찾기:', documentList);
        
        // 문서 리스트 내부 구조 확인
        if (documentList) {
            console.log('문서 리스트 HTML:', documentList.innerHTML);
            
            // 문서 리스트의 직접적인 자식 요소 확인
            const children = documentList.children;
            console.log('문서 리스트 자식 요소 개수:', children.length);
            
            // 각 자식 요소 확인
            for (let i = 0; i < children.length; i++) {
                console.log(`자식 ${i}:`, children[i]);
                console.log(`자식 ${i} 태그:`, children[i].tagName);
                console.log(`자식 ${i} 클래스:`, children[i].className);
                console.log(`자식 ${i} ID:`, children[i].getAttribute('data-id'));
            }
            
            // 요소 찾기 시도
            const allChildrenWithDataId = documentList.querySelectorAll('[data-id]');
            console.log('data-id 속성을 가진 모든 요소:', allChildrenWithDataId.length, '개');
        }
        
        // 모든 사용 가능한 선택자로 문서 항목 검색 시도
        const documentItemsAll = [
            document.querySelectorAll('.document-item'),  // 기본 선택자
            document.querySelectorAll('.doc-item'),      // 대체 선택자 1
            document.querySelectorAll('.sidebar-item'),  // 대체 선택자 2
            document.querySelectorAll('li[data-id]')     // ID를 가진 모든 li 요소
        ];
        
        // 각 선택자별 결과 출력
        documentItemsAll.forEach((items, index) => {
            console.log(`선택자 ${index} 결과:`, items.length, '개 항목');
        });
        
        // 실제 사용할 문서 항목 선택 (첫번째 비어있지 않은 선택자 사용)
        const documentItems = documentItemsAll.find(items => items.length > 0) || document.querySelectorAll('.document-item');
        
        // 이벤트 리스너 추가
        documentItems.forEach(item => {
            // 기존 리스너 제거 후 다시 추가 (중복 방지)
            item.removeEventListener('click', handleDocumentClick);
            item.addEventListener('click', handleDocumentClick);
            
            // 요소 클릭 가능하게 스타일 추가
            item.style.cursor = 'pointer';
            
            // 클릭 가능함을 표시하기 위한 클래스 추가
            item.classList.add('clickable');
            
            // HTML에 직접 이벤트 추가 (대체 방식)
            item.setAttribute('onclick', 'console.log("\ubb38\uc11c \uc694\uc18c \ud074\ub9ad\ub428 (HTML \uc18d\uc131)");');
        });
        
        // 화면에 있는 문서 항목 수 출력
        console.log('현재 문서 목록에 있는 문서 개수:', documentItems.length);
        
        // 어떤 선택자를 사용해도 작동하지 않을 수 있으므로, 이벤트 위임 방식으로 변경
        console.log('문서 목록에 직접 이벤트 위임 방식 사용');
        
        // 문서 목록이 있으면 이벤트 위임 방식 사용
        if (documentList) {
            // 기존 이벤트 제거 후 다시 연결
            documentList.removeEventListener('click', delegateDocumentClick);
            documentList.addEventListener('click', delegateDocumentClick);
            
            console.log('문서 목록에 이벤트 위임 설정 완료');
        } else {
            console.error('문서 목록 요소를 찾을 수 없습니다!');
        }
    }
    
    // 이벤트 위임을 위한 이벤트 핸들러
    function delegateDocumentClick(event) {
        console.log('문서 목록 영역에서 클릭 발생:', event.target);
        // 이벤트 시작을 알리는 메시지를 사용자에게 표시
        alert('문서 항목 클릭됨!');
        
        // 클릭된 요소나 부모 요소에서 data-id 찾기
        let target = event.target;
        let docId = null;
        
        // 클릭된 요소에서 부모로 올라가며 data-id 검색
        while (target && target !== document && !docId) {
            docId = target.getAttribute('data-id');
            if (docId) {
                console.log('문서 ID 발견:', docId, '요소:', target);
                break;
            }
            target = target.parentElement;
        }
        
        if (docId) {
            // 요소 선택 표시
            const allItems = document.querySelectorAll('[data-id]');
            allItems.forEach(item => item.classList.remove('selected'));
            target.classList.add('selected');
            
            // URL 업데이트
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.set('doc_id', docId);
            window.history.pushState({docId: docId}, '', newUrl.toString());
            
            // 문서 처리 상태 확인
            let isProcessed = target.classList.contains('processed');
            if (!isProcessed) {
                const statusElement = target.querySelector('.doc-status');
                if (statusElement) {
                    isProcessed = statusElement.classList.contains('processed');
                }
            }
            
            console.log('문서 로드 시작 (위임 방식):', docId, '처리 상태:', isProcessed);
            
            // 문서 로드 함수 호출
            loadDocument(docId, isProcessed);
        }
    }
    
    // 문서 클릭 핸들러
    function handleDocumentClick(event) {
        console.log('클릭 이벤트 발생:', event.type);
        console.log('클릭된 요소:', event.target);
        
        // 단순 클릭 이벤트만 처리
        if (event.detail > 1) {
            console.log('더블클릭 무시');
            return; // 더블클릭 무시
        }
        
        // 클릭된 요소 확인
        const target = event.target.closest('.document-item');
        console.log('문서 항목 검색 결과:', target);
        
        if (!target) {
            console.log('문서 항목이 아닙니다. 무시합니다.');
            return; // 문서 항목이 아니면 무시
        }
        
        const docId = target.getAttribute('data-id');
        // 문서 처리 상태 확인 (체크박스 또는 상태 클래스로 확인)
        let isProcessed = false;
        
        // 1. 체크박스로 확인
        const checkbox = target.querySelector('.doc-checkbox');
        if (checkbox) {
            isProcessed = checkbox.checked;
        }
        
        // 2. 상태 클래스로 확인 (체크박스가 없는 경우)
        if (!checkbox) {
            const statusElement = target.querySelector('.doc-status');
            if (statusElement) {
                isProcessed = statusElement.classList.contains('processed');
            } else {
                // 클래스로 직접 확인
                isProcessed = target.classList.contains('processed');
            }
        }
        
        console.log('문서 클릭됨:', docId, '처리 상태:', isProcessed ? '처리됨' : '미처리');
        
        // 선택 상태 변경
        const allItems = document.querySelectorAll('.document-item');
        allItems.forEach(i => i.classList.remove('selected'));
        target.classList.add('selected');
        
        // URL 업데이트 (히스토리 상태 변경)
        const newUrl = new URL(window.location.href);
        newUrl.searchParams.set('doc_id', docId);
        window.history.pushState({docId: docId}, '', newUrl.toString());
        
        // 문서 내용 로드
        loadDocument(docId, isProcessed);
    }
    
    // 문서 내용 로드 함수
    function loadDocument(docId, isProcessed) {
        console.log('문서 로드 시작:', docId, '처리 상태:', isProcessed ? '처리됨' : '미처리');
        console.log('실제 로드될 URL:', `/api/document/${docId}/processed`);
        
        // 문서 내용 영역
        const mainContent = document.querySelector('.document-content');
        if (!mainContent) {
            console.error('문서 내용을 표시할 영역을 찾을 수 없습니다.');
            return;
        }
        
        console.log('로딩 상태 표시 준비');
        mainContent.innerHTML = '<div class="loading">\ubb38\uc11c \ub0b4\uc6a9\uc744 \ubd88\ub7ec\uc624\ub294 \uc911...</div>';
        
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
                
                // 애니메이션 스타일 추가
                const style = document.createElement('style');
                style.textContent = `
                    .processing-container {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        height: 100%;
                        padding: 2rem;
                    }
                    
                    .processing-animation {
                        position: relative;
                        margin-bottom: 2rem;
                    }
                    
                    .brain-icon {
                        position: relative;
                        z-index: 2;
                        animation: pulse 2s infinite;
                    }
                    
                    .brain-icon .material-icons {
                        font-size: 4rem;
                        color: #0066cc;
                    }
                    
                    .processing-glow {
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        width: 80px;
                        height: 80px;
                        background: rgba(0, 102, 204, 0.2);
                        border-radius: 50%;
                        z-index: 1;
                        animation: glow 2s infinite;
                    }
                    
                    .processing-text {
                        font-size: 1.2rem;
                        color: #0066cc;
                        margin-top: 1rem;
                        animation: fadeInOut 2s infinite;
                    }
                    
                    @keyframes pulse {
                        0% { transform: scale(1); }
                        50% { transform: scale(1.1); }
                        100% { transform: scale(1); }
                    }
                    
                    @keyframes glow {
                        0% { opacity: 0.5; width: 80px; height: 80px; }
                        50% { opacity: 0.8; width: 100px; height: 100px; }
                        100% { opacity: 0.5; width: 80px; height: 80px; }
                    }
                    
                    @keyframes fadeInOut {
                        0% { opacity: 0.7; }
                        50% { opacity: 1; }
                        100% { opacity: 0.7; }
                    }
                `;
                document.head.appendChild(style);
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
                    mainContent.innerHTML = `<div class="error-message">문서 처리 중 오류가 발생했습니다.</div>`;
                }
            })
            .catch(error => {
                console.error('문서 처리 요청 오류:', error);
                mainContent.innerHTML = `<div class="error-message">오류: ${error.message}</div>`;
            });
        } else {
            // 이미 처리된 문서 - 처리된 내용 로드
            console.log('이미 처리된 문서의 내용 로드:', docId);
            
            // 로딩 표시
            mainContent.innerHTML = '<div class="loading">문서 내용을 불러오는 중...</div>';
            
            // 처리된 문서 내용 요청
            fetch(`/api/document/${docId}/processed`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('처리된 문서 내용 로드 실패');
                }
                return response.json();
            })
            .then(data => {
                console.log('처리된 문서 내용 로드 성공');
                displayProcessedDocument(data);
            })
            .catch(error => {
                console.error('문서 로드 오류:', error);
                mainContent.innerHTML = `<div class="error-message">오류: ${error.message}</div>`;
            });
        }
    }
    
    // 처리된 문서 표시 함수
    function displayProcessedDocument(data) {
        console.log('처리된 문서 표시 시작');
        console.log('문서 데이터 전체:', data);
        
        // 데이터 추출을 위한 변수 선언
        let contentToDisplay = '';
        let summaryContent = '';
        let titleContent = '';
        let imagesContent = [];
        
        // 처리된 데이터의 다양한 구조 처리
        if (data && data.data) {
            if (data.data.content) contentToDisplay = data.data.content;
            if (data.data.summary) summaryContent = data.data.summary;
            if (data.data.title) titleContent = data.data.title;
            if (data.data.images) imagesContent = data.data.images;
        }
        
        // 첫 번째 계층에서 가져오기 시도
        if (!contentToDisplay && data.content) contentToDisplay = data.content;
        if (!summaryContent && data.summary) summaryContent = data.summary;
        if (!titleContent && data.title) titleContent = data.title;
        if (imagesContent.length === 0 && data.images) imagesContent = data.images;
        
        // 방법 3: 처리 결과에서 문서 내용 찾기
        if (!contentToDisplay && typeof data.processed_content === 'string') {
            console.log('처리된 컨텐츠 발견:', data.processed_content.substring(0, 100) + '...');
            contentToDisplay = data.processed_content;
        }
        
        // 문서 내용이 없으면 전체 데이터 표시
        if (!contentToDisplay && typeof data === 'object') {
            contentToDisplay = JSON.stringify(data, null, 2);
        }
        
        // 데이터 로깅
        console.log('표시할 문서 내용:', { 
            content: contentToDisplay, 
            summary: summaryContent,
            title: titleContent,
            images: imagesContent
        });
        
        // 새로 추가한 문서 표시 영역 사용
        const displayContainer = document.getElementById('document-display-container');
        const titleElement = document.getElementById('document-title');
        const summaryElement = document.getElementById('document-summary');
        const contentElement = document.getElementById('document-content');
        
        if (displayContainer && titleElement && summaryElement && contentElement) {
            // 제목 설정
            titleElement.textContent = titleContent || 'PDF 문서';
            
            // 요약 설정
            if (summaryContent) {
                summaryElement.innerHTML = `<h3>요약</h3><p>${summaryContent}</p>`;
                summaryElement.style.display = 'block';
            } else {
                summaryElement.style.display = 'none';
            }
            
            // 내용 설정
            contentElement.innerHTML = `<h3>내용</h3><div class="content-text">${contentToDisplay}</div>`;
            
            // 이미지 처리
            if (imagesContent && imagesContent.length > 0) {
                let imagesHtml = '<div class="document-images"><h3>이미지</h3><div class="images-container">';
                imagesContent.forEach(img => {
                    imagesHtml += `<img src="${img}" alt="문서 이미지" class="document-image">`;
                });
                imagesHtml += '</div></div>';
                contentElement.innerHTML += imagesHtml;
            }
            
            // 표시영역 보이기
            displayContainer.style.display = 'block';
            
            console.log('문서 표시 완료');
        } else {
            console.error('문서 표시 영역을 찾을 수 없습니다');
        }
        
        // JSON 문자열인 경우 파싱 시도 (이미 위에서 처리했으므로 삭제)
    }
    
    // 내용이 없는 경우 처리
    if (  !data.content && !data.summary) {
        console.error('문서 내용이 없습니다');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="empty-content">
                    <p>문서 내용이 없습니다.</p>
                    <p>문서가 아직 처리 중이거나 오류가 발생했을 수 있습니다.</p>
                </div>
            `;
            docTitle.textContent = data.title;
        }
        
        // 문서 내용 영역
        const mainContent = document.querySelector('.document-content');
        if (!mainContent) {
            console.error('문서 내용을 표시할 영역을 찾을 수 없습니다.');
            return;
        }
        
        // 문서 내용 표시
        let htmlContent = '<div class="processed-document">';
        
        // 요약 섹션 (있는 경우)
        if (data.summary) {
            htmlContent += `
                <div class="summary-section">
                    <h3>요약</h3>
                    <div class="summary-content">${data.summary}</div>
                </div>
            `;
        }
        
        // 내용 섹션
        if (data.content) {
            // 마크다운 지원 확인
            if (typeof marked === 'function') {
                htmlContent += `
                    <div class="content-section">
                        <h3>내용</h3>
                        <div class="content-text">${marked(data.content)}</div>
                    </div>
                `;
            } else {
                // 일반 텍스트로 표시
                htmlContent += `
                    <div class="content-section">
                        <h3>내용</h3>
                        <div class="content-text">${data.content.replace(/\n/g, '<br>')}</div>
                    </div>
                `;
            }
        }
        
        // 이미지 섹션 (있는 경우)
        if (data.images && data.images.length > 0) {
            htmlContent += '<div class="image-section"><h3>이미지</h3><div class="image-gallery">';
            
            data.images.forEach(image => {
                if (typeof image === 'string') {
                    // 이미지 URL 문자열인 경우
                    htmlContent += `<div class="image-item"><img src="${image}" alt="문서 이미지"></div>`;
                } else if (typeof image === 'object' && image.url) {
                    // 이미지 객체인 경우
                    htmlContent += `
                        <div class="image-item">
                            <img src="${image.url}" alt="${image.alt || '문서 이미지'}">
                            ${image.caption ? `<div class="image-caption">${image.caption}</div>` : ''}
                        </div>
                    `;
                }
            });
            
            htmlContent += '</div></div>';
        }
        
        // 컨테이너 닫기
        htmlContent += '</div>';
        
        // 스타일 추가
        const style = document.createElement('style');
        style.textContent = `
            .processed-document {
                padding: 20px;
                max-width: 900px;
                margin: 0 auto;
                font-family: Arial, sans-serif;
                line-height: 1.6;
            }
            
            .processed-document h3 {
                color: #333;
                border-bottom: 1px solid #eee;
                padding-bottom: 8px;
                margin-bottom: 15px;
            }
            
            .summary-section {
                background-color: #f9f9f9;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                border-left: 4px solid #4caf50;
            }
            
            .summary-content {
                line-height: 1.6;
            }
            
            .content-text {
                line-height: 1.6;
                white-space: pre-line;
            }
            
            .image-gallery {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            
            .image-item {
                border: 1px solid #eee;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .image-item img {
                width: 100%;
                height: auto;
                display: block;
            }
            
            .image-caption {
                padding: 10px;
                background: #f5f5f5;
                font-size: 0.9rem;
                color: #555;
            }
        `;
        document.head.appendChild(style);
        
        // 내용 설정
        mainContent.innerHTML = htmlContent;
        
        // 상태 업데이트 (필요한 경우)
        updateDocumentStatus(data.document_id || data.id);
    }
    
    // 문서 상태 업데이트 함수
    function updateDocumentStatus(docId) {
        if (!docId) return;
        
        // 해당 문서 항목 찾기
        const docItem = document.querySelector(`.document-item[data-id="${docId}"]`);
        if (!docItem) return;
        
        // 체크박스 또는 상태 요소 업데이트
        const checkbox = docItem.querySelector('.doc-checkbox');
        if (checkbox) {
            checkbox.checked = true;
        }
        
        const statusElement = docItem.querySelector('.doc-status');
        if (statusElement) {
            statusElement.classList.add('processed');
            statusElement.innerHTML = '<span class="material-icons">check_circle</span>';
        }
        
        // 문서 항목 클래스 업데이트
        docItem.classList.add('processed');
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
