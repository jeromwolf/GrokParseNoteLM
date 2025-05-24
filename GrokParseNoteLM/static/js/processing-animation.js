/**
 * 문서 처리 애니메이션 및 알림 기능
 * 문서 업로드부터 처리 완료까지의 단계를 시각화합니다.
 */

// 처리 단계 정의
const PROCESSING_STEPS = [
    {
        id: 'upload',
        title: '문서 업로드',
        description: '서버에 문서를 업로드하는 중입니다',
        icon: 'cloud_upload'
    },
    {
        id: 'extract',
        title: '텍스트 추출',
        description: '문서에서 텍스트를 추출하는 중입니다',
        icon: 'subject'
    },
    {
        id: 'image_analysis',
        title: '이미지 분석',
        description: '문서 내 이미지를 분석하는 중입니다',
        icon: 'image'
    },
    {
        id: 'summarize',
        title: 'AI 요약 생성',
        description: 'AI가 문서 내용을 분석하고 요약하는 중입니다',
        icon: 'psychology'
    },
    {
        id: 'complete',
        title: '처리 완료',
        description: '문서 처리가 완료되었습니다',
        icon: 'check_circle'
    }
];

// 문서 처리 상태 관리 (전역 변수)
window.processingState = {
    isProcessing: false,
    currentStep: null,
    currentDocId: null,
    progressInterval: null
};

/**
 * 문서 처리 UI 생성 함수
 */
function createProcessingUI(fileName) {
    const processingContainer = document.createElement('div');
    processingContainer.className = 'processing-container';
    processingContainer.id = 'processing-animation';
    
    // 헤더 부분 생성
    const header = document.createElement('div');
    header.className = 'processing-header';
    
    const iconContainer = document.createElement('div');
    iconContainer.className = 'processing-icon';
    iconContainer.innerHTML = '<span class="material-icons">autorenew</span>';
    
    const title = document.createElement('h2');
    title.className = 'processing-title';
    title.textContent = '문서 처리 중';
    
    header.appendChild(iconContainer);
    header.appendChild(title);
    
    // 문서 정보 표시
    const fileInfo = document.createElement('div');
    fileInfo.style.padding = '10px';
    fileInfo.style.margin = '15px 0';
    fileInfo.style.backgroundColor = '#f5f5f5';
    fileInfo.style.borderRadius = '4px';
    fileInfo.style.textAlign = 'center';
    fileInfo.innerHTML = `<strong>처리중인 파일:</strong> ${fileName || '문서'}`;
    
    // 단계 컨테이너 생성
    const stepsContainer = document.createElement('div');
    stepsContainer.className = 'processing-steps';
    
    // 각 단계 요소 생성
    PROCESSING_STEPS.forEach(step => {
        const stepElement = document.createElement('div');
        stepElement.className = 'processing-step';
        stepElement.id = `processing-step-${step.id}`; // ID 형식 수정
        
        const stepIcon = document.createElement('div');
        stepIcon.className = 'step-icon';
        stepIcon.innerHTML = `<span class="material-icons">${step.icon}</span>`;
        
        const stepContent = document.createElement('div');
        stepContent.className = 'step-content';
        
        const stepTitle = document.createElement('div');
        stepTitle.className = 'step-title';
        stepTitle.textContent = step.title;
        
        const stepDesc = document.createElement('div');
        stepDesc.className = 'step-description';
        stepDesc.textContent = step.description;
        
        // 진행바 추가 (텍스트 추출, 이미지 분석, AI 요약 단계에만)
        if (['extract', 'image_analysis', 'summarize'].includes(step.id)) {
            const progressIndicator = document.createElement('div');
            progressIndicator.className = 'progress-indicator';
            
            const progressBar = document.createElement('div');
            progressBar.className = 'progress-bar';
            progressBar.id = `progress-${step.id}`;
            progressBar.style.width = '0%'; // 초기에 진행률 0으로 설정
            
            progressIndicator.appendChild(progressBar);
            stepContent.appendChild(stepTitle);
            stepContent.appendChild(stepDesc);
            stepContent.appendChild(progressIndicator);
        } else {
            stepContent.appendChild(stepTitle);
            stepContent.appendChild(stepDesc);
        }
        
        stepElement.appendChild(stepIcon);
        stepElement.appendChild(stepContent);
        
        stepsContainer.appendChild(stepElement);
    });
    
    processingContainer.appendChild(header);
    processingContainer.appendChild(fileInfo);
    processingContainer.appendChild(stepsContainer);
    
    // 외부 CSS 파일이 이미 있으므로 인라인 스타일 추가하지 않음
    
    return processingContainer;
}

