import streamlit as st
import os
import requests
import json

# Cấu hình Google OAuth
CLIENT_ID = st.secrets.get("auth", {}).get("google", {}).get("client_id")
CLIENT_SECRET = st.secrets.get("auth", {}).get("google", {}).get("client_secret")
REDIRECT_URI = "https://hdndthanhhoa.streamlit.app" # Trang chủ xử lý callback

def init_auth():
    """Xử lý Callback từ Google và duy trì trạng thái đăng nhập."""
    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False
        st.session_state.user_info = None

    # Kiểm tra nếu có mã callback từ Google trong URL
    params = st.query_params
    if "code" in params and not st.session_state.is_logged_in:
        code = params["code"]
        try:
            # Trao đổi mã (code) lấy Token
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            }
            response = requests.post(token_url, data=data)
            tokens = response.json()
            
            if "access_token" in tokens:
                # Lấy thông tin người dùng từ Access Token
                userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
                headers = {"Authorization": f"Bearer {tokens['access_token']}"}
                user_info = requests.get(userinfo_url, headers=headers).json()
                
                st.session_state.is_logged_in = True
                st.session_state.user_info = user_info
                
                # Xóa code khỏi URL để sạch sẽ
                st.query_params.clear()
                st.rerun()
        except Exception as e:
            st.error(f"Lỗi xác thực: {str(e)}")

def login_google():
    """Chuyển hướng người dùng đến trang đăng nhập Google."""
    if not CLIENT_ID or not CLIENT_SECRET:
        st.error("### 🔐 Thiếu cấu hình Google OAuth")
        st.info(f"""
            Vui lòng dán mã vào mục **Secrets** của Streamlit Cloud:
            ```toml
            [auth.google]
            client_id = "MÃ_CỦA_BẠN"
            client_secret = "MÃ_BÍ_MẬT_CỦA_BẠN"
            ```
        """)
        return

    # Tạo URL đăng nhập Google
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
        "&prompt=select_account"
    )
    
    # Chuyển hướng bằng Markdown/HTML (Streamlit không có lệnh redirect trực tiếp)
    st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{auth_url}\'">', unsafe_allow_html=True)
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

def require_auth(feature_name="tính năng này"):
    """
    Hàm kiểm tra quyền truy cập. 
    Nếu chưa đăng nhập, hiển thị thông báo và trả về False.
    """
    if not check_auth_status():
        st.warning(f"⚠️ Vui lòng đăng nhập để sử dụng **{feature_name}**.")
        st.markdown(f"""
            <div style="background: rgba(230, 57, 70, 0.1); padding: 15px; border-radius: 10px; border: 1px solid rgba(230, 57, 70, 0.3); margin-bottom: 20px;">
                <p style="color: #E63946; margin-bottom: 5px; font-weight: 600;">Quyền truy cập bị hạn chế</p>
                <p style="font-size: 0.9rem; color: #F8FAFC;">
                    Bạn cần đăng nhập bằng tài khoản Google được cấp phép hoặc liên hệ với 
                    <b>Hà Ngọc Sơn</b>, PCVP Đoàn ĐBQH và HĐND tỉnh Thanh Hóa để được hỗ trợ.
                </p>
            </div>
        """, unsafe_allow_html=True)
        return False
    return True
