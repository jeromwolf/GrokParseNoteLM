// 문서 내용 직접 표시 스크립트
document.addEventListener('DOMContentLoaded', function() {
    console.log('문서 뷰어 스크립트 로드됨');
    
    // 알림 표시 함수 정의
    window.showNotification = function(message, type) {
        console.log('알림 표시:', message, type);
        
        // 기존 알림 삭제
        const existingNotifications = document.querySelectorAll('.processing-notification');
        existingNotifications.forEach(notification => document.body.removeChild(notification));
        
        // 새 알림 생성
        const notification = document.createElement('div');
        notification.className = 'processing-notification';
        notification.textContent = message;
        
        // 알림 유형에 따른 스타일 적용
        const bgColor = type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196F3';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${bgColor};
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            font-weight: bold;
        `;
        
        // 화면에 알림 추가
        document.body.appendChild(notification);
        
        // 3초 후 알림 삭제
        setTimeout(function() {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 3000);
    };
    
    // 전역 함수로 문서 클릭 핸들러 등록
    window.viewDocument = function(docId) {
        console.log('문서 보기 함수 호출됨:', docId);
        
        // 문서 내용 영역 찾기 (확인된 HTML 구조에 맞게 수정)
        let contentArea = document.querySelector('.document-content');
        
        console.log('화면 요소 확인 - .document-content:', contentArea ? '존재함' : '없음');
        
        // 요소를 찾을 수 없는 경우, 새로 생성
        if (!contentArea) {
            console.log('문서 내용 영역을 찾을 수 없어 생성합니다');
            
            // 주요 요소 찾기
            const mainContent = document.querySelector('.main-content');
            
            if (mainContent) {
                // 기존 contentArea가 있다면 제거
                const oldContentArea = mainContent.querySelector('.document-content');
                if (oldContentArea) {
                    mainContent.removeChild(oldContentArea);
                }
                
                // 새 콘텐츠 영역 생성
                contentArea = document.createElement('div');
                contentArea.className = 'document-content';
                
                // 예시 우선순위 정하기
                const aiResponseHeader = mainContent.querySelector('.ai-response-header');
                if (aiResponseHeader) {
                    mainContent.insertBefore(contentArea, aiResponseHeader);
                } else {
                    mainContent.appendChild(contentArea);
                }
                
                console.log('새 콘텐츠 영역 생성됨');
            } else {
                console.error('.main-content 영역을 찾을 수 없습니다');
                
                // 가장 중앙 요소를 임시로 사용
                contentArea = document.querySelector('main') || document.body;
                console.log('임시 콘텐트 영역 사용:', contentArea.tagName);
            }
        }
        
        // 로딩 표시
        const loadingHtml = '<div class="loading-indicator" style="text-align: center; padding: 20px; font-weight: bold;">문서 내용을 불러오는 중...</div>';
        
        // innerHTML 대신 클리어 후 요소 생성
        contentArea.innerHTML = '';
        const loadingEl = document.createElement('div');
        loadingEl.className = 'loading-indicator';
        loadingEl.style.cssText = 'text-align: center; padding: 20px; font-weight: bold;';
        loadingEl.textContent = '문서 내용을 불러오는 중...';
        contentArea.appendChild(loadingEl);
        
        // 문서 내용 가져오기
        fetch('/api/document/' + docId + '/processed')
        .then(response => {
            if (!response.ok) {
                throw new Error('문서 내용 불러오기 실패');
            }
            return response.json();
        })
        .then(data => {
            console.log('문서 데이터 로드됨:', data);
            
            // 문서 데이터 추출
            let content = '';
            let summary = '';
            let title = data.title || '문서 제목';
            let images = [];
            
            // 콘솔에서 데이터 형식 확인
            console.log('문서 데이터 형식:', typeof data, Object.keys(data));
            
            // 다양한 데이터 구조 처리
            if (data.data) {
                console.log('data.data 있음, 키:', Object.keys(data.data));
                if (data.data.content) content = data.data.content;
                if (data.data.summary) summary = data.data.summary;
                if (data.data.title) title = data.data.title;
                if (data.data.images) images = data.data.images;
            }
            
            // 직접 속성 확인
            if (!content && data.content) {
                console.log('data.content 형식:', typeof data.content);
                // 만약 content가 문자열이 아니고 객체라면
                if (typeof data.content === 'object') {
                    content = JSON.stringify(data.content, null, 2);
                } else {
                    content = data.content;
                }
            }
            
            if (!summary && data.summary) summary = data.summary;
            if (!images.length && data.images) images = data.images;
            
            // 내용이 없으면 전체 데이터 표시
            if (!content) {
                content = JSON.stringify(data, null, 2);
            }
            
            // 문서 제목 업데이트 - 여러 가능한 요소 확인
            const titleElements = document.querySelectorAll('.document-title, .doc-title, h1.document-title');
            console.log('제목 요소 개수:', titleElements.length);
            
            // 우선순위: 제목 업데이트
            if (titleElements.length > 0) {
                titleElements.forEach(el => {
                    el.textContent = title;
                    console.log('제목 업데이트:', title);
                });
            } else {
                console.log('제목 업데이트를 위한 요소를 찾을 수 없습니다');
                
                // 대체 요소 생성 추가 필요시 이 부분 추가 개발
            }
            
            // 시각적 피드백: 문서가 로드되었음을 알리는 효과
            // 1. 로드된 문서 항목 강조
            const documentItems = document.querySelectorAll('[data-id]');
            documentItems.forEach(item => {
                if (item.getAttribute('data-id') === docId) {
                    item.classList.add('selected');
                    item.classList.add('active');
                    item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                } else {
                    item.classList.remove('selected');
                    item.classList.remove('active');
                }
            });
            
            // 2. 출처 섹션 업데이트
            const sourceSection = document.querySelector('.document-source');
            if (sourceSection) {
                sourceSection.textContent = `출처: ${title}`;
                sourceSection.style.display = 'block';
            }
            
            // HTML 생성 - 요약만 표시
            let html = '';
            
            console.log('표시할 데이터:', {
                title: title,
                summary: summary ? (summary.length > 50 ? summary.substring(0, 50) + '...' : summary) : '없음',
            });
            
            // 요약만 표시
            if (summary) {
                html += `
                    <div class="summary-section">
                        <h3>요약</h3>
                        <div class="summary-content">${summary}</div>
                    </div>
                `;
            } else {
                // 요약이 없는 경우 안내 메시지
                html += `
                    <div class="no-summary-message">
                        <p>이 문서에 대한 요약이 없습니다.</p>
                    </div>
                `;
            }
            
            // 이미지 정보가 있는 경우 표시하지 않음 (DGU 요청으로 제거)
            
            // 내용 표시 (안전한 방식으로 화면 업데이트)
            console.log('문서 내용을 화면에 표시합니다');
            
            // 문서 선택시 중앙 영역 찾기 및 초기화
            const mainContent = document.querySelector('.main-content');
            if (mainContent) {
                // 기존 콘텐츠 모두 제거 - 결정적인 부분
                console.log('중앙 영역 초기화');
                
                // 모든 요소 제거 후 다시 구성
                // 이것은 이전 내용이 그대로 남는 문제를 해결하기 위한 조치입니다
                mainContent.innerHTML = '';
                
                // 문서 제목 추가
                const titleHeader = document.createElement('div');
                titleHeader.className = 'document-view-header';
                titleHeader.innerHTML = `
                    <div class="document-owl-container">
                        <img class="document-owl" src="https://cdn-icons-png.flaticon.com/512/6855/6855217.png" alt="문서 아이콘">
                    </div>
                    <h1 class="document-title">${title}</h1>
                `;
                mainContent.appendChild(titleHeader);
                
                // 소스 섹션 추가
                const sourceDiv = document.createElement('div');
                sourceDiv.className = 'document-source';
                sourceDiv.textContent = `출처: ${title}`;
                mainContent.appendChild(sourceDiv);
                
                // 콘텐츠 영역 추가
                contentArea = document.createElement('div');
                contentArea.className = 'document-content';
                contentArea.innerHTML = html;
                mainContent.appendChild(contentArea);
                
                // 하단 액션 버튼 영역 추가
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'content-actions';
                actionsDiv.innerHTML = `
                    <div class="action-buttons content-action-buttons">
                        <button class="content-action-btn" title="파일 첨부">
                            <span class="material-icons">attach_file</span>
                        </button>
                        <button class="content-action-btn" title="하이라이트">
                            <span class="material-icons">highlight</span>
                        </button>
                    </div>
                `;
                mainContent.appendChild(actionsDiv);
                
                // AI 응답 헤더 추가
                const aiHeaderDiv = document.createElement('div');
                aiHeaderDiv.className = 'ai-response-header';
                aiHeaderDiv.innerHTML = `
                    <div class="ai-badge">
                        <span class="material-icons">psychology</span>
                        <span>AI 응답</span>
                    </div>
                `;
                mainContent.appendChild(aiHeaderDiv);
            } else {
                // 기존 방식으로 표시
                contentArea.innerHTML = '';
                const container = document.createElement('div');
                container.className = 'document-container';
                container.innerHTML = html;
                contentArea.appendChild(container);
            }
            
            // 화면 스크롤을 위로 올리기
            window.scrollTo(0, 0);
            
            // 스타일 추가
            const style = document.createElement('style');
            style.textContent = `
                .summary-section {
                    background-color: #f5f5f5;
                    padding: 15px;
                    margin-bottom: 20px;
                    border-left: 4px solid #2196F3;
                    border-radius: 4px;
                }
                
                .content-section {
                    line-height: 1.6;
                }
                
                .content-text {
                    white-space: pre-line;
                    line-height: 1.6;
                }
                
                .loading-indicator {
                    text-align: center;
                    padding: 20px;
                    color: #666;
                }
            `;
            document.head.appendChild(style);
        })
        .catch(error => {
            console.error('문서 로드 오류:', error);
            contentArea.innerHTML = `<div class="error-message">오류: ${error.message}</div>`;
        });
    };
    
    // 문서 항목에 클릭 이벤트 추가
    function addClickEvents() {
        const items = document.querySelectorAll('.document-item, [data-id]');
        console.log('클릭 이벤트 추가할 문서 항목 수:', items.length);
        
        items.forEach(item => {
            // 기존 onclick 제거하고 새 onclick 설정
            item.removeAttribute('onclick');
            item.style.cursor = 'pointer';
            
            // 클릭 이벤트 직접 설정
            item.addEventListener('click', function() {
                const docId = this.getAttribute('data-id');
                if (docId) {
                    console.log('문서 클릭됨:', docId);
                    
                    // 선택 상태 표시
                    document.querySelectorAll('.document-item').forEach(el => {
                        el.classList.remove('selected');
                    });
                    this.classList.add('selected');
                    
                    // 문서 내용 표시
                    viewDocument(docId);
                    
                    // 문서 처리 상태 확인 시작
                    startProcessingCheck(docId);
                }
            });
        });
    }
    
    // 페이지 로드 시 이벤트 추가
    setTimeout(addClickEvents, 1000);
    
    // 문서 목록 변경 감지하여 새 항목에도 이벤트 추가
    setInterval(addClickEvents, 5000);
    
    // 현재 처리 중인 문서 ID 저장
    window.processingDocId = null;
    
    // 문서 클릭 후 처리 완료 자동 확인 기능 - 실제 존재하는 API만 사용
    window.startProcessingCheck = function(docId) {
        console.log('문서 처리 상태 확인 시작:', docId);
        
        // 처리할 문서 ID 저장
        window.processingDocId = docId;
        
        // 이전 확인 중지
        if (window.processingCheckInterval) {
            clearInterval(window.processingCheckInterval);
        }
        
        // 처리 상태 확인 - 오류 없는 심플 버전
        console.log('문서 처리 상태 확인 시작:', window.processingDocId);
        
        // 처리 상태 API 호출 주기 설정
        window.processingCheckInterval = setInterval(function() {
            if (!window.processingDocId) {
                clearInterval(window.processingCheckInterval);
                return;
            }
            
            console.log('처리 상태 확인 반복:', window.processingDocId);
            
            // 직접 processed API만 호출 (실제 존재하는 API만 사용)
            fetch('/api/document/' + window.processingDocId + '/processed')
            .then(function(response) {
                // API가 존재하지 않는 경우 404 오류가 발생
                if (response.status === 404) {
                    console.log('API 없음, 처리 상태 확인 중지');
                    clearInterval(window.processingCheckInterval);
                    return null;
                }
                return response.json();
            })
            .then(function(data) {
                // 데이터가 없는 경우 무시
                if (!data) return;
                
                console.log('처리된 데이터 확인:', data);
                
                // 데이터가 있으면 처리가 완료된 것으로 간주
                if (data && !data.error) {
                    console.log('처리 완료 감지!');
                    
                    // 중앙 영역 초기화
                    const mainContent = document.querySelector('.main-content');
                    if (mainContent) {
                        console.log('중앙 영역 초기화');
                        mainContent.innerHTML = '';
                    }
                    
                    // 처리된 문서 표시
                    try {
                        viewDocument(window.processingDocId);
                        console.log('문서 표시 완료');
                    } catch (e) {
                        console.error('문서 표시 오류:', e);
                    }
                    
                    // 처리 완료 알림 표시
                    if (typeof showNotification === 'function') {
                        showNotification('문서 처리가 완료되었습니다!', 'success');
                    }
                    
                    // 처리 상태 초기화
                    window.processingDocId = null;
                    clearInterval(window.processingCheckInterval);
                }
            })
            .catch(function(error) {
                console.error('처리 상태 확인 오류:', error);
            });
        }, 3000); // 3초마다 확인

    }
});
