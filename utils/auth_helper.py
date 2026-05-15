import streamlit as st
import requests
import urllib.parse

# Cấu hình Google OAuth (Phòng thủ lỗi xuống dòng trong Secrets)
raw_id = st.secrets.get("my_google_app", {}).get("id", "")
raw_secret = st.secrets.get("my_google_app", {}).get("secret", "")

# Làm sạch dữ liệu: xóa khoảng trắng và dấu xuống dòng
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
    if "code" in params and params.get("state") == "popup":
        # Chạy đoạn mã JS để gửi code về trang chính và đóng popup
        # Trang chính sẽ nhận URL hiện tại (có code) và reload lại chính nó
        st.components.v1.html(f"""
            <script>
                if (window.opener) {{
                    window.opener.location.href = window.location.href.replace('state=popup', 'state=verified');
                    window.close();
                }}
            </script>
        """, height=0)
        st.stop()

    # TRƯỜNG HỢP 2: Trang chính nhận code đã được chuyển từ popup (state=verified)
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
            st.error(f"Lỗi hệ thống khi kết nối Google: {str(e)}")

def login_google():
    """Kích hoạt luồng Đăng nhập Google với cửa sổ Popup chuyên nghiệp."""
    if not CLIENT_ID or not CLIENT_SECRET:
        st.error("### 🔐 Thiếu thông tin kết nối Google")
        st.info("Vui lòng đảm bảo bạn đã dán mã ID và Secret vào Secrets với tên mục [my_google_app].")
        return

    # Xây dựng URL chuẩn với tham số state=popup
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": url_phan_hoi,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": "popup"
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    
    st.markdown("### 🏛️ Đăng nhập Hệ thống")
    st.info("Sử dụng tài khoản Google để truy cập đầy đủ tính năng AI.")
    
    # Nút bấm kích hoạt Popup bằng Javascript
    # Lưu ý: CSS cho nút này sẽ được đồng nhất với style của Streamlit
    st.components.v1.html(f"""
        <style>
            .login-btn {{
                background-color: #ff4b4b;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-family: 'Inter', sans-serif;
                font-size: 16px;
                font-weight: 600;
                width: 100%;
                cursor: pointer;
                transition: background-color 0.3s;
                text-decoration: none;
                display: block;
                text-align: center;
            }}
            .login-btn:hover {{
                background-color: #ff3333;
            }}
        </style>
        <button onclick="openPopup()" class="login-btn">🔑 ĐĂNG NHẬP VỚI GOOGLE</button>
        <script>
            function openPopup() {{
                const width = 500;
                const height = 600;
                const left = (window.innerWidth / 2) - (width / 2);
                const top = (window.innerHeight / 2) - (height / 2);
                window.open('{auth_url}', 'GoogleLogin', 
                    'width=' + width + ',height=' + height + ',top=' + top + ',left=' + left);
            }}
        </script>
    """, height=70)
    st.stop()

def logout():
    """Đăng xuất."""
    st.session_state.is_logged_in = False
    st.session_state.user_info = None
    st.rerun()

def check_auth_status():
    """Kiểm tra trạng thái đăng nhập an toàn."""
    return st.session_state.get("is_logged_in", False)

def get_user_info():
    """Lấy thông tin người dùng."""
    return st.session_state.get("user_info", {})

def require_auth(action_name="truy cập tính năng này"):
    """
    Kiểm tra quyền truy cập. Nếu chưa đăng nhập, hiển thị nút đăng nhập và dừng script.
    Trả về True nếu đã đăng nhập.
    """
    if not st.session_state.get("is_logged_in", False):
        st.warning(f"⚠️ Bạn cần đăng nhập để {action_name}.")
        login_google()
        return False
    
    import database
    user = database.get_user(st.session_state.user_info.get("email"))
    
    if not user:
        st.error("Lỗi dữ liệu người dùng. Vui lòng đăng nhập lại.")
        return False
        
    if not user["is_admin"] and user["credits"] <= 0:
        st.error(f"### ❌ Hết lượt truy vấn AI\nBạn đã sử dụng hết số lượt truy vấn AI được cấp. Vui lòng liên hệ đồng chí **Hà Ngọc Sơn**, PCVP Đoàn ĐBQH và HĐND tỉnh để được gia hạn thêm lượt sử dụng.")
        st.stop()
        return False
        
    return True
