from fastapi import FastAPI, File, UploadFile, Form, Depends
import PyPDF2
from enum import Enum

import os

from typing import Annotated, List, Optional


import uvicorn
import csv
from google import genai
from dotenv import load_dotenv
import os
from typing import Optional, List, Union
from fastapi import HTTPException
from typing import Annotated
import io
from utils import extract_text_from_csv
import time as time_module




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
    files: Optional[List[UploadFile]] = File(None)
):



    start_time = time_module.time()

    all_texts = []

    text = ""
    for file in files:
        text = extract_text_from_csv(file)
        all_texts.append(f"=== {file.filename} ===\n{text}")




    # Gộp nội dung tất cả các file
    combined_text = "\n\n".join(all_texts)


      
    llm_response = client.models.generate_content(model=os.getenv("GEMINI_MODEL"), 
                                                    contents=f"{prompt}\n\nContext from uploaded file:\n{combined_text}")
  




    end_time = time_module.time()  
    print(f"Time taken: {end_time - start_time} seconds")
    return {
        "response": llm_response.text,
        "text": text
    }


@app.post("/khách_hàng")
async def khachhang(
    time_filter: FilterTime = Form(...),
    prompt: str = Form(...),
    files: Optional[List[UploadFile]] = File(None)
):



    start_time = time_module.time()

    all_texts = []

    text = ""
    for file in files:
        text = extract_text_from_csv(file)
        all_texts.append(f"=== {file.filename} ===\n{text}")




    # Gộp nội dung tất cả các file
    combined_text = "\n\n".join(all_texts)


      
    llm_response = client.models.generate_content(model=os.getenv("GEMINI_MODEL"), 
                                                    contents=f"{prompt}\n\nContext from uploaded file:\n{combined_text}")
  




    end_time = time_module.time()  
    print(f"Time taken: {end_time - start_time} seconds")
    return {
        "response": llm_response.text,
        "text": text
    }


@app.post("/Kinh_doanh")
async def kinhdoanh(
    time_filter: FilterTime = Form(...),
    prompt: str = Form(...),
    files: Optional[List[UploadFile]] = File(None)
):


    start_time = time_module.time()

    all_texts = []

    text = ""
    for file in files:
        text = extract_text_from_csv(file)
        all_texts.append(f"=== {file.filename} ===\n{text}")




    # Gộp nội dung tất cả các file
    combined_text = "\n\n".join(all_texts)


      
    llm_response = client.models.generate_content(model=os.getenv("GEMINI_MODEL"), 
                                                    contents=f"{prompt}\n\nContext from uploaded file:\n{combined_text}")
  




    end_time = time_module.time()  
    print(f"Time taken: {end_time - start_time} seconds")
    return {
        "response": llm_response.text,
        "text": text
    }









if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=7000, reload=True)
