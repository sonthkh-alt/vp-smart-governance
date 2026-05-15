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
    
    # TRƯỜNG HỢP 1: Đây là cửa sổ Popup vừa nhận code từ Google
    if "code" in params and params.get("state") == "gauth_popup":
        st.components.v1.html(f"""
            <script>
                localStorage.setItem('glogin_success', 'true');
                localStorage.setItem('glogin_code', '{params["code"]}');
                window.close();
            </script>
        """, height=0)
        st.stop()

    # TRƯỜNG HỢP 2: Trang chính lắng nghe tín hiệu
    if not st.session_state.is_logged_in and "code" not in params:
        st.components.v1.html("""
            <script>
                const timer = setInterval(() => {
                    if (localStorage.getItem('glogin_success') === 'true') {
                        const code = localStorage.getItem('glogin_code');
                        localStorage.removeItem('glogin_success');
                        localStorage.removeItem('glogin_code');
                        window.location.href = window.location.origin + window.location.pathname + '?code=' + code + '&state=verified';
                        clearInterval(timer);
                    }
                }, 500);
            </script>
        """, height=0)

    # TRƯỜNG HỢP 3: Xử lý code tại trang chính
    if "code" in params and params.get("state") == "verified":
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
            st.error(f"Lỗi hệ thống khi kết nối Google: {str(e)}")

def render_login_button(sidebar=False):
    """Vẽ nút đăng nhập Google với Popup (Dùng chung cho cả Sidebar và Trang chủ)."""
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": url_phan_hoi,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": "gauth_popup"
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    
    height = 70 if not sidebar else 60
    btn_padding = "12px" if not sidebar else "10px"
    font_size = "16px" if not sidebar else "14px"

    st.components.v1.html(f"""
        <style>
            .login-btn {{
                background: linear-gradient(135deg, #ff4b4b 0%, #ff1f1f 100%);
                color: white; border: none; padding: {btn_padding}; border-radius: 10px;
                font-family: 'Inter', sans-serif; font-size: {font_size}; font-weight: 600;
                width: 100%; cursor: pointer; box-shadow: 0 4px 15px rgba(255, 75, 75, 0.2);
                transition: all 0.3s ease; text-align: center; display: block;
                text-decoration: none;
            }}
            .login-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(255, 75, 75, 0.3);
            }}
        </style>
        <button onclick="openPopup()" class="login-btn">🔑 ĐĂNG NHẬP GOOGLE</button>
        <script>
            function openPopup() {{
                const w = 500, h = 600;
                const left = (screen.width/2)-(w/2), top = (screen.height/2)-(h/2);
                window.open('{auth_url}', 'GoogleLogin', 'width='+w+',height='+h+',top='+top+',left='+left);
            }}
        </script>
    """, height=height)

def login_google():
    """Kích hoạt giao diện đăng nhập tại trang chính."""
    if not CLIENT_ID or not CLIENT_SECRET:
        st.error("### 🔐 Thiếu thông tin kết nối Google")
        return

    st.markdown("### 🏛️ Đăng nhập Hệ thống")
    st.info("Sử dụng tài khoản Google để truy cập đầy đủ tính năng AI.")
    
    render_login_button(sidebar=False)
    
    if st.button("🔄 TẢI LẠI TRANG (Nếu bị kẹt)", use_container_width=True):
        st.rerun()
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
