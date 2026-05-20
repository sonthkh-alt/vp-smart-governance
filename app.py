import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules['pysqlite3']
except ImportError:
    pass

import sys
import os
path = os.path.abspath(os.path.dirname(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

import streamlit as st

# THIẾT LẬP GIAO DIỆN FULL MÀN HÌNH
st.set_page_config(
    page_title="Smart Governance Platform",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

try:
    from utils.auth_helper import init_auth, ADMIN_EMAIL
    from utils.ui_helper import set_premium_css, draw_sidebar
except KeyError as e:
    if e.args[0] == 'utils':
        st.rerun()
    raise


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

# ─── ĐIỀU HƯỚNG VÀ TRÁNH REDIRECT LOCK-IN ────────────────────────────────────
# Tự động nhận diện trang đang chạy để reset màn hình đăng nhập khi chuyển trang
current_page = pg.title
last_page = st.session_state.get("last_page_tracker")
if last_page != current_page:
    # Nếu người dùng click chuyển trang khác, tắt màn hình đăng nhập để tránh kẹt
    st.session_state.show_login = False
    st.session_state.last_page_tracker = current_page

# Thiết lập giao diện chung (CSS) trước khi chạy trang
set_premium_css()

# Chạy trang đã chọn
pg.run()

# Vẽ thêm các thành phần tùy chỉnh vào Sidebar (Dưới menu điều hướng)
draw_sidebar()
