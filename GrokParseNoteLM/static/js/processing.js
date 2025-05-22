// 문서 처리 진행 애니메이션 JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // 문서 처리 진행 상태 UI에 필요한 스타일 추가
    const processingStyle = document.createElement('style');
    processingStyle.textContent = `
        .processing-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            height: 100%;
            text-align: center;
        }
        
        .processing-animation {
            position: relative;
            width: 120px;
            height: 120px;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .brain-icon {
            position: relative;
            z-index: 2;
        }
        
        .brain-icon .material-icons {
            font-size: 3.5rem;
            color: #0066cc;
        }
        
        .processing-glow {
            position: absolute;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle, rgba(0,102,204,0.2) 0%, rgba(0,102,204,0) 70%);
            border-radius: 50%;
            animation: pulse-glow 2s infinite ease-in-out;
        }
        
        @keyframes pulse-glow {
            0% { transform: scale(0.8); opacity: 0.3; }
            50% { transform: scale(1.2); opacity: 0.7; }
            100% { transform: scale(0.8); opacity: 0.3; }
        }
        
        .processing-steps {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 2rem 0;
            width: 100%;
        }
        
        .step-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            width: 80px;
        }
        
        .step-icon {
            font-size: 1.8rem;
            color: #ccc;
            margin-bottom: 0.5rem;
            transition: color 0.3s ease;
        }
        
        .step-text {
            font-size: 0.75rem;
            color: #999;
            transition: color 0.3s ease;
        }
        
        .step-check {
            position: absolute;
            top: -5px;
            right: 10px;
            font-size: 1rem;
            color: #4CAF50;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .step-item.active .step-icon,
        .step-item.completed .step-icon {
            color: #0066cc;
        }
        
        .step-item.active .step-text,
        .step-item.completed .step-text {
            color: #0066cc;
            font-weight: 500;
        }
        
        .step-item.completed .step-check {
            opacity: 1;
        }
        
        .step-connector {
            height: 2px;
            background-color: #eee;
            width: 40px;
            margin: 0 5px;
        }
        
        .processing-progress {
            width: 100%;
            max-width: 300px;
            margin: 1rem 0;
        }
        
        .progress-bar {
            height: 8px;
            background-color: #f0f0f0;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 0.5rem;
        }
        
        .progress-fill {
            height: 100%;
            width: 0%;
            background-color: #0066cc;
            border-radius: 4px;
            transition: width 0.5s ease;
        }
        
        .progress-percentage {
            font-size: 0.85rem;
            color: #666;
        }
        
        .processing-message {
            font-size: 0.9rem;
            color: #666;
            margin-top: 1rem;
            min-height: 1.5rem;
        }
    `;
    document.head.appendChild(processingStyle);
    
    // 빈 문서 메시지 스타일 추가
    const emptyDocStyle = document.createElement('style');
    emptyDocStyle.textContent = `
        .empty-documents-message {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem 1rem;
            text-align: center;
            color: #666;
            height: 100%;
            min-height: 200px;
        }
        
        .empty-documents-message .material-icons {
            font-size: 2.5rem;
            color: #8f9eb3;
            margin-bottom: 1rem;
            opacity: 0.7;
        }
        
        .empty-documents-message p {
            margin: 0.5rem 0;
            font-size: 0.9rem;
        }
        
        .empty-documents-message .empty-hint {
            font-size: 0.8rem;
            color: #8f9eb3;
            margin-top: 0.5rem;
        }
    `;
    document.head.appendChild(emptyDocStyle);
    
    // 문서 처리 중 UI 표시 함수
    window.showProcessingUI = function() {
        const mainContent = document.querySelector('.document-content');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="processing-container">
                    <div class="processing-animation">
                        <div class="brain-icon">
                            <span class="material-icons">psychology</span>
                        </div>
                        <div class="processing-glow"></div>
                    </div>
                    <h3>문서 처리 중</h3>
                    <div class="processing-steps">
                        <div class="step-item active" id="step-extract">
                            <span class="step-icon material-icons">description</span>
                            <span class="step-text">텍스트 추출</span>
                            <span class="step-check material-icons">check_circle</span>
                        </div>
                        <div class="step-connector"></div>
                        <div class="step-item" id="step-images">
                            <span class="step-icon material-icons">image</span>
                            <span class="step-text">이미지 분석</span>
                            <span class="step-check material-icons">check_circle</span>
                        </div>
                        <div class="step-connector"></div>
                        <div class="step-item" id="step-analyze">
                            <span class="step-icon material-icons">psychology</span>
                            <span class="step-text">OpenAI 분석</span>
                            <span class="step-check material-icons">check_circle</span>
                        </div>
                    </div>
                    <div class="processing-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-fill"></div>
                        </div>
                        <div class="progress-percentage" id="progress-percentage">0%</div>
                    </div>
                    <div class="processing-message" id="processing-message">
                        텍스트 추출 중...
                    </div>
                </div>
            `;
            return true;
        }
        return false;
    };
    
    // 처리 단계 업데이트 함수
    window.updateProcessingStep = function(step, percentage) {
        // 진행률 업데이트
        const progressFill = document.getElementById('progress-fill');
        const progressPercentage = document.getElementById('progress-percentage');
        if (progressFill && progressPercentage) {
            progressFill.style.width = `${percentage}%`;
            progressPercentage.textContent = `${percentage}%`;
        }
        
        // 단계 상태 업데이트
        const extractStep = document.getElementById('step-extract');
        const imagesStep = document.getElementById('step-images');
        const analyzeStep = document.getElementById('step-analyze');
        const processingMessage = document.getElementById('processing-message');
        
        if (extractStep && imagesStep && analyzeStep && processingMessage) {
            // 모든 스텝 초기화
            [extractStep, imagesStep, analyzeStep].forEach(s => {
                s.classList.remove('active', 'completed');
            });
            
            // 현재 단계에 따른 UI 업데이트
            if (step === 'extract') {
                extractStep.classList.add('active');
                processingMessage.textContent = '텍스트 추출 중...';
            } else if (step === 'images') {
                extractStep.classList.add('completed');
                imagesStep.classList.add('active');
                processingMessage.textContent = '문서에서 추출한 이미지 분석 중...';
            } else if (step === 'analyze') {
                extractStep.classList.add('completed');
                imagesStep.classList.add('completed');
                analyzeStep.classList.add('active');
                processingMessage.textContent = 'OpenAI GPT-4 모델을 통해 문서 분석 중...';
            } else if (step === 'complete') {
                extractStep.classList.add('completed');
                imagesStep.classList.add('completed');
                analyzeStep.classList.add('completed');
                processingMessage.textContent = '문서 분석이 완료되었습니다!';
            }
            return true;
        }
        return false;
    };
});
