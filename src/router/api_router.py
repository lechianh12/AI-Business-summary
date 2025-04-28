import asyncio
import os
import sys
import time

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse, StreamingResponse

from src.services.bs_logic import get_llm_response, prepare_llm_prompt

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import nội bộ
from src.models.schema import RETAILER_OPTIONS, SCREEN_OPTIONS, TIME_PERIOD_OPTIONS

# Tạo router
router = APIRouter()


async def stream_response(generator):
    try:
        for chunk in generator:
            if hasattr(chunk, "text"):
                yield chunk.text
                await asyncio.sleep(0.05)  # Small delay for smoother streaming
    except Exception as e:
        yield f"\nLỗi xảy ra trong quá trình streaming: {str(e)}"


# class ResponseRequest(BaseModel):
#     retailer_id: str = Query(..., enum=list(RETAILER_OPTIONS.keys()))
#     screen: str = Query(..., enum=list(SCREEN_OPTIONS.keys()))
#     time_period: str = Query(..., enum=list(TIME_PERIOD_OPTIONS.keys()))

 
@router.get("/response", response_class=PlainTextResponse)
async def response(
    retailer_id: str = Query(..., enum=list(RETAILER_OPTIONS.keys())),
    screen: str = Query(..., enum=list(SCREEN_OPTIONS.keys())),
    time_period: str = Query(..., enum=list(TIME_PERIOD_OPTIONS.keys())),
):

    try:
        start_time = time.time()
        # strict time period cho screen "Phân loại khách hàng"
        if screen == "Phân loại khách hàng":
            time_period = "Tháng này"
        else:
            time_period = time_period

        full_prompt = prepare_llm_prompt(retailer_id, screen, time_period)

        middle_time = time.time()
        print(f"Thời gian chuẩn bị prompt: {middle_time - start_time} giây")

        response_generator = get_llm_response(full_prompt)

        end_time = time.time()
        print(f"Thời gian thực hiện: {end_time - start_time} giây")

        # In ra thông tin về việc sử dụng token
        print("\nThông tin về việc sử dụng token:")
        print(response_generator.usage_metadata)

        # Return streaming response
        return StreamingResponse(
            stream_response(response_generator),
            media_type="text/plain",
        )

    except Exception as model_error:
        raise HTTPException(
            status_code=500, detail=f"Lỗi từ mô hình AI: {str(model_error)}"
        )
