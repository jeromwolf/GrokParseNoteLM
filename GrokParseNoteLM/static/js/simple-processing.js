/**
 * 간단한 문서 처리 애니메이션 모듈
 * DOM 구조와 상관없이 전체 화면 오버레이로 처리 애니메이션 표시
 */

// 전역 상태 객체
window.simpleProcessingState = {
    active: false,
    currentDocId: null,
    currentStep: null
};

/**
 * 문서 처리 애니메이션 시작
 * @param {string} docId - 문서 ID
 * @param {string} fileName - 파일 이름
 */
function startSimpleProcessing(docId, fileName) {
    console.log('간단한 처리 애니메이션 시작:', docId, fileName);
    
    // 이미 활성화된 경우 처리 중단
    if (window.simpleProcessingState.active) {
        console.log('이미 처리 중인 애니메이션이 있습니다');
        return;
    }
    
    // 상태 업데이트
    window.simpleProcessingState.active = true;
    window.simpleProcessingState.currentDocId = docId;
    window.simpleProcessingState.currentStep = 'upload';
    
    // 이전 오버레이 제거
    const existingOverlay = document.querySelector('#simple-processing-overlay');
    if (existingOverlay) {
        existingOverlay.remove();
    }
    
    // 오버레이 생성
    const overlay = document.createElement('div');
    overlay.id = 'simple-processing-overlay';
    overlay.style.cssText = 'position:fixed; top:0; left:0; width:100%; height:100%; background-color:rgba(255,255,255,0.95); z-index:9999; display:flex; align-items:center; justify-content:center;';
    
    // 컨테이너 생성
    const container = document.createElement('div');
    container.className = 'simple-processing-container';
    container.style.cssText = 'width:90%; max-width:600px; padding:20px; border-radius:8px; background-color:#f9f9f9; box-shadow:0 2px 10px rgba(0,0,0,0.1);';
    
    // 애니메이션 HTML 구성
    container.innerHTML = `
        <div style="display:flex; align-items:center; margin-bottom:20px; padding-bottom:15px; border-bottom:1px solid #eee;">
            <div style="width:40px; height:40px; border-radius:50%; background-color:#e8f4fe; display:flex; align-items:center; justify-content:center; margin-right:15px;">
                <span class="material-icons" style="color:#2196f3; animation:spin 2s linear infinite;">autorenew</span>
            </div>
            <h2 style="font-size:18px; font-weight:600; color:#333; margin:0;">문서 처리 중</h2>
        </div>
        <div style="padding:10px; margin:15px 0; background-color:#f5f5f5; border-radius:4px; text-align:center;">
            <strong>처리중인 파일:</strong> ${fileName || '문서'}
        </div>
        <div class="processing-steps" style="margin-top:20px;">
            <div class="processing-step active" id="simple-step-upload" style="display:flex; padding:12px 0; position:relative; opacity:1;">
                <div class="step-icon" style="width:40px; height:40px; border-radius:50%; background-color:#e8f4fe; display:flex; align-items:center; justify-content:center; margin-right:15px; position:relative; z-index:2;">
                    <span class="material-icons" style="font-size:20px; color:#2196f3;">cloud_upload</span>
                </div>
                <div style="flex:1;">
                    <div style="font-weight:600; margin-bottom:4px; color:#333;">문서 업로드</div>
                    <div style="font-size:14px; color:#666;">서버에 문서를 업로드하는 중입니다</div>
                </div>
            </div>
            <div class="processing-step" id="simple-step-extract" style="display:flex; padding:12px 0; position:relative; opacity:0.5;">
                <div class="step-icon" style="width:40px; height:40px; border-radius:50%; background-color:#f5f5f5; display:flex; align-items:center; justify-content:center; margin-right:15px; position:relative; z-index:2;">
                    <span class="material-icons" style="font-size:20px; color:#757575;">subject</span>
                </div>
                <div style="flex:1;">
                    <div style="font-weight:600; margin-bottom:4px; color:#333;">텍스트 추출</div>
                    <div style="font-size:14px; color:#666;">문서에서 텍스트를 추출하는 중입니다</div>
                    <div style="height:8px; width:100%; background-color:#f5f5f5; border-radius:4px; overflow:hidden; margin-top:8px;">
                        <div id="simple-progress-extract" style="height:100%; background-color:#2196f3; width:0%; transition:width 0.3s ease;"></div>
                    </div>
                </div>
            </div>
            <div class="processing-step" id="simple-step-image_analysis" style="display:flex; padding:12px 0; position:relative; opacity:0.5;">
                <div class="step-icon" style="width:40px; height:40px; border-radius:50%; background-color:#f5f5f5; display:flex; align-items:center; justify-content:center; margin-right:15px; position:relative; z-index:2;">
                    <span class="material-icons" style="font-size:20px; color:#757575;">image</span>
                </div>
                <div style="flex:1;">
                    <div style="font-weight:600; margin-bottom:4px; color:#333;">이미지 분석</div>
                    <div style="font-size:14px; color:#666;">문서 내 이미지를 분석하는 중입니다</div>
                    <div style="height:8px; width:100%; background-color:#f5f5f5; border-radius:4px; overflow:hidden; margin-top:8px;">
                        <div id="simple-progress-image" style="height:100%; background-color:#2196f3; width:0%; transition:width 0.3s ease;"></div>
                    </div>
                </div>
            </div>
            <div class="processing-step" id="simple-step-summarize" style="display:flex; padding:12px 0; position:relative; opacity:0.5;">
                <div class="step-icon" style="width:40px; height:40px; border-radius:50%; background-color:#f5f5f5; display:flex; align-items:center; justify-content:center; margin-right:15px; position:relative; z-index:2;">
                    <span class="material-icons" style="font-size:20px; color:#757575;">psychology</span>
                </div>
                <div style="flex:1;">
                    <div style="font-weight:600; margin-bottom:4px; color:#333;">AI 요약 생성</div>
                    <div style="font-size:14px; color:#666;">AI가 문서 내용을 분석하고 요약하는 중입니다</div>
                    <div style="height:8px; width:100%; background-color:#f5f5f5; border-radius:4px; overflow:hidden; margin-top:8px;">
                        <div id="simple-progress-summarize" style="height:100%; background-color:#2196f3; width:0%; transition:width 0.3s ease;"></div>
                    </div>
                </div>
            </div>
            <div class="processing-step" id="simple-step-complete" style="display:flex; padding:12px 0; position:relative; opacity:0.5;">
                <div class="step-icon" style="width:40px; height:40px; border-radius:50%; background-color:#f5f5f5; display:flex; align-items:center; justify-content:center; margin-right:15px; position:relative; z-index:2;">
                    <span class="material-icons" style="font-size:20px; color:#757575;">check_circle</span>
                </div>
                <div style="flex:1;">
                    <div style="font-weight:600; margin-bottom:4px; color:#333;">처리 완료</div>
                    <div style="font-size:14px; color:#666;">문서 처리가 완료되었습니다</div>
                </div>
            </div>
        </div>
    `;
    
    // 애니메이션 스타일 추가
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
    
    // DOM에 추가
    overlay.appendChild(container);
    document.body.appendChild(overlay);
    
    // 애니메이션 시작
    simulateSteps();
}

