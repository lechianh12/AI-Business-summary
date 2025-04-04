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

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()


@app.post("/hello")
async def hello(
    prompt: str = Form(...),
    files: Optional[List[UploadFile]] = File(None)
):


    all_texts = []

    text = ""
    print("abc")
    if files is not None:
        for file in files:
            if file.filename.endswith('.pdf'):
                pdf_reader = PyPDF2.PdfReader(file.file)
                text = "".join([page.extract_text() or "" for page in pdf_reader.pages])
            elif file.filename.endswith('.csv'):
                text = "\n".join([",".join(row) for row in csv.reader(file.file.read().decode().splitlines())])
            elif file.filename.endswith('.txt'):
                text = file.read().decode()
            else:
                raise Exception(f"Unsupported file format: {file.filename}. Please upload a PDF, CSV, or TXT file.")

            all_texts.append(f"=== {file.filename} ===\n{text}")




    # Gộp nội dung tất cả các file
    combined_text = "\n\n".join(all_texts)


    if combined_text is not None:           
        llm_response = client.models.generate_content(model="gemini-2.0-flash", 
                                                    contents=f"{prompt}\n\nContext from uploaded file:\n{combined_text}")
    elif combined_text == None:
        llm_response = client.models.generate_content(model="gemini-2.0-flash", 
                                                    contents=f"{prompt}")


    return {
        "response": llm_response.text,
        "text": text
    }

@app.post("/uploadfiles/")
async def upload_files(files: Annotated[bytes, List[UploadFile], File(...)]= None):
    if files is None:
        return {"message": "No files uploaded"}
    return {"file_count": len(files), "filenames": [file.filename for file in files]}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7000)
