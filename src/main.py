import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from scripts.api_router import router

app = FastAPI(
    title="Business Summary API",
    version="1.0.0",
)

# Thêm middleware CORS để cho phép gọi API từ các nguồn khác
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
