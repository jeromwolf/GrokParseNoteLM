// 문서 항목 클릭 이벤트 처리
document.addEventListener('DOMContentLoaded', function() {
    // 문서 항목 클릭 이벤트 (문서 선택 및 내용 표시)
    const documentItems = document.querySelectorAll('.document-item');
    if (documentItems.length > 0) {
        console.log('문서 항목 클릭 이벤트 설정:', documentItems.length);
        documentItems.forEach(item => {
            item.addEventListener('click', function() {
                console.log('문서 항목 클릭됨:', this.getAttribute('data-id'));
                // 선택 상태 토글
                documentItems.forEach(i => i.classList.remove('selected'));
                this.classList.add('selected');
                
                const docId = this.getAttribute('data-id');
                
                // 처리된 문서 내용 로드 (OpenAI 분석 결과)
                if (typeof loadProcessedDocument === 'function') {
                    loadProcessedDocument(docId);
                } else {
                    console.error('loadProcessedDocument 함수를 찾을 수 없습니다');
                    // 기본 문서 내용 표시 (폴백 옵션)
                    const mainContent = document.querySelector('.document-content');
                    if (mainContent) {
                        mainContent.innerHTML = '<div class="error-message">문서 처리 함수를 찾을 수 없습니다.</div>';
                    }
                }
            });
        });
    } else {
        console.log('문서 항목이 없습니다');
    }
});
