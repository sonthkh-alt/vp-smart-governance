import os
import time
import json
import functools
import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
import streamlit as st
import database

# Thêm thư viện Anthropic, OpenAI & Groq
try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None

try:
    from groq import Groq
except ImportError:
    Groq = None

load_dotenv(override=True)

# Danh sách Model Ưu tiên
FLASH_MODELS = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
PRO_MODELS = ["gemini-2.5-pro", "gemini-1.5-pro", "gemini-2.5-flash", "gemini-1.5-flash"]
PRO_MODELS_ONLY = ["gemini-2.5-pro", "gemini-1.5-pro"]
CLAUDE_MODELS = ["claude-sonnet-4-6", "claude-sonnet-4-5", "claude-opus-4-6", "claude-3-5-sonnet", "claude-3-5-sonnet-20240620", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"]
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
OPENAI_MODELS = ["gpt-4o", "gpt-4o-mini"]

@functools.lru_cache(maxsize=8)
def _get_api_key(provider="gemini") -> str:
    if provider == "gemini": prefix = "GEMINI"
    elif provider == "claude": prefix = "ANTHROPIC"
    elif provider == "openai": prefix = "OPENAI"
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
    key = _get_api_key("claude") or "sk-s4sEA3IauTs0JA0bHwq4S3C7wDXtj7EHZHpB8IZbmvxSIALz"
    return anthropic.Anthropic(
        api_key=key,
        base_url="https://api.shopaikey.com"
    )

def _get_openai_client():
    if not openai:
        return "MISSING_LIB"
    key = _get_api_key("openai") or "sk-s4sEA3IauTs0JA0bHwq4S3C7wDXtj7EHZHpB8IZbmvxSIALz"
    return openai.OpenAI(
        api_key=key,
        base_url="https://api.shopaikey.com/v1"
    )

def _get_groq_client():
    if not Groq:
        return "MISSING_LIB"
    key = _get_api_key("groq")
    if not key:
        return "MISSING_KEY"
    return Groq(api_key=key)

def generate_text(prompt: str, provider: str = "claude", use_pro: bool = True, use_search: bool = True) -> str:
    """Hàm gọi AI tổng quát, hỗ trợ Claude, OpenAI, Gemini và Groq với cơ chế Fallback thông minh."""
    if provider == "claude":
        res = _call_claude(prompt, use_pro)
        if "❌ Lỗi Claude API" in res or "❌ Lỗi: Chưa tìm thấy" in res:
            msg = "⚠️ Mô hình Claude gặp sự cố. Hệ thống tự động chuyển đổi dự phòng sang OpenAI ChatGPT..."
            print(msg)
            try:
                st.toast(msg, icon="⚠️")
                st.warning(msg)
            except Exception:
                pass
            openai_res = _call_openai(prompt, use_pro)
            if not "❌ Lỗi OpenAI API" in openai_res:
                return openai_res
            
            msg2 = "⚠️ Cả Claude và OpenAI đều lỗi. Hệ thống tự động chuyển đổi sang Google Gemini Pro..."
            print(msg2)
            try:
                st.toast(msg2, icon="⚠️")
                st.warning(msg2)
            except Exception:
                pass
            gemini_res = _call_gemini_with_fallback(
                PRO_MODELS_ONLY,
                {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192}},
                use_search=use_search
            )
            return gemini_res
        return res
        
    if provider == "openai":
        res = _call_openai(prompt, use_pro)
        if "❌ Lỗi OpenAI API" in res:
            msg = "⚠️ Mô hình OpenAI gặp sự cố. Hệ thống tự động chuyển đổi sang Google Gemini Pro..."
            print(msg)
            try:
                st.toast(msg, icon="⚠️")
                st.warning(msg)
            except Exception:
                pass
            return _call_gemini_with_fallback(
                PRO_MODELS_ONLY,
                {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192}},
                use_search=use_search
            )
        return res

    if provider == "groq":
        res = _call_groq(prompt, use_pro)
        limit_keywords = ["rate_limit", "quota_exceeded", "limit_exceeded", "429"]
        if any(k in res.lower() for k in limit_keywords) or "❌ Lỗi Groq API" in res:
            msg = "⚠️ Mô hình Groq gặp sự cố. Hệ thống tự động chuyển đổi sang Google Gemini Pro..."
            print(msg)
            try:
                st.toast(msg, icon="⚠️")
                st.warning(msg)
            except Exception:
                pass
            gemini_pro_res = _call_gemini_with_fallback(
                PRO_MODELS_ONLY,
                {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192}},
                use_search=use_search
            )
            if not (any(k in gemini_pro_res.lower() for k in limit_keywords) or "lỗi kết nối gemini" in gemini_pro_res.lower()):
                return gemini_pro_res
            
            msg2 = "⚠️ Cả Groq và Gemini Pro đều gặp sự cố. Hệ thống tự động chuyển đổi sang Gemini Flash..."
            print(msg2)
            try:
                st.toast(msg2, icon="⚠️")
                st.warning(msg2)
            except Exception:
                pass
            return _call_gemini_with_fallback(
                FLASH_MODELS,
                {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192}},
                use_search=use_search
            )
        return res

    # Lựa chọn Gemini
    if use_pro:
        res = _call_gemini_with_fallback(
            PRO_MODELS_ONLY,
            {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192}},
            use_search=use_search
        )
        limit_keywords = ["rate_limit", "quota_exceeded", "limit_exceeded", "429", "lỗi kết nối gemini", "kết nối gemini (đã thử toàn bộ model)"]
        if any(k in res.lower() for k in limit_keywords) or "❌ Lỗi cấu hình Gemini" in res:
            msg = "⚠️ Mô hình Google Gemini Pro gặp sự cố. Hệ thống tự động chuyển đổi sang Groq (Llama 3.3)..."
            print(msg)
            try:
                st.toast(msg, icon="⚠️")
                st.warning(msg)
            except Exception:
                pass
            groq_res = _call_groq(prompt, use_pro=True)
            if not (any(k in groq_res.lower() for k in limit_keywords[:4]) or "❌ Lỗi Groq API" in groq_res):
                return groq_res
            
            msg2 = "⚠️ Tất cả mô hình Pro gặp sự cố. Hệ thống tự động chuyển sang Gemini Flash làm phương án cuối..."
            print(msg2)
            try:
                st.toast(msg2, icon="⚠️")
                st.warning(msg2)
            except Exception:
                pass
            return _call_gemini_with_fallback(
                FLASH_MODELS,
                {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192}},
                use_search=use_search
            )
        return res
    else:
        return _call_gemini_with_fallback(
            FLASH_MODELS,
            {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192}},
            use_search=use_search
        )

