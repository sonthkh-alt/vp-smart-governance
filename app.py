import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import streamlit as st

# THIẾT LẬP GIAO DIỆN FULL MÀN HÌNH
st.set_page_config(
    page_title="Smart Governance Platform",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.auth_helper import init_auth, ADMIN_EMAIL
from utils.ui_helper import set_premium_css

# === BẮT SỚM: Nếu đây là cửa sổ Popup quay về từ Google → xử lý ngay, không tải UI ===
_params = st.query_params
if _params.get("state") == "popup" and "code" in _params:
    _code = _params["code"]
    # Dùng st.html() (inline, KHÔNG phải iframe) để window.close() và localStorage hoạt động đúng
    st.html(f"""
        <script>
            localStorage.setItem('google_oauth_code', '{_code}');
            window.close();
        </script>
        <p style="font-family:sans-serif; text-align:center; padding:40px; color:#666;">
            ✅ Đăng nhập thành công! Cửa sổ này sẽ tự đóng...<br/>
            <small>Nếu không tự đóng, hãy đóng cửa sổ này và quay lại trang chính.</small>
        </p>
    """)
    st.stop()

# 1. Khởi tạo Auth ngay lập tức
init_auth()

# 2. Định nghĩa các trang
# Chú ý: Streamlit sẽ chạy script của trang được chọn.
pages = [
    st.Page("home.py", title="Trang chủ", icon="🏛️", default=True),
    st.Page("pages/3_🔍_Draft_Review.py", title="Thẩm tra Dự thảo NQ", icon="🔍"),
    st.Page("pages/2_📝_Drafting_Hub.py", title="Trung tâm Soạn thảo", icon="📝"),
    st.Page("pages/1_🏛️_Legislative_Center.py", title="Nghiệp vụ Dân cử", icon="🏛️"),
    st.Page("pages/4_🎓_Academic_Promotion.py", title="Học thuật & Chuyên gia", icon="🎓"),
]

# 3. Chỉ thêm trang Quản trị nếu là Admin
if st.session_state.get("is_logged_in") and st.session_state.user_info.get("email") == ADMIN_EMAIL:
    pages.append(st.Page("pages/5_⚙️_Administration.py", title="Quản trị Hệ thống", icon="⚙️"))

# 4. Cấu hình điều hướng chuyên nghiệp
pg = st.navigation(pages)

# Thiết lập giao diện chung (CSS) trước khi chạy trang
set_premium_css()

# Chạy trang đã chọn
pg.run()

# Vẽ thêm các thành phần tùy chỉnh vào Sidebar (Dưới menu điều hướng)
from utils.ui_helper import draw_sidebar
draw_sidebar()
