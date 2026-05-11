"""
gemini_client.py
================
Centralized AI Client cho Smart Governance Platform.
Sử dụng Google Gen AI SDK mới (google-genai).
Cung cấp: retry logic, model fallback, structured output.
"""

import os
import time
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ─── Model Priority List (ưu tiên từ cao xuống thấp) ─────────────────────────
# Thứ tự: thử model đầu tiên, nếu lỗi quota/not-found thì fallback sang model tiếp
FLASH_MODELS = ["gemini-flash-latest", "gemini-flash-lite-latest"]
PRO_MODELS   = ["gemini-pro-latest",   "gemini-flash-latest"]


def _get_client() -> genai.Client:
    """Tạo và trả về Gemini Client đã xác thực."""
    api_key = None
    # Ưu tiên st.secrets (Streamlit Cloud)
    try:
        import streamlit as st
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    # Fallback: biến môi trường / .env
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Thiếu GEMINI_API_KEY. Cấu hình trong .env (local) hoặc Streamlit Secrets (Cloud).")
    return genai.Client(api_key=api_key)


def generate_text(prompt: str, use_pro: bool = False, max_retries: int = 2) -> str:
    """
    Gọi Gemini để sinh văn bản thuần.

    Args:
        prompt: Nội dung prompt
        use_pro: True để dùng model Pro (chất lượng cao hơn, chậm hơn)
        max_retries: Số lần thử lại khi gặp lỗi tạm thời

    Returns:
        Chuỗi văn bản kết quả
    """
    client = _get_client()
    model_list = PRO_MODELS if use_pro else FLASH_MODELS

    for model_id in model_list:
        for attempt in range(max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=8192,
                    )
                )
                return response.text
            except Exception as e:
                err_str = str(e).lower()
                # Quota, rate limit, hoặc server overload → thử lại
                if any(x in err_str for x in ["429", "resource_exhausted", "503", "unavailable", "overloaded"]):
                    if attempt < max_retries:
                        time.sleep(5 * (attempt + 1))
                        continue
                    else:
                        break  # Chuyển sang model tiếp theo
                # Model not found → thử model tiếp
                if "404" in err_str or "not found" in err_str:
                    break
                # Lỗi khác → raise
                raise RuntimeError(f"Lỗi Gemini API [{model_id}]: {e}")

    return "⚠️ Không thể kết nối đến Gemini API lúc này. Vui lòng kiểm tra API Key hoặc thử lại sau."


def generate_json(prompt: str, use_pro: bool = False, max_retries: int = 2) -> dict:
    """
    Gọi Gemini để sinh output JSON.

    Returns:
        dict kết quả đã parse, hoặc dict chứa 'error' nếu thất bại
    """
    client = _get_client()
    model_list = PRO_MODELS if use_pro else FLASH_MODELS

    for model_id in model_list:
        for attempt in range(max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=8192,
                        response_mime_type="application/json",
                    )
                )
                raw = response.text.strip()
                # Loại bỏ markdown code block nếu có
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"error": "Kết quả AI không đúng định dạng JSON.", "raw": response.text}
            except Exception as e:
                err_str = str(e).lower()
                if any(x in err_str for x in ["429", "resource_exhausted", "503", "unavailable", "overloaded"]):
                    if attempt < max_retries:
                        time.sleep(5 * (attempt + 1))
                        continue
                    else:
                        break
                if "404" in err_str or "not found" in err_str:
                    break
                return {"error": f"Lỗi Gemini API [{model_id}]: {e}"}

    return {"error": "Không thể kết nối đến Gemini API sau nhiều lần thử."}


def check_api_key() -> bool:
    """Kiểm tra nhanh API key có hợp lệ không."""
    try:
        client = _get_client()
        client.models.list()
        return True
    except Exception:
        return False