def _call_claude(prompt: str, use_pro: bool = True) -> str:
    client_res = _get_claude_client()
    if client_res == "MISSING_LIB":
        return "❌ Lỗi: Thư viện 'anthropic' chưa được cài đặt."
    if client_res == "MISSING_KEY":
        return "❌ Lỗi: Chưa tìm thấy ANTHROPIC_API_KEY."
    
    client = client_res
    try:
        model = CLAUDE_MODELS[0] if use_pro else "claude-3-haiku-20240307"
        now = datetime.datetime.now()
        sys_inst = f"Hệ thống vận hành trong thời gian thực tế: Hôm nay là ngày {now.strftime('%d/%m/%Y')} (tháng {now.strftime('%m')} năm {now.strftime('%Y')}). Bất kỳ tài liệu hoặc mốc thời gian nào từ năm 2026 trở về trước đều là thời điểm hiện tại hoặc quá khứ hoàn toàn hợp lệ."
        resp = client.messages.create(
            model=model,
            max_tokens=4096,
            system=sys_inst,
            messages=[{"role": "user", "content": prompt}]
        )
        p_tokens = resp.usage.input_tokens if hasattr(resp, "usage") and resp.usage else 0
        c_tokens = resp.usage.output_tokens if hasattr(resp, "usage") and resp.usage else 0
        if "user_info" in st.session_state:
            email = st.session_state.user_info.get("email")
            database.use_credit(email)
            database.log_api_usage(email, model, "success", p_tokens=p_tokens, c_tokens=c_tokens)
        return resp.content[0].text
    except Exception as e:
        err_msg = str(e)
        print(f"CLAUDE ERROR: {err_msg}")
        return f"❌ Lỗi Claude API: {err_msg}"

