import streamlit as st
import requests
import urllib.parse

# Cấu hình Google OAuth
raw_id = st.secrets.get("my_google_app", {}).get("id", "")
raw_secret = st.secrets.get("my_google_app", {}).get("secret", "")

CLIENT_ID = raw_id.strip().replace("\n", "").replace("\r", "")
CLIENT_SECRET = raw_secret.strip().replace("\n", "").replace("\r", "")
url_phan_hoi = "https://hdndthanhhoa.streamlit.app/"

ADMIN_EMAIL = "sonthkh@gmail.com"

def init_auth():
    """Xử lý Callback từ Google để định danh User."""
    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False
        st.session_state.user_info = None

    params = st.query_params
    if "code" in params and not st.session_state.is_logged_in:
        try:
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "code": params["code"],
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": url_phan_hoi,
                "grant_type": "authorization_code",
            }
            response = requests.post(token_url, data=data)
            tokens = response.json()
            
            if "access_token" in tokens:
                userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
                headers = {"Authorization": f"Bearer {tokens['access_token']}"}
                user_info = requests.get(userinfo_url, headers=headers).json()
                
                st.session_state.is_logged_in = True
                st.session_state.user_info = user_info
                
                import database
                is_admin = 1 if user_info.get("email") == ADMIN_EMAIL else 0
                database.create_user(user_info.get("email"), user_info.get("name"), is_admin)
                
                ip = st.context.headers.get("x-forwarded-for", "-")
                ua = st.context.headers.get("user-agent", "-")
                database.log_login(user_info.get("email"), ip, ua)
                
                st.query_params.clear()
                st.rerun()
        except Exception as e:
            st.error(f"Lỗi kết nối Google: {str(e)}")

def render_login_button(sidebar=False):
    """Vẽ nút đăng nhập Google mở Tab mới hoàn toàn (Tránh lỗi 403 Iframe)."""
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": url_phan_hoi,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account"
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    
    if sidebar:
        # Nút Sidebar dùng HTML link target="_blank"
        st.markdown(f"""
            <a href="{auth_url}" target="_blank" style="text-decoration: none;">
                <div style="background: #ff4b4b; color: white; padding: 10px; 
                            border-radius: 8px; text-align: center; font-weight: 600;
                            font-size: 14px; box-shadow: 0 2px 8px rgba(255, 75, 75, 0.2);">
                    🔑 ĐĂNG NHẬP GOOGLE
                </div>
            </a>
        """, unsafe_allow_html=True)
    else:
        # Nút Trang chủ dùng HTML link target="_blank"
        st.markdown(f"""
            <a href="{auth_url}" target="_blank" style="text-decoration: none;">
                <div style="background: linear-gradient(135deg, #ff4b4b 0%, #ff1f1f 100%);
                            color: white; padding: 14px; border-radius: 10px;
                            text-align: center; font-weight: 700; font-size: 18px;
                            box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3);
                            margin-bottom: 20px; display: block; width: 100%;">
                    🚀 ĐĂNG NHẬP NGAY VỚI GOOGLE
                </div>
            </a>
        """, unsafe_allow_html=True)

def login_google():
    if not CLIENT_ID or not CLIENT_SECRET:
        st.error("### 🔐 Thiếu thông tin kết nối Google")
        return

    render_login_button(sidebar=False)
    st.stop()

def logout():
    st.session_state.is_logged_in = False
    st.session_state.user_info = None
    st.rerun()

def check_auth_status():
    return st.session_state.get("is_logged_in", False)

def get_user_info():
    return st.session_state.get("user_info", {})

def require_auth(action_name="truy cập tính năng này"):
    if not st.session_state.get("is_logged_in", False):
        st.warning(f"⚠️ Bạn cần đăng nhập để {action_name}.")
        login_google()
        return False
    
    import database
    user = database.get_user(st.session_state.user_info.get("email"))
    if not user: return False
    if not user["is_admin"] and user["credits"] <= 0:
        st.error(f"### ❌ Hết lượt truy vấn AI")
        st.stop()
        return False
    return True
