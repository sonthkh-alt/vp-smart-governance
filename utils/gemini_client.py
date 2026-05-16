import os
import time
import json
import functools
from dotenv import load_dotenv
from google import genai
from google.genai import types
import streamlit as st
import database

# Thêm thư viện Anthropic & Groq
try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from groq import Groq
except ImportError:
    Groq = None

load_dotenv(override=True)

# Danh sách Model Ưu tiên
FLASH_MODELS = ["gemini-1.5-flash", "gemini-1.5-pro"]
PRO_MODELS = ["gemini-1.5-pro", "gemini-1.5-flash"]
CLAUDE_MODELS = ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"]
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]

@functools.lru_cache(maxsize=1)
def _get_api_key(provider="gemini") -> str:
    if provider == "gemini": prefix = "GEMINI"
    elif provider == "claude": prefix = "ANTHROPIC"
    elif provider == "groq": prefix = "GROQ"
    else: prefix = provider.upper()
    
    try:
        key = st.secrets.get(f"{prefix}_API_KEY")
        if key: return key
    except Exception: pass
    return os.getenv(f"{prefix}_API_KEY", "")

def _get_gemini_client():
    key = _get_api_key("gemini")
    if not key: raise ValueError("Thiếu GEMINI_API_KEY.")
    return genai.Client(api_key=key)

def _get_claude_client():
    if not anthropic: 
        return "MISSING_LIB"
    key = _get_api_key("claude")
    if not key: 
        return "MISSING_KEY"
    return anthropic.Anthropic(api_key=key)

def _get_groq_client():
    if not Groq:
        return "MISSING_LIB"
    key = _get_api_key("groq")
    if not key:
        return "MISSING_KEY"
    return Groq(api_key=key)

def generate_text(prompt: str, provider: str = "groq", use_pro: bool = True, use_search: bool = True) -> str:
    """Hàm gọi AI tổng quát, hỗ trợ Gemini, Claude và Groq với cơ chế Fallback."""
    if provider == "claude":
        return _call_claude(prompt, use_pro)
    
    if provider == "groq":
        res = _call_groq(prompt, use_pro)
        # Kiểm tra nếu bị giới hạn (Rate Limit / Quota)
        limit_keywords = ["rate_limit", "quota_exceeded", "limit_exceeded", "429"]
        if any(k in res.lower() for k in limit_keywords) or "❌ Lỗi Groq API" in res:
            print(f"⚠️ Groq bị giới hạn hoặc lỗi, đang tự động chuyển sang Gemini... (Lỗi: {res[:50]}...)")
            return _call_gemini_with_fallback(
                PRO_MODELS if use_pro else FLASH_MODELS,
                {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192}},
                use_search=use_search
            )
        return res

    return _call_gemini_with_fallback(
        PRO_MODELS if use_pro else FLASH_MODELS,
        {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192}},
        use_search=use_search
    )

def _call_claude(prompt: str, use_pro: bool = True) -> str:
    client_res = _get_claude_client()
    if client_res == "MISSING_LIB":
        return "❌ Lỗi: Thư viện 'anthropic' chưa được cài đặt."
    if client_res == "MISSING_KEY":
        return "❌ Lỗi: Chưa tìm thấy ANTHROPIC_API_KEY. Hãy kiểm tra mục Secrets trên Streamlit Cloud."
    
    client = client_res
    try:
        model = CLAUDE_MODELS[0] if use_pro else "claude-3-haiku-20240307"
        resp = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        if "user_info" in st.session_state:
            database.log_api_usage(st.session_state.user_info.get("email"), model, "success")
        return resp.content[0].text
    except Exception as e:
        err_msg = str(e)
        print(f"CLAUDE ERROR: {err_msg}")
        return f"❌ Lỗi Claude API: {err_msg}"

def _call_groq(prompt: str, use_pro: bool = True) -> str:
    client_res = _get_groq_client()
    if client_res == "MISSING_LIB":
        return "❌ Lỗi: Thư viện 'groq' chưa được cài đặt."
    if client_res == "MISSING_KEY":
        return "❌ Lỗi: Chưa tìm thấy GROQ_API_KEY. Hãy kiểm tra file .env hoặc Secrets."
    
    client = client_res
    try:
        model = GROQ_MODELS[0] if use_pro else GROQ_MODELS[1]
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=4096,
        )
        if "user_info" in st.session_state:
            database.log_api_usage(st.session_state.user_info.get("email"), model, "success")
        return completion.choices[0].message.content
    except Exception as e:
        err_msg = str(e)
        print(f"GROQ ERROR: {err_msg}")
        return f"❌ Lỗi Groq API: {err_msg}"

