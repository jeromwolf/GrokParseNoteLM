// OpenAI 모델로 처리된 문서 내용 로드
function loadProcessedDocument(docId) {
    // 중앙 패널에 로딩 상태 표시
    const mainContent = document.querySelector('.document-content');
    if (mainContent) {
        // 데이터가 준비되기 전에는 로딩 인디케이터만 표시
        mainContent.innerHTML = '<div class="loading-indicator"><span class="material-icons spin">autorenew</span><span>문서를 처리하는 중...</span></div>';
        
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
    
    // 문서 데이터 준비를 위한 변수
    let processedTitle = '';
    let processedContent = '';
    
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
            
            // 데이터를 완전히 준비한 후에만 UI 업데이트
            if (data.success && data.content) {
                // 문서 제목 준비
                if (data.title) {
                    processedTitle = data.title;
                }
                
                // 문서 내용 준비
                processedContent = '<div class="processed-document">';
                
                // GPT-4 분석 헤더 추가
                processedContent += `
                    <div class="ai-analysis-header">
                        <div class="ai-badge">
                            <span class="material-icons">psychology</span>
                            <span>${data.parser || '업스테이지 PDF 파서'} + ${data.model_type?.toUpperCase() || 'OPENAI'}${data.model_name ? ' - ' + data.model_name : ''} 분석</span>
                        </div>
                        <div class="analysis-timestamp">처리 시간: ${new Date().toLocaleString()}</div>
                    </div>`;
                
                // 요약 섹션 추가
                if (data.summary) {
                    processedContent += `
                        <div class="document-section">
                            <h3>핵심 요약</h3>
                            <div class="summary-content">${data.summary.replace(/\n/g, '<br>')}</div>
                        </div>`;
                }
                
                // 문서 내용 추가
                if (data.content) {
                    processedContent += `
                        <div class="document-section">
                            <h3>문서 내용</h3>
                            <div class="content-text">${data.content.replace(/\n/g, '<br>')}</div>
                        </div>`;
                }
                
                // 이미지 분석 결과 추가
                if (data.images && data.images.length > 0) {
                    processedContent += `
                        <div class="document-section">
                            <h3>이미지 분석 (총 ${data.images.length}개)</h3>
                            <div class="image-gallery">`;
                    
                    data.images.forEach((image, index) => {
                        processedContent += `
                            <div class="image-item">
                                <div class="image-container">
                                    <img src="${image.path}" alt="추출 이미지 ${index + 1}">
                                </div>
                                <div class="image-info">
                                    <span class="image-number">Image ${index + 1}</span>
                                    ${image.ocr_text ? `<div class="ocr-text">${image.ocr_text.replace(/\n/g, '<br>')}</div>` : ''}
                                </div>
                            </div>`;
                    });
                    
                    processedContent += `</div></div>`;
                }
                
                processedContent += '</div>';
                
                // 모든 데이터 준비가 끝난 후 한 번에 UI 업데이트
                const docTitle = document.querySelector('.document-title');
                if (docTitle) {
                    docTitle.textContent = processedTitle;
                }
                
                if (mainContent) {
                    // 준비된 모든 내용을 한 번에 적용
                    mainContent.innerHTML = processedContent;
                }
                
                // GPT-4 분석 헤더에 대한 스타일 추가
                const headerStyle = document.createElement('style');
                headerStyle.textContent = `
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
                document.head.appendChild(headerStyle);
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
