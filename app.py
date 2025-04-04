from fastapi import FastAPI, File, UploadFile, Form, Depends
import PyPDF2
import uvicorn
import csv
from google import genai
from dotenv import load_dotenv
import os
from typing import Optional, List, Union
from fastapi import HTTPException
from typing import Annotated
import io
from utils import extract_text_from_pdf, extract_text_from_csv, extract_text_from_txt
import time



load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()


@app.post("/hello")
async def hello(
    prompt: str = Form(...),
    files: Optional[List[UploadFile]] = File(None)
):

    start_time = time.time()
    all_texts = []

    text = ""
    if files is not None:
        for file in files:
            if file.filename.endswith('.pdf'):
                text = extract_text_from_pdf(file)
            elif file.filename.endswith('.csv'):
                text = extract_text_from_csv(file)
            elif file.filename.endswith('.txt'):
                text = extract_text_from_txt(file)
            else:
                raise Exception(f"Unsupported file format: {file.filename}. Please upload a PDF, CSV, or TXT file.")

            all_texts.append(f"=== {file.filename} ===\n{text}")




    # Gộp nội dung tất cả các file
    combined_text = "\n\n".join(all_texts)


    if combined_text is not None:           
        llm_response = client.models.generate_content(model=os.getenv("GEMINI_MODEL"), 
                                                    contents=f"{prompt}\n\nContext from uploaded file:\n{combined_text}")
    elif combined_text == None:
        llm_response = client.models.generate_content(model=os.getenv("GEMINI_MODEL"), 
                                                    contents=f"{prompt}")



    end_time = time.time()  
    print(f"Time taken: {end_time - start_time} seconds")
    return {
        "response": llm_response.text,
        "text": text
    }




if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=7000, reload=True)
