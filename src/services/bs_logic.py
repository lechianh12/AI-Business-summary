import os
from fastapi import HTTPException
import google.generativeai as genai

from src.config import (
    API_KEY,
    MODEL_NAME,
    RETAILER_DATA_DIR,
)
from src.models.schema import (
    RETAILER_OPTIONS,
    SCREEN_OPTIONS,
    TIME_PERIOD_OPTIONS,
)
from src.utils.preprocessing import (
    filter_by_timeframe,
    get_columns_for_screen,
    preprocess_csv_data,
    process_csv_for_screen,
    read_csv_content,
)
from src.utils.prompt import generate_retail_system_prompt


def prepare_llm_prompt(retailer_id, screen, time_period):
    # Process data
    if retailer_id not in RETAILER_OPTIONS:
        raise HTTPException(
            status_code=400, detail=f"retailer_id không hợp lệ: {retailer_id}"
        )

    csv_filename = RETAILER_OPTIONS[retailer_id]
    csv_path = f"{RETAILER_DATA_DIR}/{csv_filename}"

    if not os.path.exists(csv_path):
        raise HTTPException(
            status_code=400, detail=f"File CSV không tồn tại: {csv_path}"
        )

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        file_content = f.read()

    try:
        # Đọc file csv
        df = read_csv_content(file_content)
        
        # Lọc dữ liệu theo thời gian
        time_period_value = TIME_PERIOD_OPTIONS[time_period]
        filtered_by_time_df = filter_by_timeframe(df, time_period_value)

        # Xử lý dữ liệu
        processed_data = preprocess_csv_data(filtered_by_time_df)

        # Lấy cột theo screen
        screen_value = SCREEN_OPTIONS[screen]
        columns_data = get_columns_for_screen(screen_value)
        filtered_data, filter_df = process_csv_for_screen(
            processed_data, columns_data
        )
        csv_text = filtered_data["csv_text"]

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Lỗi khi xử lí dữ liệu CSV: {str(e)}"
        )

    try:
        # Tạo user_prompt
        user_input = f"Hãy phân tích cho tôi tình hình kinh doanh trong {time_period} của cửa hàng, chú ý các chỉ số tăng giảm so với kỳ trước nếu có."

        # Tạo system_prompt
        system_instructions = generate_retail_system_prompt(screen_value)

        # Tạo prompt cuối cùng
        full_prompt = f"{system_instructions}\n\nDữ liệu CSV:\n{csv_text}\n\n\n\nUser Input: {user_input}"
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Lỗi khi tạo full prompt: {str(e)}"
        )
    
    # Lưu prompt cuối cùng vào file test -> dùng để debug
    with open("tests/test_output.txt", "w", encoding="utf-8-sig") as f:
        f.write(full_prompt)

    return full_prompt


def get_llm_response(full_prompt):
    try:
        # Cấu hình Google Generative AI
        genai.configure(api_key=API_KEY)

        model = genai.GenerativeModel(MODEL_NAME)
        response_generator = model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.75,
                top_p=0.95,
            ),
            stream=True,
        )
        return response_generator
    except Exception as model_error:
        raise HTTPException(
            status_code=500, detail=f"Lỗi từ mô hình AI: {str(model_error)}"
        )
    

