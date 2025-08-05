import os
import json
import time
import uuid
import httpx
import random
import logging
from fastapi import FastAPI, Request, HTTPException, Depends, APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from starlette.status import HTTP_401_UNAUTHORIZED
import google.generativeai as genai
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .helpers import SAFETY_SETTINGS, SAFETY_SETTINGS_G2, openai_to_gemini_params
from .models import ChatCompletionRequest
from collections import deque
from . import gem_handler

# --- 日志记录 ---
MAX_LOG_ENTRIES = 20
call_logs = deque(maxlen=MAX_LOG_ENTRIES)

# --- 配置 ---
GEM_ENABLED = os.environ.get("GEM", "false").lower() == "true"
GEMINI_API_KEYS = [key.strip() for key in os.environ.get("GEMINI_API_KEYS", "").split(',') if key.strip()]
LAOPOBAO_AUTH_KEY = os.environ.get("LAOPOBAO_AUTH")
MAX_TRY = int(os.environ.get("MAX_TRY", 3))

# --- FastAPI 应用实例与速率限制 ---
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="baojimi-lite",
    version="1.0.0",
    description="年轻人的第一个gemini代理轮询服务 (Hugging Face Docker版)"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- 启动事件 ---
@app.on_event("startup")
async def startup_event():
    logger = logging.getLogger("uvicorn.info")
    logger.info("--- Baojimi-lite Configuration Check ---")
    if GEMINI_API_KEYS:
        logger.info("已配置Gemini API Key")
    else:
        logger.warning("未配置Gemini API Key")

    if LAOPOBAO_AUTH_KEY:
        logger.info("已配置调用密钥")
    else:
        logger.warning("未配置调用密钥，请立即配置")

    if 'MAX_TRY' in os.environ:
        logger.info(f"已配置最大重试次数，最大重试次数为{MAX_TRY}")
    else:
        logger.info(f"未配置最大重试次数，默认为 3")

    if 'GEM' in os.environ:
        if GEM_ENABLED:
            logger.info("已开启GEM自愈功能")
        else:
            logger.info("已加载GEM自愈功能，但尚未启动，如需启动，请将GEM的值更改为true")
    else:
        logger.warning("GEM自愈系统未启动，将按照常规方式处理API调用")
    logger.info("----------------------------------------")

# --- 路由 ---
v1_router = APIRouter(prefix="/v1")
admin_router = APIRouter(prefix="/api")

# --- 认证 ---
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_current_auth(auth_key: str = Depends(api_key_header)):
    if not LAOPOBAO_AUTH_KEY:
        return None # No auth key configured
    if not auth_key or auth_key.replace("Bearer ", "") != LAOPOBAO_AUTH_KEY:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid authorization key")
    return auth_key

async def verify_auth_key(auth: str = Depends(get_current_auth)):
    if LAOPOBAO_AUTH_KEY and not auth:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Authorization key required but not provided")

# --- 路由实现 ---
@admin_router.get("/status", tags=["Admin"])
async def get_status():
    return {"status": "ok", "key_count": len(GEMINI_API_KEYS), "service": "baojimi-lite"}

@admin_router.get("/logs", tags=["Admin"])
async def get_logs():
    return list(call_logs)

