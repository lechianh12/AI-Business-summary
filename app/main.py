import os
import time
from typing import List, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from google import genai
from utils import (
    extract_text_from_csv,
    extract_text_from_image,
    extract_text_from_pdf,
    extract_text_from_txt,
)

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()


@app.post("/hello")
async def hello(
    prompt: str = Form(...), files: Optional[List[UploadFile]] = File(None)
):

    start_time = time.time()

    all_texts = []

    text = ""
    is_image = False
    if files is not None:
        for file in files:
            if file.filename.endswith(".pdf"):
                text = extract_text_from_pdf(file)
            elif file.filename.endswith(".csv"):
                text = extract_text_from_csv(file)
            elif file.filename.endswith(".txt"):
                text = extract_text_from_txt(file)
            elif file.filename.endswith(("png", "jpg", "jpeg", "bmp")):
                image = await extract_text_from_image(file)
                is_image = True

            else:
                raise Exception(
                    f"Unsupported file format: {file.filename}. Please upload a PDF, CSV, or TXT file."
                )

            all_texts.append(f"=== {file.filename} ===\n{text}")

    # Gộp nội dung tất cả các file
    combined_text = "\n\n".join(all_texts)

    if combined_text is not None and is_image == False:
        llm_response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL"),
            contents=f"{prompt}\n\nContext from uploaded file:\n{combined_text}",
        )
    elif combined_text == None and is_image == False:
        llm_response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL"), contents=f"{prompt}"
        )
    elif combined_text is not None and is_image == True:
        print(
            "Now is reading image-----------------------------------------------------------"
        )
        llm_response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL"), contents=[prompt, image]
        )

    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
    return {"response": llm_response.text, "text": text}


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=7000, reload=True)
