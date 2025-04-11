import os

import google.generativeai as genai
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from scripts.config import API_KEY, MODEL_NAME
from scripts.prompt import generate_retail_system_prompt
from scripts.utils import (
    get_columns_for_screen,
    preprocess_csv_data,
    process_csv_for_screen,
    read_csv_content,
)

# Tạo router API
router = APIRouter()

# Cấu hình Google Generative AI
genai.configure(api_key=API_KEY)

# Định nghĩa các lựa chọn
RETAILER_OPTIONS = {
    "285727": "retailer_285727.csv",
    "541173": "retailer_541173.csv",
    "500577674": "retailer_500577674.csv",
}

TIME_PERIOD_OPTIONS = {
    "month_current": "Tháng này",
    "days_7": "7 ngày gần nhất",
    "days_30": "30 ngày gần nhất",
}

SCREEN_OPTIONS = {
    "product_overview": "Tổng quan hàng hóa",
    "customer_overview": "Tổng quan khách hàng",
}


@router.get("/response", response_class=PlainTextResponse)
async def response(
    retailer_id: str = Query(
        ..., enum=list(RETAILER_OPTIONS.keys())
    ),
    time_period: str = Query(
        ..., enum=list(TIME_PERIOD_OPTIONS.keys())
    ),
    screen: str = Query(
        ..., enum=list(SCREEN_OPTIONS.keys())
    ),
):
    try:
        # Xác định file CSV tương ứng với retailer_id
        if retailer_id not in RETAILER_OPTIONS:
            raise HTTPException(
                status_code=400, detail=f"retailer_id không hợp lệ: {retailer_id}"
            )

        csv_filename = RETAILER_OPTIONS[retailer_id]
        csv_path = f"assets/retailer_data/{csv_filename}"

        # Kiểm tra file CSV tồn tại
        if not os.path.exists(csv_path):
            raise HTTPException(
                status_code=400, detail=f"File CSV không tồn tại: {csv_path}"
            )

        # Đọc nội dung file CSV
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            file_content = f.read()

        # Đọc file CSV thành DataFrame
        try:
            df = read_csv_content(file_content)

            # Tiền xử lý dữ liệu
            processed_data = preprocess_csv_data(df)

            # Xử lý dữ liệu dựa trên lựa chọn màn hình
            columns_data = get_columns_for_screen(screen)
            filtered_data = process_csv_for_screen(processed_data, columns_data)

            # Lấy text CSV đã được xử lý
            csv_text = filtered_data["csv_text"]
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Lỗi khi xử lý file CSV: {str(e)}"
            )

        # Tạo user_input dựa trên lựa chọn thời gian
        time_period_text = TIME_PERIOD_OPTIONS[time_period]
        user_input = f"Hãy phân tích cho tôi tình hình kinh doanh trong {time_period_text} của cửa hàng"

        # Kết hợp system prompt và nội dung vào một chuỗi
        screen_text = SCREEN_OPTIONS[screen]
        system_prompt = generate_retail_system_prompt(screen)
        full_prompt = (
            f"{system_prompt}\n\nDữ liệu CSV:\n{csv_text}\n\nUser Input: {user_input}"
        )

        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(
            contents=full_prompt,
        )

        # Trả về phản hồi của mô hình dạng text
        return response.text

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý yêu cầu: {str(e)}")
