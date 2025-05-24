// 문서 클릭 처리를 위한 직접 클릭 핸들러 스크립트
document.addEventListener('DOMContentLoaded', function() {
    console.log('직접 클릭 이벤트 스크립트 로드됨');
    
    // 문서 선택시 빈 화면 제거
    function clearEmptyContentMessage() {
        const emptyMessage = document.querySelector('.empty-content-message');
        if (emptyMessage) {
            console.log('초기 빈 화면 제거');
            const mainContent = document.querySelector('.main-content');
            mainContent.removeChild(emptyMessage);
        }
    }
    
    // 모든 문서 항목에 직접 클릭 이벤트 추가
    function addDirectClickEvents() {
        // 1초 후 문서 항목 찾기 (DOM이 완전히 로드된 후)
        setTimeout(function() {
            // 가능한 모든 선택자로 문서 항목 찾기
            const items = document.querySelectorAll('.document-item, .doc-item, [data-id]');
            console.log('직접 클릭 이벤트를 추가할 항목 수:', items.length);
            
            items.forEach(function(item) {
                // 클릭 가능 스타일 추가
                item.style.cursor = 'pointer';
                item.classList.add('clickable');
                
                // onclick 속성 직접 추가 (이미 있는지 확인 후 추가)
                if (!item.hasAttribute('onclick')) {
                    item.setAttribute('onclick', 'handleDirectClick(this)');
                }
            });
        }, 1000);
    }
    
    // 전역 함수로 직접 클릭 핸들러 등록
    window.handleDirectClick = function(element) {
        console.log('직접 클릭 발생:', element);
        
        const docId = element.getAttribute('data-id');
        if (!docId) {
            console.error('문서 ID를 찾을 수 없습니다.');
            return;
        }
        
        // 빈 화면 메시지 제거 (초기 화면)
        clearEmptyContentMessage();
        
        // 중앙 영역 초기화 (중요: 기존 콘텐츠를 제거하기 위해)
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            // 현재 콘텐츠 확인
            console.log('중앙 영역 초기화 - 하위 요소:', mainContent.children.length);
            
            // 아예 완전히 초기화 (아주 중요함)
            mainContent.innerHTML = '';
        }
        
        // 문서 처리 상태 저장
        window.currentDocId = docId;
        window.currentDocElement = element;
        
        // 선택 상태 설정
        const allItems = document.querySelectorAll('[data-id]');
        allItems.forEach(item => item.classList.remove('selected'));
        element.classList.add('selected');
        
        // simpleViewer.js의 viewDocument 함수 호출
        if (typeof window.viewDocument === 'function') {
            console.log('viewDocument 함수 호출:', docId);
            window.viewDocument(docId);
            
            // 문서 처리 상태 확인 시작
            if (typeof window.startProcessingCheck === 'function') {
                console.log('문서 처리 상태 확인 시작:', docId);
                window.startProcessingCheck(docId);
            } else {
                console.warn('처리 상태 확인 기능을 찾을 수 없습니다.');
            }
        } else {
            console.error('viewDocument 함수를 찾을 수 없습니다. simpleViewer.js가 로드되었는지 확인하세요.');
        }
    }
    
    addDirectClickEvents();
});