def _call_openai(prompt: str, use_pro: bool = True) -> str:
    client_res = _get_openai_client()
    if client_res == "MISSING_LIB":
        return "❌ Lỗi: Thư viện 'openai' chưa được cài đặt."
    
    client = client_res
    try:
        model = "gpt-4o" if use_pro else "gpt-4o-mini"
        now = datetime.datetime.now()
        sys_inst = f"Hệ thống vận hành trong thời gian thực tế: Hôm nay là ngày {now.strftime('%d/%m/%Y')} (tháng {now.strftime('%m')} năm {now.strftime('%Y')}). Bất kỳ tài liệu hoặc mốc thời gian nào từ năm 2026 trở về trước đều là thời điểm hiện tại hoặc quá khứ hoàn toàn hợp lệ."
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys_inst},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )
        p_tokens = completion.usage.prompt_tokens if hasattr(completion, "usage") and completion.usage else 0
        c_tokens = completion.usage.completion_tokens if hasattr(completion, "usage") and completion.usage else 0
        if "user_info" in st.session_state:
            email = st.session_state.user_info.get("email")
            database.use_credit(email)
            database.log_api_usage(email, model, "success", p_tokens=p_tokens, c_tokens=c_tokens)
        return completion.choices[0].message.content
    except Exception as e:
        err_msg = str(e)
        print(f"OPENAI ERROR: {err_msg}")
        return f"❌ Lỗi OpenAI API: {err_msg}"

def _call_groq(prompt: str, use_pro: bool = True) -> str:
    client_res = _get_groq_client()
    if client_res == "MISSING_LIB":
        return "❌ Lỗi: Thư viện 'groq' chưa được cài đặt."
    if client_res == "MISSING_KEY":
        return "❌ Lỗi: Chưa tìm thấy GROQ_API_KEY. Hãy kiểm tra file .env hoặc Secrets."
    
    client = client_res
    try:
        model = GROQ_MODELS[0] if use_pro else GROQ_MODELS[1]
        now = datetime.datetime.now()
        sys_inst = f"Hệ thống vận hành trong thời gian thực tế: Hôm nay là ngày {now.strftime('%d/%m/%Y')} (tháng {now.strftime('%m')} năm {now.strftime('%Y')}). Bất kỳ tài liệu hoặc mốc thời gian nào từ năm 2026 trở về trước đều là thời điểm hiện tại hoặc quá khứ hoàn toàn hợp lệ."
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys_inst},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        p_tokens = completion.usage.prompt_tokens if hasattr(completion, "usage") and completion.usage else 0
        c_tokens = completion.usage.completion_tokens if hasattr(completion, "usage") and completion.usage else 0
        if "user_info" in st.session_state:
            email = st.session_state.user_info.get("email")
            database.use_credit(email)
            database.log_api_usage(email, model, "success", p_tokens=p_tokens, c_tokens=c_tokens)
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

    now = datetime.datetime.now()
    sys_inst = f"Hệ thống vận hành trong thời gian thực tế: Hôm nay là ngày {now.strftime('%d/%m/%Y')} (tháng {now.strftime('%m')} năm {now.strftime('%Y')}). Bất kỳ tài liệu hoặc mốc thời gian nào từ năm 2026 trở về trước đều là thời điểm hiện tại hoặc quá khứ hoàn toàn hợp lệ."

    for model_id in model_list:
        try:
            resp = client.models.generate_content(
                model=model_id, contents=config["prompt"],
                config=types.GenerateContentConfig(
                    tools=tools, 
                    system_instruction=sys_inst,
                    **config["params"]
                ),
            )
            if not resp or not resp.text: raise RuntimeError("API trả về rỗng.")
            
            p_tokens = resp.usage_metadata.prompt_token_count if hasattr(resp, "usage_metadata") and resp.usage_metadata else 0
            c_tokens = resp.usage_metadata.candidates_token_count if hasattr(resp, "usage_metadata") and resp.usage_metadata else 0
            if "user_info" in st.session_state:
                email = st.session_state.user_info.get("email")
                database.use_credit(email)
                database.log_api_usage(email, model_id, "success", p_tokens=p_tokens, c_tokens=c_tokens)
            
            raw = resp.text
            if not parse_json: return raw
            
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
            continue
            
    return f"⚠️ Lỗi kết nối Gemini (đã thử toàn bộ model): {last_error}"

