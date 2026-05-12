import streamlit as st
import os

def init_auth():
    """Khởi tạo trạng thái đăng nhập dựa trên Streamlit Native Auth."""
    # Streamlit Cloud cung cấp st.user tự động
    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False

def login_google():
    """Bước 1 & 2: Kích hoạt quy trình Đăng nhập Google chuẩn."""
    # Lệnh này sẽ mở cửa sổ Google, cho phép chọn tài khoản và nhập mật khẩu/2FA
    st.login("google")

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
