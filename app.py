import os
from typing import Annotated, List, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from google import genai

from utils import extract_text_from_csv, extract_text_from_pdf, extract_text_from_txt

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()


@app.post("/hello")
async def hello(
    prompt: str = Form(...), files: Optional[List[UploadFile]] = File(None)
):

    all_texts = []

    text = ""
    print("abc")
    if files is not None:
        for file in files:
            if file.filename.endswith(".pdf"):
                text = extract_text_from_pdf(file)
            elif file.filename.endswith(".csv"):
                text = extract_text_from_csv(file)
            elif file.filename.endswith(".txt"):
                text = extract_text_from_txt(file)
            else:
                raise Exception(
                    f"Unsupported file format: {file.filename}. Please upload a PDF, CSV, or TXT file."
                )

            all_texts.append(f"=== {file.filename} ===\n{text}")

    # Gộp nội dung tất cả các file
    combined_text = "\n\n".join(all_texts)

    if combined_text is not None:
        llm_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"{prompt}\n\nContext from uploaded file:\n{combined_text}",
        )
    elif combined_text == None:
        llm_response = client.models.generate_content(
            model="gemini-2.0-flash", contents=f"{prompt}"
        )

    return {"response": llm_response.text, "text": text}


@app.post("/uploadfiles/")
async def upload_files(files: Annotated[bytes, List[UploadFile], File(...)] = None):
    if files is None:
        return {"message": "No files uploaded"}
    return {"file_count": len(files), "filenames": [file.filename for file in files]}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7000)
