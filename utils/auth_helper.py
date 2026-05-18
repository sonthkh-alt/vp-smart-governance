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

    # Tự động nhận diện khi Google gửi phản hồi về
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
                
                # Biến khách thành User chính thức của hệ thống
                st.session_state.is_logged_in = True
                st.session_state.user_info = user_info
                
                # Cập nhật DB và ghi log
                import database
                is_admin = 1 if user_info.get("email") == ADMIN_EMAIL else 0
                database.create_user(user_info.get("email"), user_info.get("name"), is_admin)
                
                # Ghi log đăng nhập
                ip = st.context.headers.get("x-forwarded-for", "-")
                ua = st.context.headers.get("user-agent", "-")
                database.log_login(user_info.get("email"), ip, ua)
                
                st.query_params.clear()
                st.rerun()
        except Exception as e:
            st.error(f"Lỗi hệ thống khi kết nối Google: {str(e)}")

    # Lắng nghe tín hiệu từ Popup (nếu chưa đăng nhập và chưa có code)
    if not st.session_state.is_logged_in and "code" not in params:
        st.components.v1.html("""
            <script>
                const poll = setInterval(() => {
                    const code = localStorage.getItem('google_oauth_code');
                    if (code) {
                        localStorage.removeItem('google_oauth_code');
                        clearInterval(poll);
                        window.top.location.href = window.top.location.origin + '/?code=' + encodeURIComponent(code);
                    }
                }, 500);
            </script>
        """, height=0)

def render_login_button(sidebar=False):
    """Vẽ nút đăng nhập Google (Popup → tự đóng sau khi đăng nhập)."""
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
    
    if sidebar:
        st.components.v1.html(f"""
            <style>
                .g-btn {{
                    background: #ff4b4b; color: white; border: none;
                    padding: 10px; border-radius: 8px; width: 100%;
                    font-size: 14px; font-weight: 600; cursor: pointer;
                    box-shadow: 0 2px 8px rgba(255,75,75,0.2);
                }}
                .g-btn:hover {{ opacity: 0.9; }}
            </style>
            <button class="g-btn" onclick="window.open('{auth_url}', 'GoogleLogin', 'width=500,height=600,left='+((screen.width-500)/2)+',top='+((screen.height-600)/2))">
                🔑 Đăng nhập Google
            </button>
        """, height=50)
    else:
        st.components.v1.html(f"""
            <style>
                .g-btn-main {{
                    background: linear-gradient(135deg, #4285F4 0%, #357AE8 100%);
                    color: white; border: none; padding: 14px; border-radius: 10px;
                    width: 100%; font-size: 16px; font-weight: 700; cursor: pointer;
                    box-shadow: 0 4px 15px rgba(66,133,244,0.3);
                    transition: all 0.3s ease;
                }}
                .g-btn-main:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(66,133,244,0.4); }}
            </style>
            <button class="g-btn-main" onclick="window.open('{auth_url}', 'GoogleLogin', 'width=500,height=600,left='+((screen.width-500)/2)+',top='+((screen.height-600)/2))">
                🔑 ĐĂNG NHẬP VỚI TÀI KHOẢN GOOGLE
            </button>
        """, height=60)

def login_google():
    """Giao diện đăng nhập đa phương thức: User/Pass + Google."""
    if not CLIENT_ID or not CLIENT_SECRET:
        st.error("### 🔐 Thiếu thông tin kết nối Google")
        return

    st.markdown("<div style='text-align: center; padding: 20px 0;'>", unsafe_allow_html=True)
    st.markdown("### 🏛️ HỆ THỐNG QUẢN TRỊ THÔNG MINH HĐND")
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("#### 👤 Đăng nhập hệ thống")
            email = st.text_input("Tên đăng nhập / Email")
            password = st.text_input("Mật khẩu", type="password")
            submitted = st.form_submit_button("ĐĂNG NHẬP", use_container_width=True, type="primary")
            
            if submitted:
                if email and password:
                    import database
                    user = database.verify_password_login(email, password)
                    if user:
                        st.session_state.is_logged_in = True
                        st.session_state.user_info = {
                            "email": user["email"],
                            "name": user["name"],
                            "picture": "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                        }
                        database.log_login(user["email"], st.context.headers.get("x-forwarded-for", "-"))
                        st.success("Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("❌ Thông tin đăng nhập không chính xác.")
                else:
                    st.warning("Vui lòng điền đầy đủ thông tin.")

        st.markdown("<div style='text-align: center; margin: 20px 0; color: #94A3B8;'>─── HOẶC ───</div>", unsafe_allow_html=True)
        render_login_button(sidebar=False)
    
    st.stop()

def logout():
    """Đăng xuất."""
    st.session_state.clear()
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
