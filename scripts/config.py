import os

from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

# Cấu hình API
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.0-flash-thinking-exp-01-21"
# gemini-2.0-flash-thinking-exp-01-21
# gemini-2.0-flash
