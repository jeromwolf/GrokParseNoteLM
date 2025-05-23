from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from PIL import Image
import io
import os
import uuid
import logging
from typing import List, Optional
import time

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Image Analysis Server", description="FastAPI 및 Tesseract OCR을 사용한 이미지 분석 서버")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 임시 저장소 설정
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "이미지 분석 서버가 실행 중입니다", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/analyze/ocr")
async def analyze_image_ocr(file: UploadFile = File(...), lang: str = "eng"):
    """
    이미지에서 텍스트를 추출합니다.
    
    - file: 분석할 이미지 파일
    - lang: OCR 언어 (기본값: eng, 한국어: kor, 한국어+영어: kor+eng)
    """
    try:
        start_time = time.time()
        
        # 이미지 읽기
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # OCR 수행
        text = pytesseract.image_to_string(image, lang=lang)
        
        # 처리 시간 계산
        process_time = time.time() - start_time
        
        return {
            "filename": file.filename,
            "text": text,
            "language": lang,
            "process_time_seconds": process_time
        }
    except Exception as e:
        logger.error(f"OCR 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이미지 처리 중 오류 발생: {str(e)}")

@app.post("/analyze/ocr/batch")
async def analyze_multiple_images(files: List[UploadFile] = File(...), lang: str = "eng"):
    """
    여러 이미지에서 텍스트를 추출합니다.
    
    - files: 분석할 이미지 파일 목록
    - lang: OCR 언어 (기본값: eng, 한국어: kor, 한국어+영어: kor+eng)
    """
    results = []
    
    for file in files:
        try:
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            text = pytesseract.image_to_string(image, lang=lang)
            
            results.append({
                "filename": file.filename,
                "text": text,
                "language": lang
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e),
                "language": lang
            })
    
    return {"results": results}

@app.post("/analyze/ocr/from_path")
async def analyze_image_from_path(image_path: str, lang: str = "eng"):
    logger.debug(f"analyze_image_from_path 호출됨: 경로={image_path}, 언어={lang}")
    """
    서버 로컬 경로에 있는 이미지에서 텍스트를 추출합니다.
    
    - image_path: 분석할 이미지의 전체 경로
    - lang: OCR 언어 (기본값: eng, 한국어: kor, 한국어+영어: kor+eng)
    """
    try:
        logger.debug(f"이미지 경로 확인: {image_path}")
        if not os.path.exists(image_path):
            logger.error(f"이미지 파일을 찾을 수 없음: {image_path}")
            raise HTTPException(status_code=404, detail=f"이미지를 찾을 수 없습니다: {image_path}")
        
        start_time = time.time()
        
        # 이미지 읽기
        logger.debug(f"이미지 파일 열기 시도: {image_path}")
        try:
            image = Image.open(image_path)
            logger.debug(f"이미지 크기: {image.size}, 모드: {image.mode}")
        except Exception as img_err:
            logger.error(f"이미지 열기 실패: {str(img_err)}")
            raise
        
        # OCR 수행
        text = pytesseract.image_to_string(image, lang=lang)
        
        # 처리 시간 계산
        process_time = time.time() - start_time
        
        return {
            "image_path": image_path,
            "text": text,
            "language": lang,
            "process_time_seconds": process_time
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이미지 처리 중 오류 발생: {str(e)}")

@app.post("/analyze/ocr/directory")
async def analyze_directory(directory_path: str, lang: str = "eng", extensions: List[str] = ["jpg", "jpeg", "png", "tiff", "bmp"]):
    """
    지정된 디렉토리에 있는 모든 이미지에서 텍스트를 추출합니다.
    
    - directory_path: 분석할 이미지가 있는 디렉토리 경로
    - lang: OCR 언어 (기본값: eng, 한국어: kor, 한국어+영어: kor+eng)
    - extensions: 처리할 이미지 파일 확장자 목록
    """
    try:
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            raise HTTPException(status_code=404, detail=f"디렉토리를 찾을 수 없습니다: {directory_path}")
        
        results = []
        
        # 디렉토리 내 이미지 파일 검색
        for filename in os.listdir(directory_path):
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ""
            
            if file_ext in extensions:
                file_path = os.path.join(directory_path, filename)
                
                try:
                    image = Image.open(file_path)
                    text = pytesseract.image_to_string(image, lang=lang)
                    
                    results.append({
                        "filename": filename,
                        "path": file_path,
                        "text": text,
                        "language": lang
                    })
                except Exception as e:
                    results.append({
                        "filename": filename,
                        "path": file_path,
                        "error": str(e),
                        "language": lang
                    })
        
        return {"directory": directory_path, "results": results, "file_count": len(results)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"디렉토리 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"디렉토리 처리 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("이미지 분석 서버 시작 중...")
    logger.info(f"Tesseract 버전: {pytesseract.get_tesseract_version()}")
    logger.info(f"지원 언어: {', '.join(pytesseract.get_languages())}")
    uvicorn.run("server:app", host="0.0.0.0", port=5050, reload=True, log_level="debug")
