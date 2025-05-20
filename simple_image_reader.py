from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import pytesseract
from PIL import Image
import io
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Simple Image Reader MCP Server")

@app.get("/")
async def read_root():
    return {"message": "Simple Image Reader MCP Server is running"}

@app.post("/read_image")
async def read_image(file: UploadFile = File(...)):
    try:
        # 이미지 파일 읽기
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # 이미지에서 텍스트 추출 (Tesseract OCR 사용)
        text = pytesseract.image_to_string(image)
        
        logger.info(f"이미지에서 텍스트를 성공적으로 추출했습니다. 크기: {len(text)}자")
        
        return {
            "status": "success",
            "text": text.strip(),
            "filename": file.filename,
            "size": len(contents)
        }
    except Exception as e:
        logger.error(f"이미지 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