def generate_json(prompt: str, provider: str = "claude", use_pro: bool = True) -> dict:
    if provider == "claude":
        res = _call_claude(prompt + "\nBẮT BUỘC TRẢ VỀ JSON NGUYÊN BẢN (KHÔNG ĐƯỢC CHỨA CÁC ĐOẠN GIẢI THÍCH, KHÔNG CHỨA MÀU SẮC HOẶC KÝ TỰ KHÁC NGOÀI JSON).", use_pro)
        try:
            text = res.strip()
            if text.startswith("```"):
                parts = text.split("```")
                if len(parts) >= 3:
                    text = parts[1]
                    if text.startswith("json"): text = text[4:]
            return json.loads(text)
        except Exception as e:
            print("WARNING: Claude JSON lỗi, tự động dự phòng sang OpenAI...")
            return generate_json(prompt, provider="openai", use_pro=use_pro)
            
    if provider == "openai":
        client_res = _get_openai_client()
        if client_res == "MISSING_LIB":
            return {"error": "Thư viện openai chưa được cài đặt"}
        
        client = client_res
        try:
            model = "gpt-4o" if use_pro else "gpt-4o-mini"
            now = datetime.datetime.now()
            sys_inst = f"Hệ thống vận hành trong thời gian thực tế: Hôm nay là ngày {now.strftime('%d/%m/%Y')} (tháng {now.strftime('%m')} năm {now.strftime('%Y')}). Bất kỳ tài liệu hoặc mốc thời gian nào từ năm 2026 trở về trước đều là thời điểm hiện tại hoặc quá khứ hoàn toàn hợp lệ."
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": sys_inst},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            raw = completion.choices[0].message.content
            p_tokens = completion.usage.prompt_tokens if hasattr(completion, "usage") and completion.usage else 0
            c_tokens = completion.usage.completion_tokens if hasattr(completion, "usage") and completion.usage else 0
            if "user_info" in st.session_state:
                email = st.session_state.user_info.get("email")
                database.use_credit(email)
                database.log_api_usage(email, model, "success", p_tokens=p_tokens, c_tokens=c_tokens)
            return json.loads(raw)
        except Exception as e:
            print(f"WARNING: OpenAI JSON lỗi: {e}. Chuyển hướng dự phòng sang Gemini Pro...")
            return _call_gemini_with_fallback(
                PRO_MODELS_ONLY,
                {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192, "response_mime_type": "application/json"}},
                parse_json=True
            )
    
    if provider == "groq":
        res = _call_groq(prompt + "\nBẮT BUỘC TRẢ VỀ JSON NGUYÊN BẢN.", use_pro)
        limit_keywords = ["rate_limit", "quota_exceeded", "limit_exceeded", "429"]
        if any(k in res.lower() for k in limit_keywords) or "❌ Lỗi Groq API" in res:
            print("WARNING: Groq JSON bị giới hạn, tự động chuyển sang Gemini Pro...")
            gemini_pro_res = _call_gemini_with_fallback(
                PRO_MODELS_ONLY,
                {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192, "response_mime_type": "application/json"}},
                parse_json=True
            )
            if not (isinstance(gemini_pro_res, str) and "lỗi" in gemini_pro_res.lower()):
                return gemini_pro_res
            return _call_gemini_with_fallback(
                FLASH_MODELS,
                {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192, "response_mime_type": "application/json"}},
                parse_json=True
            )

        try:
            text = res.strip()
            if text.startswith("```"):
                parts = text.split("```")
                if len(parts) >= 3:
                    text = parts[1]
                    if text.startswith("json"): text = text[4:]
            return json.loads(text)
        except: return {"error": "Groq không trả về JSON hợp lệ", "raw": res}
    
    # Lựa chọn Gemini
    if use_pro:
        res = _call_gemini_with_fallback(
            PRO_MODELS_ONLY,
            {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192, "response_mime_type": "application/json"}},
            parse_json=True
        )
        if isinstance(res, str) and ("lỗi" in res.lower() or "⚠️" in res):
            print("WARNING: Gemini Pro JSON gặp sự cố, chuyển sang Groq...")
            groq_raw = _call_groq(prompt + "\nBẮT BUỘC TRẢ VỀ JSON NGUYÊN BẢN.", use_pro=True)
            limit_keywords = ["rate_limit", "quota_exceeded", "limit_exceeded", "429"]
            if not (any(k in groq_raw.lower() for k in limit_keywords) or "❌ Lỗi Groq API" in groq_raw):
                try:
                    text = groq_raw.strip()
                    if text.startswith("```"):
                        parts = text.split("```")
                        if len(parts) >= 3:
                            text = parts[1]
                            if text.startswith("json"): text = text[4:]
                    return json.loads(text)
                except: pass
            
            print("WARNING: Dùng Gemini Flash làm cứu cánh...")
            return _call_gemini_with_fallback(
                FLASH_MODELS,
                {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192, "response_mime_type": "application/json"}},
                parse_json=True
            )
        return res
    else:
        return _call_gemini_with_fallback(
            FLASH_MODELS,
            {"prompt": prompt, "params": {"temperature": 0.1, "max_output_tokens": 8192, "response_mime_type": "application/json"}},
            parse_json=True
        )

