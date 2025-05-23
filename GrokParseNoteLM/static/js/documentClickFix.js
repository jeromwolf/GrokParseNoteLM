// 문서 항목 클릭 이벤트 강력 바인딩
document.addEventListener('DOMContentLoaded', function() {
    console.log('documentClickFix.js 로딩됨');
    
    // 문서 목록에 이벤트 위임 방식으로 처리
    const documentList = document.getElementById('document-list');
    if (documentList) {
        console.log('문서 목록 요소 찾음:', documentList);
        
        // 문서 목록 전체에 클릭 이벤트를 위임하여 처리
        documentList.addEventListener('click', function(event) {
            // 클릭된 요소가 문서 항목이거나 그 하위 요소인지 확인
            let targetElement = event.target;
            let documentItem = null;
            
            // 클릭된 요소나 부모 요소 중 .document-item 클래스를 가진 요소 찾기
            while (targetElement && targetElement !== documentList) {
                if (targetElement.classList.contains('document-item')) {
                    documentItem = targetElement;
                    break;
                }
                targetElement = targetElement.parentElement;
            }
            
            // 문서 항목을 찾았다면 처리
            if (documentItem) {
                const docId = documentItem.getAttribute('data-id');
                console.log('문서 항목 클릭됨 (위임 방식):', docId);
                
                // 모든 문서 항목에서 선택 상태 제거
                const allItems = documentList.querySelectorAll('.document-item');
                allItems.forEach(item => item.classList.remove('selected'));
                
                // 클릭된 항목에 선택 상태 추가
                documentItem.classList.add('selected');
                
                // 처리된 문서 내용 로드
                if (typeof loadProcessedDocument === 'function') {
                    console.log('loadProcessedDocument 함수 호출:', docId);
                    loadProcessedDocument(docId);
                } else {
                    console.error('loadProcessedDocument 함수를 찾을 수 없습니다');
                    alert('문서 처리 기능을 로드할 수 없습니다. 페이지를 새로고침해 주세요.');
                }
            }
        });
    } else {
        console.error('문서 목록 요소를 찾을 수 없습니다');
    }
    
    // 기존 방식으로도 바인딩 시도
    const documentItems = document.querySelectorAll('.document-item');
    if (documentItems.length > 0) {
        console.log('기존 방식으로 문서 항목 이벤트 바인딩:', documentItems.length);
        documentItems.forEach(item => {
            item.addEventListener('click', function() {
                const docId = this.getAttribute('data-id');
                console.log('문서 항목 직접 클릭됨:', docId);
                
                // 모든 문서 항목에서 선택 상태 제거
                documentItems.forEach(i => i.classList.remove('selected'));
                
                // 클릭된 항목에 선택 상태 추가
                this.classList.add('selected');
                
                // 처리된 문서 내용 로드
                if (typeof loadProcessedDocument === 'function') {
                    loadProcessedDocument(docId);
                } else {
                    console.error('loadProcessedDocument 함수를 찾을 수 없습니다');
                }
            });
        });
    }
    
    // 페이지 로드 완료 후 현재 문서 목록 상태 로그로 출력
    setTimeout(function() {
        const items = document.querySelectorAll('.document-item');
        console.log('페이지 로드 후 문서 항목 수:', items.length);
        items.forEach((item, index) => {
            console.log(`문서 항목 ${index+1}:`, item.getAttribute('data-id'), item.querySelector('.doc-title')?.textContent);
        });
    }, 1000);
});
