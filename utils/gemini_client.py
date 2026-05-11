import os
import time
import json
import functools
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(override=True)

# Using Flash-Lite and 1.5-Flash for better free tier quota
FLASH_MODELS = ["gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-flash-latest", "gemini-2.5-flash"]
PRO_MODELS   = ["gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-flash-latest", "gemini-2.5-flash"]

_RETRY_ERRORS = frozenset(["429", "resource_exhausted", "503", "unavailable", "overloaded", "deadline_exceeded"])
_SKIP_ERRORS  = frozenset(["404", "not_found", "unimplemented", "permission_denied"])

@functools.lru_cache(maxsize=1)
def _get_api_key() -> str:
    """Resolve API key once, then cache."""
    try:
        import streamlit as st
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return key
    except Exception:
        pass
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return "" # Don't raise here, let the client call handle it with a better message
    return key


def _get_client() -> genai.Client:
    key = _get_api_key()
    if not key:
        raise ValueError("Thiếu GEMINI_API_KEY. Vui lòng kiểm tra file .env hoặc Streamlit Secrets.")
    return genai.Client(api_key=key)


def _should_retry(err_str: str) -> bool:
    return any(x in err_str for x in _RETRY_ERRORS)


def _should_skip(err_str: str) -> bool:
    return any(x in err_str for x in _SKIP_ERRORS)


def _call_with_fallback(model_list, config, max_retries=2, parse_json=False, use_search=False):
    """Core retry+fallback loop for both text and JSON generation."""
    try:
        client = _get_client()
    except ValueError as e:
        return {"error": str(e)} if parse_json else f"❌ {e}"

    last_error = None

    # Prepare tools if search is requested
    tools = [types.Tool(google_search_retrieval=types.GoogleSearchRetrieval())] if use_search else None

    for model_id in model_list:
        for attempt in range(max_retries + 1):
            try:
                # Add tools to config if search is enabled
                current_params = config["params"].copy()
                
                resp = client.models.generate_content(
                    model=model_id, contents=config["prompt"],
                    config=types.GenerateContentConfig(tools=tools, **current_params),
                )
                
                if not resp or not resp.text:
                    raise RuntimeError("API trả về kết quả rỗng (Empty response).")
                
                raw = resp.text
                if not parse_json:
                    return raw

                text = raw.strip()
                if text.startswith("```"):
                    parts = text.split("```")
                    if len(parts) >= 3:
                        text = parts[1]
                        if text.startswith("json"):
                            text = text[4:]
                return json.loads(text)

            except json.JSONDecodeError:
                return {"error": "Kết quả AI không đúng định dạng JSON.", "raw": raw}
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                
                # Log error to console for debugging
                print(f"DEBUG: Gemini Error [{model_id}] (Attempt {attempt+1}): {e}")

                if _should_retry(err_str) and attempt < max_retries:
                    time.sleep(5 * (attempt + 1))
                    continue
                
                # If it's a 404 or other skippable error, try next model
                if _should_skip(err_str) or _should_retry(err_str):
                    break
                
                # If it's a fatal error (like 401 Unauthorized), don't bother retrying or falling back
                if "401" in err_str or "unauthorized" in err_str or "invalid_api_key" in err_str:
                    msg = "API Key không hợp lệ hoặc đã hết hạn."
                    return {"error": msg} if parse_json else f"❌ {msg}"

                # Otherwise, continue to next model/retry
                continue

    fallback_msg = f"Không thể kết nối đến Gemini API. Lỗi cuối cùng: {last_error}"
    return {"error": fallback_msg} if parse_json else f"⚠️ {fallback_msg}"


def generate_text(prompt: str, use_pro: bool = False, max_retries: int = 2, use_search: bool = True) -> str:
    return _call_with_fallback(
        PRO_MODELS if use_pro else FLASH_MODELS,
        {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192}},
        max_retries=max_retries,
        use_search=use_search
    )


def generate_json(prompt: str, use_pro: bool = False, max_retries: int = 2, use_search: bool = True) -> dict:
    return _call_with_fallback(
        PRO_MODELS if use_pro else FLASH_MODELS,
        {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192,
                                       "response_mime_type": "application/json"}},
        max_retries=max_retries, parse_json=True,
        use_search=use_search
    )


def check_api_key() -> bool:
    try:
        _get_client().models.list()
        return True
    except Exception:
        return False

