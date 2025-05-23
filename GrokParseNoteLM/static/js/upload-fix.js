/**
 * 파일 업로드 모달 문제를 해결하기 위한 긴급 수정 스크립트
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Upload fix script loaded');
    
    // 문서 추가 버튼 강제 연결
    const addDocBtn = document.getElementById('add-doc-btn');
    const uploadModal = document.getElementById('upload-modal');
    
    if (addDocBtn && uploadModal) {
        console.log('Found add document button and upload modal - fixing connection');
        
        // 기존 이벤트 리스너 제거를 위해 복제 후 교체
        const newAddDocBtn = addDocBtn.cloneNode(true);
        addDocBtn.parentNode.replaceChild(newAddDocBtn, addDocBtn);
        
        // 새로운 이벤트 리스너 추가
        newAddDocBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Add document button clicked (from fix script)');
            uploadModal.classList.remove('hidden');
        });
    } else {
        console.error('Could not find add document button or upload modal');
    }
});
