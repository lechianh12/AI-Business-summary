import os
import time as time_module
from enum import Enum
from typing import List, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from google import genai
from scripts.readfiles import extract_text_from_csv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()


class FilterTime(str, Enum):
    option1 = "7"
    option2 = "30"
    option3 = "tháng"


@app.post("/Sản_phẩm")
async def sanpham(
    time_filter: FilterTime = Form(...),
    prompt: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
):

    start_time = time_module.time()

    all_texts = []

    text = ""
    for file in files:
        text = extract_text_from_csv(file)
        all_texts.append(f"=== {file.filename} ===\n{text}")

    # Gộp nội dung tất cả các file
    combined_text = "\n\n".join(all_texts)

    llm_response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL"),
        contents=f"{prompt}\n\nContext from uploaded file:\n{combined_text}",
    )

    end_time = time_module.time()
    print(f"Time taken: {end_time - start_time} seconds")
    return {"response": llm_response.text, "text": text}


@app.post("/khách_hàng")
async def khachhang(
    time_filter: FilterTime = Form(...),
    prompt: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
):

    start_time = time_module.time()

    all_texts = []

    text = ""
    for file in files:
        text = extract_text_from_csv(file)
        all_texts.append(f"=== {file.filename} ===\n{text}")

    # Gộp nội dung tất cả các file
    combined_text = "\n\n".join(all_texts)

    llm_response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL"),
        contents=f"{prompt}\n\nContext from uploaded file:\n{combined_text}",
    )

    end_time = time_module.time()
    print(f"Time taken: {end_time - start_time} seconds")
    return {"response": llm_response.text, "text": text}


@app.post("/Kinh_doanh")
async def kinhdoanh(
    time_filter: FilterTime = Form(...),
    prompt: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
):

    start_time = time_module.time()

    all_texts = []

    text = ""
    for file in files:
        text = extract_text_from_csv(file)
        all_texts.append(f"=== {file.filename} ===\n{text}")

    # Gộp nội dung tất cả các file
    combined_text = "\n\n".join(all_texts)

    llm_response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL"),
        contents=f"{prompt}\n\nContext from uploaded file:\n{combined_text}",
    )

    end_time = time_module.time()
    print(f"Time taken: {end_time - start_time} seconds")
    return {"response": llm_response.text, "text": text}


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=7000, reload=True)