/**
 * 현재 단계 활성화 함수
 */
function setActiveStep(stepId) {
    console.log('현재 활성화 단계:', stepId);
    // 모든 단계 요소 가져오기
    PROCESSING_STEPS.forEach((step, index) => {
        const stepElement = document.getElementById(`processing-step-${step.id}`);
        if (!stepElement) {
            console.warn(`단계 요소를 찾을 수 없음: processing-step-${step.id}`);
            return;
        }
        
        if (step.id === stepId) {
            // 현재 단계 활성화
            stepElement.classList.add('active');
            stepElement.classList.remove('completed');
            window.processingState.currentStep = step.id;
        } else if (index < PROCESSING_STEPS.findIndex(s => s.id === stepId)) {
            // 이전 단계는 완료로 표시
            stepElement.classList.remove('active');
            stepElement.classList.add('completed');
        } else {
            // 이후 단계는 비활성화
            stepElement.classList.remove('active');
            stepElement.classList.remove('completed');
        }
    });
}

/**
 * 진행 상태 업데이트 함수
 */
function updateProgress(stepId, percent) {
    console.log(`진행률 업데이트: ${stepId}, ${percent}%`);
    const progressBar = document.getElementById(`progress-${stepId}`);
    if (progressBar) {
        progressBar.style.width = `${percent}%`;
    } else {
        console.warn(`진행바를 찾을 수 없음: progress-${stepId}`);
    }
}

/**
 * 가상의 처리 과정 시뮤레이션
 */
function simulateProcessing() {
    console.log('처리 과정 시뮤레이션 시작');
    const steps = ['upload', 'extract', 'image_analysis', 'summarize', 'complete'];
    let currentIndex = 0;
    
    // 처음에는 업로드 단계 활성화
    setActiveStep(steps[currentIndex]);
    console.log('처음 단계 활성화:', steps[currentIndex]);
    
    // 업로드 단계 2초 후 다음 단계로 이동
    setTimeout(() => {
        currentIndex++; // 텍스트 추출 단계로 이동
        if (currentIndex < steps.length) {
            setActiveStep(steps[currentIndex]);
            console.log('다음 단계로 이동:', steps[currentIndex]);
            simulateStepProgress(steps, currentIndex);
        }
    }, 2000);
}

/**
 * 각 단계별 진행상황 시뮤레이션
 */
function simulateStepProgress(steps, startIndex) {
    let currentIndex = startIndex;
    const currentStep = steps[currentIndex];
    let progress = 0;
    
    // 현재 단계가 진행바가 있는 단계인지 확인
    const hasProgressBar = ['extract', 'image_analysis', 'summarize'].includes(currentStep);
    
    if (hasProgressBar) {
        console.log('진행상황 시뮤레이션 시작:', currentStep);
        
        // 진행바 업데이트 인터벌 설정
        const interval = setInterval(() => {
            // 이미 처리가 완료되었다면 중단
            if (!window.processingState.isProcessing) {
                clearInterval(interval);
                return;
            }
            
            progress += 5;
            updateProgress(currentStep, progress);
            console.log('진행상황 업데이트:', currentStep, progress + '%');
            
            if (progress >= 100) {
                clearInterval(interval);
                
                // 다음 단계로 이동
                currentIndex++;
                if (currentIndex < steps.length) {
                    setActiveStep(steps[currentIndex]);
                    console.log('다음 단계로 이동:', steps[currentIndex]);
                    
                    // 공통 지연시간
                    setTimeout(() => {
                        // 다음 단계 시뮤레이션 진행
                        simulateStepProgress(steps, currentIndex);
                    }, 500);
                } else {
                    // 모든 단계 완료
                    completeProcessing();
                }
            }
        }, 200); // 진행상황 업데이트 주기 단축
    } else {
        // 진행바가 없는 단계는 3초 후 다음 단계로 자동 이동
        setTimeout(() => {
            currentIndex++;
            if (currentIndex < steps.length) {
                setActiveStep(steps[currentIndex]);
                console.log('다음 단계로 이동:', steps[currentIndex]);
                simulateStepProgress(steps, currentIndex);
            } else {
                // 모든 단계 완료
                completeProcessing();
            }
        }, 3000);
    }
}