def check_api_status():
    results = {}
    # Test Anthropic
    try:
        client = _get_claude_client()
        if client and client != "MISSING_LIB":
            results["Anthropic Claude"] = {"status": "✅ Hoạt động (ShopAIKey Proxy)"}
        else: results["Anthropic Claude"] = {"status": "❌ Chưa cấu hình"}
    except:
        results["Anthropic Claude"] = {"status": "❌ Lỗi kết nối"}

    # Test OpenAI
    try:
        client = _get_openai_client()
        if client and client != "MISSING_LIB":
            results["OpenAI ChatGPT"] = {"status": "✅ Hoạt động (ShopAIKey Proxy)"}
        else: results["OpenAI ChatGPT"] = {"status": "❌ Chưa cấu hình"}
    except:
        results["OpenAI ChatGPT"] = {"status": "❌ Lỗi kết nối"}

    # Test Gemini
    try:
        client = _get_gemini_client()
        resp = client.models.generate_content(model="gemini-2.5-flash", contents="Ping")
        if resp and resp.text:
            results["Gemini"] = {"status": "✅ Hoạt động"}
        else:
            results["Gemini"] = {"status": "⚠️ API phản hồi rỗng"}
    except ValueError:
        results["Gemini"] = {"status": "❌ Chưa cấu hình (Thiếu API Key)"}
    except Exception as e:
        err = str(e).lower()
        if "429" in err or "quota" in err or "resource_exhausted" in err:
            results["Gemini"] = {"status": "⚠️ Hết quota miễn phí (Đợi reset)"}
        else:
            results["Gemini"] = {"status": f"❌ Lỗi: {str(e)[:80]}"}
    
    # Test Groq
    try:
        client = _get_groq_client()
        if client and client != "MISSING_KEY" and client != "MISSING_LIB":
            results["Groq"] = {"status": "✅ Hoạt động"}
        else: results["Groq"] = {"status": "➖ Chưa cấu hình"}
    except: 
        results["Groq"] = {"status": "❌ Lỗi"}
    
    return results
