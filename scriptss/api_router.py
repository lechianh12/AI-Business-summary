import os
import time
import google.generativeai as genai
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse, StreamingResponse

# Import nội bộ
from scriptss.config import API_KEY, MODEL_NAME, RETAILER_DATA_DIR
from scriptss.prompt import generate_retail_system_prompt
from scriptss.schema import RETAILER_OPTIONS, SCREEN_OPTIONS, TIME_PERIOD_OPTIONS
from scriptss.utils import (
    filter_by_timeframe,
    get_columns_for_screen,
    preprocess_csv_data,
    print_response_time,
    process_csv_for_screen,
    read_csv_content,
    set_null_values_for_previous_periods,
    validate_data,
    drop_null_top10_row,
)

# Tạo router
router = APIRouter()

# Cấu hình Google Generative AI
genai.configure(api_key=API_KEY)

def stream_response_text(text: str):
    """ Generator để stream từng 10 ký tự của phản hồi """
    for i in range(0, len(text), 20):  # Chia ra các phần có 10 ký tự mỗi lần
        yield text[i:i + 20]
        time.sleep(0.1)  # Đảm bảo có độ trễ giữa các phần để mô phỏng việc phản hồi dần dần

@router.get("/response", response_class=PlainTextResponse)
async def response(
    retailer_id: str = Query(..., enum=list(RETAILER_OPTIONS.keys())),
    screen: str = Query(..., enum=list(SCREEN_OPTIONS.keys())),
    time_period: str = Query(..., enum=list(TIME_PERIOD_OPTIONS.keys())),
):
    start_time_total = time.time()

    try:
        # Kiểm tra retailer_id
        if retailer_id not in RETAILER_OPTIONS:
            raise HTTPException(status_code=400, detail=f"retailer_id không hợp lệ: {retailer_id}")

        csv_filename = RETAILER_OPTIONS[retailer_id]
        csv_path = f"{RETAILER_DATA_DIR}/{csv_filename}"

        # Kiểm tra file tồn tại
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=400, detail=f"File CSV không tồn tại: {csv_path}")

        print(f"[DEBUG] Đang đọc file CSV: {csv_path}")

        with open(csv_path, "r", encoding="utf-8-sig") as f:
            file_content = f.read()

        try:
            df = read_csv_content(file_content)
            print("[DEBUG] DataFrame gốc:")
            print(df.head())

            # Kiểm tra dữ liệu
            # bool_check = validate_data(df)
            # if not bool_check:
            #     raise HTTPException(status_code=400, detail="Dữ liệu tính sai")

            print("[DEBUG] Dữ liệu hợp lệ.")
            df = drop_null_top10_row(df)

            time_period_value = TIME_PERIOD_OPTIONS[time_period]
            screen_value = SCREEN_OPTIONS[screen]

            # Lọc dữ liệu theo thời gian
            filtered_by_time_df = filter_by_timeframe(df, time_period_value)
            filtered_by_time_df = set_null_values_for_previous_periods(filtered_by_time_df)
            processed_data = preprocess_csv_data(filtered_by_time_df)

            # Lấy cột theo screen
            columns_data = get_columns_for_screen(screen_value)
            filtered_data = process_csv_for_screen(processed_data, columns_data)

            csv_text = filtered_data["csv_text"]

            print("[DEBUG] CSV sau xử lý:")
            print(csv_text[:500])  # Chỉ in 500 ký tự đầu tiên cho gọn

        except Exception as e:
            print(f"[DEBUG] Lỗi xử lý CSV: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Lỗi khi xử lý file CSV: {str(e)}")

        # Tạo prompt người dùng
        user_input = f"Hãy phân tích cho tôi tình hình kinh doanh trong {time_period} của cửa hàng, chú ý các chỉ số tăng giảm so với kỳ trước nếu có."

        system_prompt = generate_retail_system_prompt(screen_value)
        full_prompt = (
            f"{system_prompt}\n\nDữ liệu CSV:\n{csv_text}\n\nUser Input: {user_input}"
        )

        with open("tests/test_output.txt", "w", encoding="utf-8-sig") as f:
            f.write(full_prompt)

        print("[DEBUG] Prompt gửi đến Gemini:")
        print(full_prompt[:500])  # In giới hạn

        # Gọi model
        try:
            start_time_model = time.time()

            model = genai.GenerativeModel(MODEL_NAME)
            response = model.generate_content(contents=full_prompt)

            end_time_model = time.time()
            print_response_time("Model phản hồi", start_time_model, end_time_model)

            print("[DEBUG] Phản hồi từ Gemini:")
            print(response.text[:500])  # In phần đầu

        except Exception as model_error:
            print(f"[DEBUG] Lỗi từ Gemini API: {str(model_error)}")
            raise HTTPException(status_code=500, detail=f"Lỗi từ mô hình AI: {str(model_error)}")

        end_time_total = time.time()
        print_response_time("Thời gian phản hồi tổng", start_time_total, end_time_total)

        # Trả về dữ liệu theo từng 10 ký tự một lần
        return StreamingResponse(stream_response_text(response.text), media_type="text/plain")

    except Exception as e:
        print(f"[DEBUG] Lỗi tổng thể: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý yêu cầu: {str(e)}")