/**
 * 처리 단계 시뮬레이션
 */
function simulateSteps() {
    console.log('처리 단계 시뮬레이션 시작');
    
    // 업로드 단계 완료
    const uploadStep = document.getElementById('simple-step-upload');
    if (uploadStep) {
        uploadStep.style.opacity = '1';
        const icon = uploadStep.querySelector('.step-icon');
        if (icon) {
            icon.style.backgroundColor = '#e8f5e9';
            const iconSpan = icon.querySelector('.material-icons');
            if (iconSpan) iconSpan.style.color = '#4caf50';
        }
    }
    
    // 텍스트 추출 단계
    setTimeout(() => {
        window.simpleProcessingState.currentStep = 'extract';
        const extractStep = document.getElementById('simple-step-extract');
        if (!extractStep) return;
        
        extractStep.style.opacity = '1';
        const extractIcon = extractStep.querySelector('.step-icon');
        if (extractIcon) {
            extractIcon.style.backgroundColor = '#e8f4fe';
            const iconSpan = extractIcon.querySelector('.material-icons');
            if (iconSpan) iconSpan.style.color = '#2196f3';
        }
        
        // 진행률 애니메이션
        const progressBar = document.getElementById('simple-progress-extract');
        let progress = 0;
        const interval = setInterval(() => {
            progress += 5;
            if (progressBar) progressBar.style.width = progress + '%';
            
            if (progress >= 100) {
                clearInterval(interval);
                if (extractIcon) {
                    extractIcon.style.backgroundColor = '#e8f5e9';
                    const iconSpan = extractIcon.querySelector('.material-icons');
                    if (iconSpan) iconSpan.style.color = '#4caf50';
                }
                
                // 이미지 분석 단계
                startImageAnalysisStep();
            }
        }, 100);
    }, 1000);
}