/**
 * 진행 상태 시뮤레이션 - 새 시뮤레이션 방식으로 교체
 */
function simulateProgress() {
    // 사용하지 않음 - 새로운 simulateStepProgress 함수에서 처리
    console.log('이전 simulateProgress 함수 호출 (deprecated)');
}

/**
 * 실제 처리 상태 확인
 */
function checkProcessingStatus(docId) {
    // 3초마다 처리 상태 확인
    const statusInterval = setInterval(() => {
        // 이미 처리가 완료되었다면 중단
        if (!window.processingState.isProcessing) {
            clearInterval(statusInterval);
            return;
        }
        
        // 처리된 문서 데이터 확인
        fetch(`/api/document/${docId}/processed`)
        .then(response => {
            if (response.status === 404) {
                // 아직 처리 중
                return null;
            }
            return response.json();
        })
        .then(data => {
            if (!data) return;
            
            console.log('처리된 데이터 확인:', data);
            
            // 데이터가 있으면 처리가 완료된 것으로 간주
            if (data && !data.error) {
                clearInterval(statusInterval);
                completeProcessing();
            }
        })
        .catch(error => {
            console.error('처리 상태 확인 오류:', error);
        });
    }, 3000);
}

/**
 * 처리 완료 함수
 */
function completeProcessing() {
    // 처리 완료 단계로 설정
    setActiveStep('complete');
    window.processingState.isProcessing = false;
    
    if (window.processingState.progressInterval) {
        clearInterval(window.processingState.progressInterval);
    }
    
    // 알림 표시
    showNotification('문서 처리가 완료되었습니다!', 'success');
    
    // 처리된 문서 로드
    setTimeout(() => {
        if (window.processingState.currentDocId && typeof viewDocument === 'function') {
            viewDocument(window.processingState.currentDocId);
        }
    }, 1000);
}

/**
 * 알림 표시 함수
 */
