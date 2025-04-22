import asyncio
import os
import sys

import google.generativeai as genai
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse, StreamingResponse

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import nội bộ
from scriptss.config import API_KEY, MODEL_NAME, RETAILER_DATA_DIR
from scriptss.prompt import generate_retail_system_prompt
from scriptss.schema import RETAILER_OPTIONS, SCREEN_OPTIONS, TIME_PERIOD_OPTIONS
from scriptss.utils import (
    filter_by_timeframe,
    get_columns_for_screen,
    preprocess_csv_data,
    process_csv_for_screen,
    read_csv_content,
)

# Tạo router
router = APIRouter()

# Cấu hình Google Generative AI
genai.configure(api_key=API_KEY)


async def stream_response(generator):
    """Async generator wrapper for streaming response"""
    try:
        for chunk in generator:
            if hasattr(chunk, "text"):
                yield chunk.text
                await asyncio.sleep(0.05)  # Small delay for smoother streaming
    except Exception as e:
        print(f"Error in streaming: {e}")
        yield f"\nError occurred during streaming: {str(e)}"


@router.get("/response", response_class=PlainTextResponse)
async def response(
    retailer_id: str = Query(..., enum=list(RETAILER_OPTIONS.keys())),
    screen: str = Query(..., enum=list(SCREEN_OPTIONS.keys())),
    time_period: str = Query(..., enum=list(TIME_PERIOD_OPTIONS.keys())),
):

    try:
        # Kiểm tra retailer_id
        if retailer_id not in RETAILER_OPTIONS:
            raise HTTPException(
                status_code=400, detail=f"retailer_id không hợp lệ: {retailer_id}"
            )

        csv_filename = RETAILER_OPTIONS[retailer_id]
        csv_path = f"{RETAILER_DATA_DIR}/{csv_filename}"

        # Kiểm tra file tồn tại
        if not os.path.exists(csv_path):
            raise HTTPException(
                status_code=400, detail=f"File CSV không tồn tại: {csv_path}"
            )

        with open(csv_path, "r", encoding="utf-8-sig") as f:
            file_content = f.read()

        try:
            df = read_csv_content(file_content)

            # Kiểm tra dữ liệu
            # bool_check = validate_data(df)
            # if not bool_check:
            #     raise HTTPException(status_code=400, detail="Dữ liệu tính sai")
            # print("[DEBUG] Dữ liệu hợp lệ.")

            time_period_value = TIME_PERIOD_OPTIONS[time_period]
            screen_value = SCREEN_OPTIONS[screen]

            # Lọc dữ liệu theo thời gian
            filtered_by_time_df = filter_by_timeframe(df, time_period_value)
            # filtered_by_time_df = set_null_values_for_previous_periods(
            #     filtered_by_time_df
            # )
            processed_data = preprocess_csv_data(filtered_by_time_df)

            # Lấy cột theo screen
            columns_data = get_columns_for_screen(screen_value)
            filtered_data, filter_df = process_csv_for_screen(
                processed_data, columns_data
            )

            # print(
            #     "======================================================================================"
            # )
            # filter_df, json_data = df_to_clean_json(filter_df)
            # print("[DEBUG] Dữ liệu JSON:")
            # print(json_data)
            # print(
            #     "======================================================================================"
            # )

            csv_text = filtered_data["csv_text"]

            # print("[DEBUG] CSV sau xử lý:")
            # print(csv_text[:500])  # Chỉ in 500 ký tự đầu tiên cho gọn

        except Exception as e:
            print(f"[DEBUG] Lỗi xử lý CSV: {str(e)}")
            raise HTTPException(
                status_code=400, detail=f"Lỗi khi xử lý file CSV: {str(e)}"
            )

        # Tạo prompt người dùng
        user_input = f"Hãy phân tích cho tôi tình hình kinh doanh trong {time_period} của cửa hàng, chú ý các chỉ số tăng giảm so với kỳ trước nếu có."

        # Get the system prompt
        system_instructions = generate_retail_system_prompt(screen_value)

        # Create the combined prompt
        full_prompt = f"{system_instructions}\n\nDữ liệu CSV:\n{csv_text}\n\n\n\nUser Input: {user_input}"

        # Save the full prompt for reference
        with open("tests/test_output.txt", "w", encoding="utf-8-sig") as f:
            f.write(full_prompt)

        try:
            model = genai.GenerativeModel(MODEL_NAME)

            # Generate streaming response
            response_generator = model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.75,
                    top_p=0.95,
                ),
                stream=True,
            )

            # Log token usage information (if available)
            try:
                print("\nThông tin về việc sử dụng token:")
                print(response_generator.usage_metadata)
            except AttributeError:
                print("Note: usage_metadata not available in streaming mode")

            # Return streaming response
            return StreamingResponse(
                stream_response(response_generator),
                media_type="text/plain",
            )

        except Exception as model_error:
            print(f"[DEBUG] Lỗi từ Gemini API: {str(model_error)}")
            raise HTTPException(
                status_code=500, detail=f"Lỗi từ mô hình AI: {str(model_error)}"
            )

    except Exception as e:
        print(f"[DEBUG] Lỗi tổng thể: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý yêu cầu: {str(e)}")
