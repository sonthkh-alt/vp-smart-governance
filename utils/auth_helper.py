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
                st.session_state.show_login = False
                st.session_state.pop("login_action", None)
                
                # Cập nhật DB và ghi log
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
    """Vẽ nút đăng nhập Google (Mở tab mới - cách duy nhất ổn định trên Streamlit Cloud)."""
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
        st.link_button("🔑 Đăng nhập Google", auth_url, use_container_width=True, type="primary")
    else:
        st.link_button("🔑 ĐĂNG NHẬP VỚI TÀI KHOẢN GOOGLE", auth_url, use_container_width=True)

def login_google():
    """Giao diện đăng nhập đa phương thức: User/Pass + Google."""
    if not CLIENT_ID or not CLIENT_SECRET:
        st.error("### 🔐 Thiếu thông tin kết nối Google")
        return

    # Inject CSS tùy biến riêng cho Login form và làm mịn giao diện
    st.markdown("""
        <style>
        /* Tùy biến khung Form Đăng nhập thành Glassmorphism cao cấp */
        div[data-testid="stForm"] {
            background: rgba(15, 23, 42, 0.65) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 20px !important;
            padding: 35px !important;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            max-width: 460px !important;
            margin: 0 auto !important;
            transition: all 0.3s ease;
        }
        div[data-testid="stForm"]:hover {
            border-color: rgba(96, 165, 250, 0.3) !important;
            box-shadow: 0 25px 60px rgba(37, 99, 235, 0.15) !important;
        }
        /* Tiêu đề Đăng nhập */
        .login-header {
            text-align: center;
            font-size: 1.7rem;
            font-weight: 800;
            letter-spacing: 0.5px;
            background: linear-gradient(135deg, #F8FAFC 0%, #60A5FA 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 25px;
            margin-top: 0px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Hiển thị Logo & Tên Hệ thống lớn, cân đối ở giữa
    st.markdown("""
        <div style='text-align: center; padding: 40px 0 20px 0;'>
            <div style='font-size: 4rem; margin-bottom: 15px; filter: drop-shadow(0 0 10px rgba(96,165,250,0.3));'>🏛️</div>
            <h2 style='font-weight: 800; font-size: 2.2rem; letter-spacing: -0.5px; margin: 0; background: linear-gradient(135deg, #F8FAFC 0%, #94A3B8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>HỆ THỐNG QUẢN TRỊ THÔNG MINH HĐND</h2>
            <p style='color: #94A3B8; font-size: 1rem; margin-top: 8px;'>Hệ sinh thái AI hỗ trợ nghiệp vụ & điều hành cao cấp</p>
        </div>
    """, unsafe_allow_html=True)

    # Hiển thị banner cảnh báo hành động cần đăng nhập (nếu có)
    action_name = st.session_state.get("login_action")
    if action_name:
        st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #EF4444; padding: 14px 20px; border-radius: 10px; margin: 0 auto 25px auto; max-width: 460px; text-align: left; box-shadow: 0 4px 15px rgba(0,0,0,0.15);">
                <div style="color: #F8FAFC; font-weight: 600; font-size: 0.95rem; display: flex; align-items: center; gap: 8px;">
                    <span>⚠️ Yêu cầu đăng nhập</span>
                </div>
                <div style="color: #94A3B8; font-size: 0.85rem; margin-top: 4px;">Vui lòng đăng nhập để {action_name} hoặc liên hệ đồng chí <b>Hà Ngọc Sơn</b>, PCVP Đoàn ĐBQH và HĐND tỉnh.</div>
            </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("<h3 class='login-header'>👤 ĐĂNG NHẬP</h3>", unsafe_allow_html=True)
            email = st.text_input("Tên đăng nhập / Email", placeholder="Tên đăng nhập hoặc Email...")
            password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu truy cập...")
            submitted = st.form_submit_button("ĐĂNG NHẬP HỆ THỐNG", use_container_width=True, type="primary")
            
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
                        st.session_state.show_login = False
                        st.session_state.pop("login_action", None)
                        
                        database.log_login(user["email"], st.context.headers.get("x-forwarded-for", "-"))
                        st.success("Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("❌ Thông tin đăng nhập không chính xác.")
                else:
                    st.warning("Vui lòng điền đầy đủ thông tin.")

            st.markdown("<div style='text-align: center; margin: 25px 0 20px 0; color: #64748B; font-size: 0.85rem; letter-spacing: 1px;'>─── HOẶC ───</div>", unsafe_allow_html=True)
            render_login_button(sidebar=False)
            st.markdown("<div style='text-align: center; margin-top: 15px; color: #94A3B8; font-size: 0.8rem; line-height: 1.4;'>💡 Đăng nhập Google sẽ mở tab mới.<br>Sau khi đăng nhập thành công, hãy sử dụng tab mới đó.</div>", unsafe_allow_html=True)
    
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
    """Kiểm tra quyền truy cập."""
    if not st.session_state.get("is_logged_in", False):
        st.session_state.show_login = True
        st.session_state.login_action = action_name
        st.rerun()
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
