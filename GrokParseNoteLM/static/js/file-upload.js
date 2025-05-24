/**
 * 파일 업로드 관련 기능을 처리하는 JavaScript 파일
 * 파일 선택 다이얼로그가 자동으로 열리는 문제를 해결하기 위해 완전히 새로 작성되었습니다.
 */

// 사용자 인터랙션이 발생했는지 추적하는 변수
let userInteracted = false;
let fileSelected = false;

// 파일 선택 입력 요소 참조 변수
let fileInput = null;

// DOM이 로드된 후 실행
document.addEventListener('DOMContentLoaded', function() {
    console.log('File upload JS initialized (v2)');
    
    // DOM 요소
    const addDocBtn = document.getElementById('add-doc-btn');
    const sidebarAddDocBtn = document.getElementById('sidebar-add-doc-btn'); // 사이드바 + 버튼 추가
    const uploadModal = document.getElementById('upload-modal');
    const modalBrowseBtn = document.getElementById('modal-browse-btn');
    const modalDropzone = document.getElementById('modal-dropzone');
    const confirmUploadBtn = document.getElementById('confirm-upload-btn');
    const closeModalBtn = document.querySelector('.close-modal-btn');
    const cancelBtn = document.querySelector('.cancel-btn');
    const hiddenFileControls = document.getElementById('hidden-file-controls');
    
    // 사용자 인터랙션 추적
    document.addEventListener('click', function() {
        userInteracted = true;
    });
    
    // 파일 입력 삭제 함수
    function removeExistingFileInput() {
        if (fileInput && fileInput.parentNode) {
            fileInput.parentNode.removeChild(fileInput);
            fileInput = null;
        }
        
        // 새로운 파일 입력 필드를 위한 컨테이너 비우기
        if (hiddenFileControls) {
            while (hiddenFileControls.firstChild) {
                hiddenFileControls.removeChild(hiddenFileControls.firstChild);
            }
        }
    }
    
    // 문서 추가 모달 열기 함수
    function openUploadModal(e) {
        console.log('Opening upload modal');
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // 기존 파일 입력 제거
        removeExistingFileInput();
        
        // 상태 초기화
        if (modalDropzone && modalDropzone.querySelector('p')) {
            modalDropzone.querySelector('p').textContent = '문서를 여기에 끌어다 놓거나';
        }
        fileSelected = false;
        
        // 업로드 버튼 비활성화
        if (confirmUploadBtn) {
            confirmUploadBtn.disabled = true;
        }
        
        // 모달 표시
        uploadModal.classList.remove('hidden');
    }
    
    // 헤더 버튼 이벤트 등록
    if (addDocBtn) {
        addDocBtn.addEventListener('click', openUploadModal);
    }
    
    // 사이드바 버튼 이벤트 등록
    if (sidebarAddDocBtn) {
        sidebarAddDocBtn.addEventListener('click', openUploadModal);
        console.log('Sidebar add document button event registered');
    }
    
    // 모달 닫기
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', function() {
            uploadModal.classList.add('hidden');
        });
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            uploadModal.classList.add('hidden');
        });
    }
    
    // 파일 선택 버튼 클릭
    if (modalBrowseBtn) {
        modalBrowseBtn.addEventListener('click', function(e) {
            console.log('File browse button clicked');
            e.preventDefault();
            e.stopPropagation();
            
            // if (!userInteracted) {
            //     console.log('User has not interacted with the page yet');
            //     return;
            // }
            
            // 이전 파일 입력창 제거
            removeExistingFileInput();
            
            // 새로운 파일 입력 요소 생성
            fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = '.pdf,.txt,.md';
            fileInput.style.position = 'absolute';
            fileInput.style.width = '1px';
            fileInput.style.height = '1px';
            fileInput.style.opacity = '0';
            fileInput.style.pointerEvents = 'none';
            hiddenFileControls.appendChild(fileInput);
            
            // 파일 선택 이벤트 리스너 추가
            fileInput.addEventListener('change', function() {
                if (this.files && this.files.length > 0) {
                    const fileName = this.files[0].name;
                    console.log('File selected:', fileName);
                    
                    // UI 업데이트
                    if (modalDropzone && modalDropzone.querySelector('p')) {
                        modalDropzone.querySelector('p').textContent = `선택된 파일: ${fileName}`;
                    }
                    
                    // 업로드 버튼 활성화
                    if (confirmUploadBtn) {
                        confirmUploadBtn.disabled = false;
                    }
                    
                    fileSelected = true;
                }
            });
            
            // 사용자 지정 함수를 사용하여 다이얼로그 열기
            setTimeout(function() {
                console.log('Opening file dialog after delay');
                fileInput.click();
            }, 500);
        });
    }
    
    // 모달 닫기
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', function() {
            uploadModal.classList.add('hidden');
            removeExistingFileInput();
        });
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            uploadModal.classList.add('hidden');
            removeExistingFileInput();
        });
    }
    
    // 파일 업로드 처리
    if (confirmUploadBtn) {
        confirmUploadBtn.addEventListener('click', function() {
            if (!fileSelected || !fileInput || !fileInput.files || fileInput.files.length === 0) {
                console.log('No file selected');
                return;
            }
            
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            const autoProcess = document.getElementById('auto-process');
            if (autoProcess && autoProcess.checked) {
                formData.append('auto_process', 'true');
            }
            
            // 업로드 요청 전송
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                console.log('Upload successful:', data);
                uploadModal.classList.add('hidden');
                removeExistingFileInput();
                
                // 업로드 후 처리
                const uploadEvent = new CustomEvent('fileUploaded', { detail: data });
                document.dispatchEvent(uploadEvent);
                
                // 애니메이션 처리 함수 직접 호출
                if (typeof window.startProcessingAnimation === 'function' && data.document) {
                    const docId = data.document.id || data.document.doc_id;
                    const fileName = data.document.filename || data.document.name;
                    if (docId) {
                        console.log('애니메이션 직접 호출', docId, fileName);
                        window.startProcessingAnimation(docId, fileName);
                    }
                }
            })
            .catch(error => {
                console.error('Upload error:', error);
            });
        });
    }
    
    // 드래그 앤 드롭 기능 추가
    if (modalDropzone) {
        // 드래그 이벤트 처리
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            modalDropzone.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // 하이라이트 추가/제거
        ['dragenter', 'dragover'].forEach(eventName => {
            modalDropzone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            modalDropzone.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            modalDropzone.classList.add('highlight');
        }
        
        function unhighlight() {
            modalDropzone.classList.remove('highlight');
        }
        
        // 드롭 처리
        modalDropzone.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                // 이전 파일 입력창 제거
                removeExistingFileInput();
                
                // 새로운 파일 입력 요소 생성
                fileInput = document.createElement('input');
                fileInput.type = 'file';
                fileInput.accept = '.pdf,.txt,.md';
                hiddenFileControls.appendChild(fileInput);
                
                // 파일 데이터 설정 (파일 선택 창을 통해 가져온 것처럼)
                const fileName = files[0].name;
                modalDropzone.querySelector('p').textContent = `선택된 파일: ${fileName}`;
                
                // DataTransfer에서 파일을 포함하는 FormData 객체 생성
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(files[0]);
                fileInput.files = dataTransfer.files;
                
                // 업로드 버튼 활성화
                confirmUploadBtn.disabled = false;
                fileSelected = true;
            }
        }
    }
});
