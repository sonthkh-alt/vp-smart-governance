import streamlit as st
import os

def init_auth():
    """Khởi tạo trạng thái đăng nhập dựa trên Streamlit Native Auth."""
    # Streamlit Cloud cung cấp st.user tự động
    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False

def login_google():
    """Kích hoạt Google Login thật hoặc hướng dẫn cấu hình nếu thiếu 'chìa khóa'."""
    try:
        st.login("google")
    except Exception as e:
        # Nếu chưa cấu hình Secrets, hiện bảng hướng dẫn thay vì báo lỗi đỏ
        st.error("### 🔐 Cấu hình Đăng nhập Google")
        st.info(f"""
            Để kích hoạt luồng đăng nhập chuẩn 3 bước, bạn cần dán "chìa khóa" vào mục **Secrets** của Streamlit Cloud.
            
            **Hướng dẫn nhanh:**
            1. Truy cập [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
            2. Tạo OAuth Client ID (Web Application) với Redirect URI: 
               `https://hdndthanhhoa.streamlit.app/oauth2callback`
            3. Copy mã dán vào **Settings -> Secrets**:
            ```toml
            [auth]
            redirect_uri = "https://hdndthanhhoa.streamlit.app/oauth2callback"
            cookie_secret = "sondeptrai"

            [auth.google]
            client_id = "MÃ_CLIENT_ID_CỦA_BẠN"
            client_secret = "MÃ_BÍ_MẬT_CỦA_BẠN"
            server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
            ```
        """)
        if "Authlib" in str(e):
            st.warning("⚠️ Hệ thống đang cài đặt thư viện hỗ trợ (Authlib). Vui lòng chờ 1 phút rồi nhấn thử lại.")
        else:
            st.caption(f"Chi tiết kỹ thuật: {str(e)}")

def logout():
    """Bước 3: Đăng xuất và dọn dẹp phiên làm việc."""
    st.logout()

def check_auth_status():
    """Kiểm tra trạng thái đăng nhập một cách an toàn."""
    # Thử sử dụng Streamlit Native Auth nếu có
    try:
        if hasattr(st, "user"):
            # Một số phiên bản dùng .is_logged_in, số khác dùng kiểm tra email
            if getattr(st.user, "is_logged_in", False):
                return True
            if getattr(st.user, "email", None):
                return True
    except:
        pass
    
    # Quay lại sử dụng session_state nếu Native Auth không khả dụng
    return st.session_state.get("is_logged_in", False)

def get_user_info():
    """Lấy thông tin người dùng một cách an toàn."""
    try:
        if hasattr(st, "user") and (getattr(st.user, "is_logged_in", False) or getattr(st.user, "email", None)):
            return {
                "name": getattr(st.user, "name", "Người dùng"),
                "email": getattr(st.user, "email", ""),
                "picture": getattr(st.user, "picture", "https://www.gstatic.com/images/branding/product/2x/avatar_anonymous_128dp.png")
            }
    except:
        pass
    return st.session_state.get("user_info", None)

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
