import asyncio

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse, StreamingResponse

from src.config import API_KEY, RETAILER_OPTIONS, SCREEN_OPTIONS, TIME_PERIOD_OPTIONS
from src.services.business_logic import get_llm_streaming_response, prepare_llm_prompt

router = APIRouter()


async def stream_response(generator):
    try:
        for chunk in generator:
            if hasattr(chunk, "text"):
                yield chunk.text
                await asyncio.sleep(0.05)
    except Exception as e:
        yield f"\nError occurred during streaming: {str(e)}"


@router.get("/response", response_class=PlainTextResponse)
async def response(
    retailer_id: str = Query(..., enum=list(RETAILER_OPTIONS.keys())),
    screen: str = Query(..., enum=list(SCREEN_OPTIONS.keys())),
    time_period: str = Query(..., enum=list(TIME_PERIOD_OPTIONS.keys())),
):
    try:
        full_prompt = prepare_llm_prompt(retailer_id, screen, time_period)
        response_generator = get_llm_streaming_response(full_prompt, API_KEY)
        return StreamingResponse(
            stream_response(response_generator),
            media_type="text/plain",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý yêu cầu: {str(e)}")
