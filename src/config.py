import os

from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

# Cấu hình API
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.0-flash-thinking-exp-01-21"
# gemini-2.0-flash-thinking-exp-01-21
# gemini-2.0-flash
# gemini-2.5-pro-exp-03-25
# gemini-2.0-pro-exp-02-05

# Thư mục dữ liệu
RETAILER_DATA_DIR = "assets/retailer_data/full_data_for_bs_v3_p3"
COLUMN_DATA_DIR = "assets/column_definition"