def _call_gemini_with_fallback(model_list, config, max_retries=1, parse_json=False, use_search=False):
    try:
        client = _get_gemini_client()
    except Exception as e: 
        return f"❌ Lỗi cấu hình Gemini: {e}"

    last_error = None
    tools = [types.Tool(google_search=types.GoogleSearch())] if use_search and not parse_json else None

    for model_id in model_list:
        try:
            resp = client.models.generate_content(
                model=model_id, contents=config["prompt"],
                config=types.GenerateContentConfig(tools=tools, **config["params"]),
            )
            if not resp or not resp.text: raise RuntimeError("API trả về rỗng.")
            
            if "user_info" in st.session_state:
                email = st.session_state.user_info.get("email")
                database.use_credit(email)
                database.log_api_usage(email, model_id, "success")
            
            raw = resp.text
            if not parse_json: return raw
            
            # Xử lý JSON
            text = raw.strip()
            if text.startswith("```"):
                parts = text.split("```")
                if len(parts) >= 3:
                    text = parts[1]
                    if text.startswith("json"): text = text[4:]
            return json.loads(text)
        except Exception as e:
            last_error = e
            print(f"GEMINI ERROR [{model_id}]: {e}")
            continue # Thử model tiếp theo
            
    return f"⚠️ Lỗi kết nối Gemini (đã thử toàn bộ model): {last_error}"

def generate_json(prompt: str, provider: str = "groq", use_pro: bool = True) -> dict:
    if provider == "claude":
        # Claude mặc định hỗ trợ JSON tốt qua prompt, nhưng ở đây ta gọi text rồi load
        res = _call_claude(prompt + "\nBẮT BUỘC TRẢ VỀ JSON NGUYÊN BẢN.", use_pro)
        try:
            return json.loads(res)
        except: return {"error": "Claude không trả về JSON hợp lệ", "raw": res}
    
    if provider == "groq":
        res = _call_groq(prompt + "\nBẮT BUỘC TRẢ VỀ JSON NGUYÊN BẢN.", use_pro)
        limit_keywords = ["rate_limit", "quota_exceeded", "limit_exceeded", "429"]
        
        # Nếu Groq lỗi/limit, chuyển sang Gemini
        if any(k in res.lower() for k in limit_keywords) or "❌ Lỗi Groq API" in res:
            print("⚠️ Groq JSON bị giới hạn, đang chuyển sang Gemini...")
            return _call_gemini_with_fallback(
                PRO_MODELS if use_pro else FLASH_MODELS,
                {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192, "response_mime_type": "application/json"}},
                parse_json=True
            )

        try:
            # Làm sạch nếu có markdown
            text = res.strip()
            if text.startswith("```"):
                parts = text.split("```")
                if len(parts) >= 3:
                    text = parts[1]
                    if text.startswith("json"): text = text[4:]
            return json.loads(text)
        except: return {"error": "Groq không trả về JSON hợp lệ", "raw": res}
    
    return _call_gemini_with_fallback(
        PRO_MODELS if use_pro else FLASH_MODELS,
        {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192, "response_mime_type": "application/json"}},
        parse_json=True
    )

def check_api_status():
    results = {}
    # Test Gemini
    try:
        _get_gemini_client().models.list()
        results["Gemini"] = {"status": "✅ Hoạt động"}
    except: results["Gemini"] = {"status": "❌ Lỗi/Chưa cấu hình"}
    
    # Test Claude
    try:
        client = _get_claude_client()
        if client:
            results["Claude"] = {"status": "✅ Hoạt động"}
        else: results["Claude"] = {"status": "➖ Chưa cấu hình"}
    except: results["Claude"] = {"status": "❌ Lỗi"}
    
    # Test Groq
    try:
        client = _get_groq_client()
        if client and client != "MISSING_KEY" and client != "MISSING_LIB":
            # Thử gọi list models nhẹ nhàng
            results["Groq"] = {"status": "✅ Hoạt động"}
        else: results["Groq"] = {"status": "➖ Chưa cấu hình"}
    except: results["Groq"] = {"status": "❌ Lỗi"}
    
    return results