function showNotification(message, type = 'info') {
    // 기존 알림 삭제
    const existingNotification = document.getElementById('processing-notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // 알림 요소 생성
    const notification = document.createElement('div');
    notification.id = 'processing-notification';
    notification.style.position = 'fixed';
    notification.style.bottom = '20px';
    notification.style.right = '20px';
    notification.style.padding = '15px 20px';
    notification.style.backgroundColor = type === 'success' ? '#4caf50' : '#1565c0';
    notification.style.color = 'white';
    notification.style.borderRadius = '4px';
    notification.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
    notification.style.display = 'flex';
    notification.style.alignItems = 'center';
    notification.style.zIndex = '1000';
    notification.style.transform = 'translateY(100px)';
    notification.style.opacity = '0';
    notification.style.transition = 'all 0.3s ease';
    
    // 아이콘 설정
    let icon = 'info';
    if (type === 'success') icon = 'check_circle';
    if (type === 'error') icon = 'error';
    
    notification.innerHTML = `
        <div style="margin-right: 10px;">
            <span class="material-icons">${icon}</span>
        </div>
        <div style="font-weight: 500;">${message}</div>
        <div style="margin-left: 15px; cursor: pointer;" onclick="this.parentNode.remove();">
            <span class="material-icons">close</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // 알림 표시 애니메이션
    setTimeout(() => {
        notification.style.transform = 'translateY(0)';
        notification.style.opacity = '1';
    }, 10);
    
    // 자동 닫기
    setTimeout(() => {
        notification.style.transform = 'translateY(100px)';
        notification.style.opacity = '0';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

/**
 * 문서 처리 애니메이션 시작 함수
 */
window.startProcessingAnimation = function(docId, fileName) {
    console.log('문서 처리 애니메이션 시작:', docId, fileName);
    console.log('문서 처리 상태:', window.processingState);
    
    // 이미 처리 중이면 중단
    if (window.processingState.isProcessing) {
        console.log('이미 문서 처리 중입니다');
        return;
    }
    
    // 상태 초기화
    window.processingState.isProcessing = true;
    window.processingState.currentDocId = docId;
    window.processingState.currentStep = 'upload';
    
    // 메인 컨텐츠 영역 찾기 - 다양한 셀렉터로 시도
    console.log('메인 컨텐츠 영역 검색 시작');
    
    // 다양한 셀렉터와 방법으로 요소 찾기 시도
    let mainContent = document.querySelector('section.main-content');
    
    if (!mainContent) {
        console.log('section.main-content 요소를 찾을 수 없습니다. 다른 셀렉터 시도...');
        mainContent = document.querySelector('.main-content');
    }
    
    if (!mainContent) {
        console.log('다른 셀렉터도 실패. .app-content 내부에서 찾기 시도...');
        const appContent = document.querySelector('.app-content');
        
        if (appContent) {
            // 앞에서 부터 두 번째 자식은 일반적으로 중앙 컨텐츠
            const children = appContent.children;
            if (children.length > 1) {
                mainContent = children[1]; // 일반적으로 중앙 컨텐츠는 두 번째 자식
                console.log('.app-content의 두 번째 자식 요소를 사용합니다:', mainContent);
            } else {
                console.log('.app-content에 충분한 자식 요소가 없습니다.');
            }
        }
    }
    
    if (!mainContent) {
        // 여전히 찾지 못했다면 app-container에 새 요소 생성
        console.log('메인 컨텐츠 영역을 찾을 수 없어 새로 생성합니다.');
        const appContainer = document.querySelector('.app-container');
        
        if (appContainer) {
            mainContent = document.createElement('section');
            mainContent.className = 'main-content';
            
            // 이미 존재하는 app-content 영역에 추가
            const appContent = appContainer.querySelector('.app-content');
            if (appContent) {
                // 일반적으로 사이드바 다음에 추가
                const sidebar = appContent.querySelector('.sidebar');
                if (sidebar && sidebar.nextSibling) {
                    appContent.insertBefore(mainContent, sidebar.nextSibling);
                } else {
                    appContent.appendChild(mainContent);
                }
            } else {
                appContainer.appendChild(mainContent);
            }
            console.log('새 메인 컨텐츠 영역 생성함:', mainContent);
        } else {
            console.error('app-container를 찾을 수 없습니다.');
            return; // 중요한 컨테이너를 찾을 수 없으면 중단
        }
    }
    
    // 기존 내용 지우기
    console.log('기존 내용을 지우고 애니메이션 UI 추가:', mainContent);
    mainContent.innerHTML = '';
    
    // 처리 애니메이션 UI 생성 및 추가
    const processingUI = createProcessingUI(fileName);
    mainContent.appendChild(processingUI);
    
    // 가상의 처리 과정 시작 (0.5초 뒤 시작해서 DOM이 초기화될 시간 확보)
    setTimeout(() => {
        simulateProcessing();
    }, 500);
    
    // 실제 처리 상태 확인 시작
    checkProcessingStatus(docId);
};

// DOM 로드 시 초기화 함수
document.addEventListener('DOMContentLoaded', function() {
    console.log('문서 처리 애니메이션 스크립트 로드됨');
    
    // 파일 업로드 성공 이벤트 핸들러
    const fileUploadHandler = function(event) {
        if (event.detail && event.detail.success && event.detail.document) {
            const docId = event.detail.document.id || event.detail.document.doc_id;
            const fileName = event.detail.document.filename || event.detail.document.name;
            
            if (docId) {
                // 문서 처리 애니메이션 시작
                window.startProcessingAnimation(docId, fileName);
            }
        }
    };
    
    // 파일 업로드 이벤트 리스너 추가
    document.addEventListener('fileUploaded', fileUploadHandler);
    
    console.log('문서 처리 애니메이션 초기화 완료');
});