@admin_router.post("/check-keys", tags=["Admin"], dependencies=[Depends(verify_auth_key)])
@limiter.limit("5/minute")
async def check_api_keys(request: Request):
    if not GEMINI_API_KEYS: return {"valid_keys": [], "invalid_keys": []}
    valid_keys, invalid_keys = [], []
    async with httpx.AsyncClient() as client:
        for key in GEMINI_API_KEYS:
            try:
                if not isinstance(key, str) or not key:
                    raise ValueError("API key must be a non-empty string.")
                genai.configure(api_key=key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                await model.generate_content_async("hello", generation_config={"max_output_tokens": 1})
                valid_keys.append(key)
            except Exception as e:
                # Log the error for debugging purposes
                print(f"Key check failed for key ending in ...{key[-4:] if isinstance(key, str) and len(key) > 4 else '****'}: {e}")
                invalid_keys.append(key)
    return {"valid_keys": valid_keys, "invalid_keys": invalid_keys}

@v1_router.get("/models", tags=["OpenAI Compatibility"])
async def list_models():
    if not GEMINI_API_KEYS:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEYS is not configured.")

    api_key = random.choice(GEMINI_API_KEYS)
    genai.configure(api_key=api_key)

    try:
        models = genai.list_models()
        model_list = []
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                model_list.append(
                     {"id": m.name.replace("models/", ""), "object": "model", "created": int(time.time()), "owned_by": "google"}
                 )
        return {"object": "list", "data": model_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch models from Google. Error: {e}")

@v1_router.post("/chat/completions", tags=["OpenAI Compatibility"]) # Auth is handled inside
@limiter.limit("20/minute")
async def chat_completions(req: ChatCompletionRequest, request: Request, auth: str = Depends(get_current_auth)):
    # For some clients, we need to check auth key here
    if LAOPOBAO_AUTH_KEY and not auth:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid authorization key")

    if not GEMINI_API_KEYS: raise HTTPException(status_code=500, detail="GEMINI_API_KEYS is not configured.")
  
    model_name = req.model
    try:
        gemini_params = openai_to_gemini_params(req.dict())
        safety_settings = SAFETY_SETTINGS_G2 if model_name.startswith('gemini-2') else SAFETY_SETTINGS
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    available_keys = random.sample(GEMINI_API_KEYS, len(GEMINI_API_KEYS))
  
    log_entry = {
        "id": f"log-{uuid.uuid4()}",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "model": model_name,
        "stream": req.stream,
        "status": "pending",
        "key_used": None,
        "error_info": None
    }

    for i in range(min(len(available_keys), MAX_TRY)):
        api_key = available_keys[i]
        log_entry["key_used"] = f"...{api_key[-4:]}"
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=model_name,
                safety_settings=safety_settings,
                system_instruction=gemini_params.get("system_instruction")
            )
          
            if req.stream:
                if GEM_ENABLED and model_name.startswith('gemini'):
                    # Use the self-healing stream generator for all gemini models
                    response_generator = gem_handler.self_healing_stream_generator(model_name, gemini_params, api_key, SAFETY_SETTINGS, SAFETY_SETTINGS_G2)
                else:
                    # Use the standard stream generator
                    response_generator = await model.generate_content_async(gemini_params["contents"], generation_config=gemini_params["generation_config"], stream=True)
                
                log_entry["status"] = "success"
                call_logs.appendleft(log_entry)
                return StreamingResponse(stream_generator(response_generator, model_name), media_type="text/event-stream")
            else:
                response = await model.generate_content_async(gemini_params["contents"], generation_config=gemini_params["generation_config"])
                log_entry["status"] = "success"
                call_logs.appendleft(log_entry)
                return non_stream_response(response, model_name)
        except Exception as e:
            print(f"Attempt {i+1} with key ...{api_key[-4:]} failed: {e}")
            log_entry["status"] = "failed"
            log_entry["error_info"] = str(e)
            if i == min(len(available_keys), MAX_TRY) - 1:
                call_logs.appendleft(log_entry)
                raise HTTPException(status_code=500, detail=f"All API keys failed. Last error: {e}")
            continue
    
    # This part should ideally not be reached if successful response is returned
    log_entry["status"] = "failed"
    log_entry["error_info"] = "All retries failed."
    call_logs.appendleft(log_entry)
    raise HTTPException(status_code=500, detail="Failed to get response from Gemini after all retries.")

# --- 辅助函数 ---
def gemini_finish_reason_to_openai(reason: str) -> str:
    """Converts Gemini's finish reason to OpenAI's format."""
    if reason is None:
        return "stop"
    # Maps Gemini finish reasons to OpenAI equivalents.
    return {
        "STOP": "stop",
        "MAX_TOKENS": "length",
        "SAFETY": "content_filter",
        "RECITATION": "content_filter",
        "OTHER": "stop",
    }.get(reason, "stop")

async def stream_generator(gemini_response, model_name):
    try:
        async for chunk in gemini_response:
            if not chunk.parts:
                continue
            choice = {
                "index": 0,
                "delta": {"content": chunk.text},
                "finish_reason": None
            }
            if chunk.candidates and chunk.candidates[0].finish_reason:
                choice["finish_reason"] = gemini_finish_reason_to_openai(chunk.candidates[0].finish_reason)

            openai_chunk = {
                "id": f"chatcmpl-{uuid.uuid4()}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_name,
                "choices": [choice]
            }
            yield f"data: {json.dumps(openai_chunk)}\n\n"
    except Exception as e:
        print(f"Error in stream generator: {e}")
        error_chunk = {"error": str(e)}
        yield f"data: {json.dumps(error_chunk)}\n\n"

    final_chunk = {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }
        ]
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"

def non_stream_response(gemini_response, model_name):
    try:
        content = gemini_response.text
        usage = gemini_response.usage_metadata
        finish_reason = gemini_finish_reason_to_openai(gemini_response.candidates[0].finish_reason if gemini_response.candidates else None)

        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": finish_reason
                }
            ],
            "usage": {
                "prompt_tokens": usage.prompt_token_count,
                "completion_tokens": usage.candidates_token_count,
                "total_tokens": usage.total_token_count
            }
        }
    except Exception as e:
        # Handle cases where the response might not have the expected structure
        # For example, if the response was blocked due to safety settings
        try:
            # Try to get a more descriptive error from the response
            error_details = str(gemini_response.prompt_feedback)
        except AttributeError:
            error_details = str(e)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to process Gemini response", "details": error_details}
        )



# --- 注册路由和静态文件服务 ---
app.include_router(v1_router)
app.include_router(admin_router)
app.mount("/", StaticFiles(directory="public", html=True), name="static")