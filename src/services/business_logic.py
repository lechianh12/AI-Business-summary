# business_logic.py
import os

import google.generativeai as genai

from src.config import (
    MODEL_NAME,
    RETAILER_DATA_DIR,
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
        raise ValueError(f"retailer_id không hợp lệ: {retailer_id}")

    csv_filename = RETAILER_OPTIONS[retailer_id]
    csv_path = f"{RETAILER_DATA_DIR}/{csv_filename}"

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File CSV không tồn tại: {csv_path}")
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        file_content = f.read()

    # df_check = pd.read_csv(csv_path)
    # check_data(df_check)
    df = read_csv_content(file_content)
    time_period_value = TIME_PERIOD_OPTIONS[time_period]
    screen_value = SCREEN_OPTIONS[screen]
    filtered_by_time_df = filter_by_timeframe(df, time_period_value)
    processed_data = preprocess_csv_data(filtered_by_time_df)
    columns_data = get_columns_for_screen(screen_value)
    filtered_data, filter_df = process_csv_for_screen(processed_data, columns_data)
    csv_text = filtered_data["csv_text"]

    # Prepare prompt
    user_input = f"Hãy phân tích cho tôi tình hình kinh doanh trong {time_period} của cửa hàng, chú ý các chỉ số tăng giảm so với kỳ trước nếu có."
    system_instructions = generate_retail_system_prompt(screen_value)
    full_prompt = f"{system_instructions}\n\nDữ liệu CSV:\n{csv_text}\n\n\n\nUser Input: {user_input}"
    return full_prompt


def get_llm_streaming_response(full_prompt, api_key):
    """
    Gọi LLM và trả về generator cho streaming response.
    """
    genai.configure(api_key=api_key)
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
