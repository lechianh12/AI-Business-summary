from typing import Optional

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile

app = FastAPI()


@app.post("/process-item/")
async def process_item(
    item_id: str = Form(...),  # Một trường dữ liệu khác bắt buộc từ form
    file: Optional[UploadFile] = File(None),  # File là tùy chọn, mặc định là None
):
    """
    Endpoint xử lý item, cho phép upload file tùy chọn.
    """
    if file:
        # Nếu người dùng có upload file
        content = await file.read()
        # Xử lý file ở đây (ví dụ: lưu file, đọc nội dung, ...)
        return {
            "item_id": item_id,
            "file_uploaded": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "message": f"File '{file.filename}' processed successfully.",
        }
    else:
        # Nếu người dùng không upload file
        return {
            "item_id": item_id,
            "file_uploaded": False,
            "message": "No file was uploaded, but item processed.",
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
