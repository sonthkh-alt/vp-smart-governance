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

# 1. Khởi tạo Auth ngay lập tức
init_auth()

# 2. Định nghĩa các trang
# Chú ý: Streamlit sẽ chạy script của trang được chọn.
pages = [
    st.Page("home.py", title="Trang chủ", icon="🏛️", default=True),
    st.Page("pages/1_🏛️_Legislative_Intelligence.py", title="Trợ lý Kỳ họp", icon="🏛️"),
    st.Page("pages/2_📊_Petitions.py", title="Kiến nghị Cử tri", icon="📊"),
    st.Page("pages/3_📝_Document_Drafting.py", title="Quản trị Điều hành", icon="📝"),
    st.Page("pages/4_⚖️_Policy_Review.py", title="Thẩm tra Chính sách", icon="⚖️"),
    st.Page("pages/5_🎓_Academic_Promotion.py", title="Học thuật & Nâng hạng", icon="🎓"),
    st.Page("pages/6_📋_Document_Review.py", title="Kiểm soát Văn bản", icon="📋"),
    st.Page("pages/8_🌍_Portal.py", title="Cổng thông tin HĐND", icon="🌍"),
]

# 3. Chỉ thêm trang Quản trị nếu là Admin
if st.session_state.get("is_logged_in") and st.session_state.user_info.get("email") == ADMIN_EMAIL:
    pages.append(st.Page("pages/7_⚙️_Administration.py", title="Quản trị Hệ thống", icon="⚙️"))

# 4. Cấu hình điều hướng chuyên nghiệp
pg = st.navigation(pages)

# Thiết lập giao diện chung (CSS) trước khi chạy trang
set_premium_css()

# Chạy trang đã chọn
pg.run()

# Vẽ thêm các thành phần tùy chỉnh vào Sidebar (Dưới menu điều hướng)
from utils.ui_helper import draw_sidebar
draw_sidebar()
