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

# Thư mục dữ liệu
RETAILER_DATA_DIR = "assets/retailer_data/product_for_bs_v2"
COLUMN_DATA_DIR = "assets/column_definition"


#Danh sách các cột cần xử lý null
COLUMNS_TO_SET_NULL = [
        "Top_product_rev",
        "top_product_rev",
        "Top_product_quantity",
        "top_product_quantity",
        "Top_product_profit",
        "top_product_profit",
        "Last_product_quantity",
        "last_product_quantity",
        "Last_product_rev",
        "last_product_rev",
        "Last_product_profit",
        "last_product_profit",
        "Top_group_quantity",
        "top_group_quantity",
        "Top_group_rev",
        "top_group_rev",
        "Top_group_profit",
        "top_group_profit",
        "Last_group_quantity",
        "last_group_quantity",
        "Last_group_rev",
        "last_group_rev",
        "Last_group_profit",
        "last_group_profit",
]
