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
                st.query_params.clear()
                st.rerun()
        except Exception as e:
            st.error(f"Lỗi hệ thống khi kết nối Google: {str(e)}")

def login_google():
    """Kích hoạt luồng Đăng nhập Google duy nhất."""
    if not CLIENT_ID or not CLIENT_SECRET:
        st.error("### 🔐 Thiếu thông tin kết nối Google")
        st.info("Vui lòng đảm bảo bạn đã dán mã ID và Secret vào Secrets với tên mục [my_google_app].")
        return

    # Xây dựng URL chuẩn
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": url_phan_hoi,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account"
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    
    st.markdown("### 🏛️ Đăng nhập Hệ thống")
    st.info("Sử dụng tài khoản Google để truy cập đầy đủ tính năng AI.")
    st.link_button("🔑 ĐĂNG NHẬP VỚI GOOGLE", auth_url, use_container_width=True, type="primary")
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
        st.warning(f"⚠️ Bạn cần đăng nhập để {action_name}. (Vui lòng liên hệ đồng chí Hà Ngọc Sơn, PCVP Đoàn ĐBQH và HĐND tỉnh để được hỗ trợ).")
        login_google()
        return False
    return True
