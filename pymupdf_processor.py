import os
import fitz  # PyMuPDF
import logging
import time
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

# 로깅 설정
logger = logging.getLogger('pymupdf_processor')

def extract_text_and_images_from_pdf(pdf_path: str, output_dir: str, save_debug_info: bool = True) -> Tuple[str, List[str]]:
    """PDF 파일에서 텍스트와 이미지를 추출합니다 (PyMuPDF 사용).
    
    Args:
        pdf_path: PDF 파일 경로
        output_dir: 추출된 이미지를 저장할 디렉토리
        save_debug_info: 디버그 정보를 파일로 저장할지 여부
        
    Returns:
        (추출된_텍스트, 이미지_경로_리스트) 튜플
    """
    # 이미지 저장 디렉토리 생성
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # 로그 디렉토리 생성
    logs_dir = os.path.join(output_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # 현재 시간을 이용한 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 결과 저장 변수
    all_text = ""
    image_paths = []
    
    # 성능 측정 시작
    start_time = time.time()
    
    try:
        logger.info(f"PyMuPDF를 사용하여 {os.path.basename(pdf_path)} 파싱 시작")
        print(f"PyMuPDF를 사용하여 {pdf_path} 파싱 중...")
        
        # 파일 크기 확인
        file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB 단위
        logger.info(f"PDF 파일 크기: {file_size:.2f} MB")
        
        # PDF 문서 열기
        try:
            doc = fitz.open(pdf_path)
            logger.info(f"PDF 문서 열기 성공: {len(doc)} 페이지")
        except Exception as e:
            logger.error(f"PDF 문서 열기 실패: {str(e)}")
            raise
        
        # 문서 메타데이터 확인
        metadata = doc.metadata
        if metadata and save_debug_info:
            logger.info(f"PDF 메타데이터: {metadata}")
            
            # 메타데이터 저장
            try:
                meta_file = os.path.join(logs_dir, f"metadata_{timestamp}.txt")
                with open(meta_file, 'w', encoding='utf-8') as f:
                    for key, value in metadata.items():
                        f.write(f"{key}: {value}\n")
            except Exception as e:
                logger.warning(f"메타데이터 저장 실패: {str(e)}")
        
        # 각 페이지 처리
        for page_num, page in enumerate(doc):
            page_start_time = time.time()
            logger.info(f"페이지 {page_num+1}/{len(doc)} 처리 중...")
            print(f"페이지 {page_num+1}/{len(doc)} 처리 중...")
            
            # 텍스트 추출
            try:
                page_text = page.get_text()
                text_length = len(page_text)
                all_text += page_text + "\n\n"
                logger.debug(f"페이지 {page_num+1} 텍스트 추출 완료: {text_length} 자")
            except Exception as e:
                logger.error(f"페이지 {page_num+1} 텍스트 추출 실패: {str(e)}")
                page_text = ""
            
            # 이미지 추출
            try:
                image_list = page.get_images(full=True)
                logger.debug(f"페이지 {page_num+1} 이미지 목록 추출: {len(image_list)}개")
            except Exception as e:
                logger.error(f"페이지 {page_num+1} 이미지 목록 추출 실패: {str(e)}")
                image_list = []
            
            # 페이지에서 이미지 추출 및 저장
            page_images_count = 0
            for img_idx, img_info in enumerate(image_list):
                try:
                    xref = img_info[0]  # 이미지 참조 번호
                    base_image = doc.extract_image(xref)
                    
                    if not base_image:
                        logger.warning(f"페이지 {page_num+1}의 이미지 {img_idx+1} 추출 실패: 빈 이미지")
                        continue
                        
                    image_bytes = base_image.get("image")
                    if not image_bytes:
                        logger.warning(f"페이지 {page_num+1}의 이미지 {img_idx+1} 추출 실패: 이미지 데이터 없음")
                        continue
                        
                    image_ext = base_image.get("ext", "png")
                    
                    # 이미지 품질 및 크기 정보
                    width = base_image.get("width", 0)
                    height = base_image.get("height", 0)
                    colorspace = base_image.get("colorspace", "")
                    
                    # 너무 작은 이미지 필터링 (옵션)
                    min_dimension = 50  # 최소 50픽셀
                    if width < min_dimension or height < min_dimension:
                        logger.debug(f"페이지 {page_num+1}의 이미지 {img_idx+1} 건너뜀: 크기가 너무 작음 ({width}x{height})")
                        continue
                    
                    # 이미지 파일 저장
                    image_filename = f"page{page_num+1}_img{img_idx+1}.{image_ext}"
                    image_path = os.path.join(images_dir, image_filename)
                    
                    try:
                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)
                        
                        # 이미지 크기 확인
                        image_size = os.path.getsize(image_path) / 1024  # KB 단위
                        
                        image_paths.append(image_path)
                        page_images_count += 1
                        
                        logger.debug(f"이미지 저장: {image_filename} ({width}x{height}, {image_size:.1f} KB, {colorspace})")
                        print(f"이미지 저장: {image_path}")
                    except Exception as e:
                        logger.error(f"이미지 파일 저장 실패 ({image_filename}): {str(e)}")
                except Exception as e:
                    logger.error(f"이미지 처리 중 오류 발생 (페이지 {page_num+1}, 이미지 {img_idx+1}): {str(e)}")
            
            # 페이지 처리 시간 측정
            page_time = time.time() - page_start_time
            logger.info(f"페이지 {page_num+1} 처리 완료: {page_images_count}개 이미지 추출 (소요 시간: {page_time:.2f}초)")
        
        # 문서 닫기
        doc.close()
        
        # 전체 처리 시간 측정
        total_time = time.time() - start_time
        
        # 결과 요약
        logger.info(f"PDF 처리 완료: {len(all_text)} 자의 텍스트, {len(image_paths)}개의 이미지 추출 (소요 시간: {total_time:.2f}초)")
        print(f"추출된 텍스트 길이: {len(all_text)} 자")
        print(f"추출된 이미지 수: {len(image_paths)}개")
        
        # 추출된 텍스트 저장 (디버깅용)
        if all_text and save_debug_info:
            try:
                text_file = os.path.join(logs_dir, f"pymupdf_text_{timestamp}.txt")
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(all_text)
                logger.info(f"추출된 텍스트 저장 완료: {text_file}")
            except Exception as e:
                logger.warning(f"텍스트 저장 실패: {str(e)}")
        
        return all_text, image_paths
        
    except Exception as e:
        error_msg = f"PDF 처리 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        
        # 오류 로그 저장
        try:
            error_log_file = os.path.join(logs_dir, f"pymupdf_error_{timestamp}.log")
            with open(error_log_file, 'w', encoding='utf-8') as f:
                f.write(f"Error: {str(e)}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"PDF file: {pdf_path}\n")
            logger.info(f"오류 로그 저장 완료: {error_log_file}")
        except Exception as log_error:
            logger.warning(f"오류 로그 저장 실패: {str(log_error)}")
            
        return "", []