/**
 * 이미지 분석 단계 시작
 */
function startImageAnalysisStep() {
    window.simpleProcessingState.currentStep = 'image_analysis';
    const imageStep = document.getElementById('simple-step-image_analysis');
    if (!imageStep) return;
    
    imageStep.style.opacity = '1';
    const imageIcon = imageStep.querySelector('.step-icon');
    if (imageIcon) {
        imageIcon.style.backgroundColor = '#e8f4fe';
        const iconSpan = imageIcon.querySelector('.material-icons');
        if (iconSpan) iconSpan.style.color = '#2196f3';
    }
    
    // 진행률 애니메이션
    const progressBar = document.getElementById('simple-progress-image');
    let progress = 0;
    const interval = setInterval(() => {
        progress += 7;
        if (progressBar) progressBar.style.width = progress + '%';
        
        if (progress >= 100) {
            clearInterval(interval);
            if (imageIcon) {
                imageIcon.style.backgroundColor = '#e8f5e9';
                const iconSpan = imageIcon.querySelector('.material-icons');
                if (iconSpan) iconSpan.style.color = '#4caf50';
            }
            
            // 요약 단계
            startSummarizeStep();
        }
    }, 120);
}

/**
 * 요약 단계 시작
 */
function startSummarizeStep() {
    window.simpleProcessingState.currentStep = 'summarize';
    const summarizeStep = document.getElementById('simple-step-summarize');
    if (!summarizeStep) return;
    
    summarizeStep.style.opacity = '1';
    const summarizeIcon = summarizeStep.querySelector('.step-icon');
    if (summarizeIcon) {
        summarizeIcon.style.backgroundColor = '#e8f4fe';
        const iconSpan = summarizeIcon.querySelector('.material-icons');
        if (iconSpan) iconSpan.style.color = '#2196f3';
    }
    
    // 진행률 애니메이션
    const progressBar = document.getElementById('simple-progress-summarize');
    let progress = 0;
    const interval = setInterval(() => {
        progress += 4;
        if (progressBar) progressBar.style.width = progress + '%';
        
        if (progress >= 100) {
            clearInterval(interval);
            if (summarizeIcon) {
                summarizeIcon.style.backgroundColor = '#e8f5e9';
                const iconSpan = summarizeIcon.querySelector('.material-icons');
                if (iconSpan) iconSpan.style.color = '#4caf50';
            }
            
            // 완료 단계
            completeProcessing();
        }
    }, 150);
}

/**
 * 처리 완료 단계
 */
function completeProcessing() {
    window.simpleProcessingState.currentStep = 'complete';
    const completeStep = document.getElementById('simple-step-complete');
    if (!completeStep) return;
    
    completeStep.style.opacity = '1';
    const completeIcon = completeStep.querySelector('.step-icon');
    if (completeIcon) {
        completeIcon.style.backgroundColor = '#e8f5e9';
        const iconSpan = completeIcon.querySelector('.material-icons');
        if (iconSpan) iconSpan.style.color = '#4caf50';
    }
    
    // 2초 후 화면 새로고침 또는 다음 단계로 진행
    setTimeout(() => {
        window.simpleProcessingState.active = false;
        window.location.reload();
    }, 2000);
}

// 전역 스코프에 함수 노출
window.startSimpleProcessing = startSimpleProcessing;
