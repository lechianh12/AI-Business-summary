import os

import google.generativeai as genai
from fastapi import HTTPException

from src.config import (
    API_KEY,
    CSV_AGG_PATH,
    CSV_RETAILER_DIR,
    MODEL_NAME,
)
from src.models.schema import (
    RETAILER_OPTIONS,
    SCREEN_OPTIONS,
    SCREEN_TO_CSV_MAP,
    TIME_PERIOD_OPTIONS,
)
from src.utils.preprocessing import (
    filter_by_timeframe,
    get_columns_for_screen,
    process_csv_for_screen,
    read_csv_content,
    validate_data,
)
from src.utils.prompt import generate_retail_system_prompt
from src.utils.splitfile import check_retailer_data_exists, split_csv_by_retailer_id

# Định nghĩa mapping giữa màn hình và file CSV tương ứng


# Chuẩn bị data để gửi cho model
def prepare_llm_prompt(retailer_id, screen, time_period):
    # Kiểm tra và chuẩn bị dữ liệu trước khi xử lý
    if not check_retailer_data_exists():
        print("Dữ liệu retailer chưa tồn tại. Tiến hành chia file...")
        split_csv_by_retailer_id(CSV_AGG_PATH, CSV_RETAILER_DIR)
    else:
        print("Dữ liệu retailer đã tồn tại. Bỏ qua bước chia file.")

    # Process data
    if retailer_id not in RETAILER_OPTIONS:
        raise HTTPException(
            status_code=400, detail=f"retailer_id không hợp lệ: {retailer_id}"
        )

    # Chuyển đổi screen thành giá trị từ SCREEN_OPTIONS
    if screen not in SCREEN_OPTIONS:
        raise HTTPException(status_code=400, detail=f"screen không hợp lệ: {screen}")
    screen_value = SCREEN_OPTIONS[screen]

    # Lấy tên file CSV dựa vào loại màn hình
    if screen_value not in SCREEN_TO_CSV_MAP:
        raise HTTPException(
            status_code=400, detail=f"Không tìm thấy file CSV cho màn hình: {screen}"
        )
    csv_filename = SCREEN_TO_CSV_MAP[screen_value]

    # Tạo đường dẫn đến folder retailer_id cụ thể
    retailer_folder = f"retailer_{retailer_id}"
    csv_path = f"{CSV_RETAILER_DIR}/{retailer_folder}/{csv_filename}"

    if not os.path.exists(csv_path):
        raise HTTPException(
            status_code=400, detail=f"Đường dẫn CSV không tồn tại: {csv_path}"
        )

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        file_content = f.read()

    try:
        # Đọc file csv
        df = read_csv_content(file_content)

        # Kiểm tra dữ liệu DataFrame
        validate_data(df)


        # Lọc dữ liệu theo thời gian nếu có cột timeframe_type
        if "timeframe_type" in df.columns:
            time_period_value = TIME_PERIOD_OPTIONS[time_period]
            filtered_df = filter_by_timeframe(df, time_period_value.lower())
        else:
            filtered_df = df

        # Đóng gói DataFrame(rows) thành dict -> Luồng cũ để process data thì dữ liệu cần dạng dict
        rows_data = {
            "dataframe": filtered_df,
            "csv_text": filtered_df.to_csv(index=False),
        }

        # Lấy cột theo screen
        columns_data = get_columns_for_screen(screen_value)

        # Xử lý dữ liệu
        filtered_data, filter_df = process_csv_for_screen(rows_data, columns_data)
        csv_text = filtered_data["csv_text"]

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Lỗi khi xử lí dữ liệu CSV: {str(e)}"
        )

    try:
        # Tạo user_prompt, điều chỉnh theo trường hợp có hoặc không có lọc thời gian
        if "timeframe_type" in df.columns:
            user_input = f"Hãy phân tích cho tôi tình hình kinh doanh trong {time_period} của cửa hàng, chú ý các chỉ số tăng giảm so với kỳ trước nếu có."
        else:
            if screen_value == "stock":
                user_input = "Hãy phân tích cho tôi tình hình tồn kho hiện tại của cửa hàng, chú ý các sản phẩm tồn kho lâu ngày và giá trị tồn kho."
            elif screen_value == "customer_segmentation":
                user_input = "Hãy phân tích cho tôi phân loại khách hàng hiện tại của cửa hàng, chú ý các nhóm khách hàng quan trọng và giá trị mang lại."


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
                response_mime_type="text/plain",
                # response_schema = list[Recipe],
            ),
            stream=True,
        )
        return response_generator
    except Exception as model_error:
        raise HTTPException(
            status_code=400, detail=f"Lỗi từ mô hình AI: {str(model_error)}"
        )
