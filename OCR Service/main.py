from fastapi import FastAPI, UploadFile, File
import shutil
import uuid
import os

from ocr_engine import OCREngine

app = FastAPI()

ocr_engine = OCREngine()

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)


@app.post("/ocr")
async def run_ocr(file: UploadFile = File(...)):

    temp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.jpg")

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = ocr_engine.extract_text(temp_path)

    os.remove(temp_path)

    return {
        "success": True,
        "text": text
    }