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

from utils.auth_helper import init_auth
from utils.ui_helper import set_premium_css, draw_module_header

# Xử lý đăng nhập Google ngay khi tải trang
init_auth()

# Áp dụng giao diện Premium
set_premium_css()

# Hiển thị Hero Header
draw_module_header(
    "Smart Governance Platform",
    "🏛️",
    "Hệ sinh thái Quản trị dựa trên Dữ liệu và AI dành cho Cơ quan Dân cử"
)

st.markdown("### 🌟 Các Trung tâm Nghiệp vụ Thông minh")

# Dashboard Grid Row 1
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🏛️ Nghiệp vụ Dân cử")
    st.markdown("Trợ lý Kỳ họp, Thẩm tra Chính sách và Thư viện Pháp luật tập trung.")
    st.page_link("pages/1_🏛️_Legislative_Center.py", label="Truy cập Trung tâm", icon="🚀")
    st.markdown('</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Trung tâm Soạn thảo")
    st.markdown("Soạn thảo văn bản chuẩn NĐ 30, bài phát biểu Lãnh đạo và Soát xét lỗi AI.")
    st.page_link("pages/2_📝_Drafting_Hub.py", label="Truy cập Trung tâm", icon="🚀")
    st.markdown('</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Cử tri & Kết nối")
    st.markdown("Quản lý kiến nghị cử tri, phân tích điểm nóng và Cổng thông tin công cộng.")
    st.page_link("pages/3_📊_Voter_Engagement.py", label="Truy cập Trung tâm", icon="🚀")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Dashboard Grid Row 2
col4, col5, col6 = st.columns(3)
with col4:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🎓 Học thuật & Chuyên gia")
    st.markdown("Lộ trình PGS cá nhân hóa và quản lý công trình nghiên cứu khoa học.")
    st.page_link("pages/4_🎓_Academic_Promotion.py", label="Truy cập Trung tâm", icon="🚀")
    st.markdown('</div>', unsafe_allow_html=True)
with col5:
    from utils.auth_helper import ADMIN_EMAIL
    is_admin = st.session_state.get("is_logged_in") and st.session_state.user_info.get("email") == ADMIN_EMAIL
    if is_admin:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### ⚙️ Quản trị Hệ thống")
        st.markdown("Quản lý người dùng, phân quyền, cấu hình AI và giám sát nhật ký.")
        st.page_link("pages/5_⚙️_Administration.py", label="Truy cập Hệ thống", icon="🛠️")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="glass-card" style="opacity: 0.5; cursor: not-allowed;">', unsafe_allow_html=True)
        st.markdown("### 🔒 Khu vực Quản trị")
        st.markdown("Dành riêng cho Quản trị viên hệ thống.")
        st.button("Hạn chế truy cập", disabled=True, key="admin_locked", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── CỔNG THÔNG TIN HĐND ──────────────────────────────────────────────────────
st.markdown("### 🌍 Cửa sổ số HĐND")
st.markdown('<div class="glass-card" style="border: 1px solid #457B9D; background: rgba(69, 123, 157, 0.1);">', unsafe_allow_html=True)
c_left, c_right = st.columns([2, 1])
with c_left:
    st.markdown("#### 🌍 Cổng thông tin Hội đồng Nhân dân")
    st.markdown("Kết nối thông tin trực tiếp từ website công cộng dành cho Cử tri.")
with c_right:
    # We still use the link but it's now integrated in Center 3 as well
    st.page_link("pages/3_📊_Voter_Engagement.py", label="Truy cập Cổng tin", icon="🌐", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.info("👈 Hãy chọn một phân hệ từ thanh điều hướng bên trái (Sidebar) để bắt đầu sử dụng.")

st.markdown("---")

# ─── SYSTEM STATUS PANEL ──────────────────────────────────────────────────────
st.markdown("### 🔧 Trạng thái Hệ thống")

import os
from dotenv import load_dotenv
load_dotenv(override=True)

sc1, sc2, sc3, sc4 = st.columns(4)

# Kiểm tra API Key
from utils.gemini_client import _get_api_key
api_key = _get_api_key()
with sc1:
    if api_key:
        st.success("✅ **Gemini API Key**\nĐã cấu hình")
    else:
        st.error("❌ **Gemini API Key**\nChưa cấu hình")

# Kiểm tra ChromaDB
with sc2:
    if os.path.exists("chroma_db"):
        st.success("✅ **Knowledge Base**\nĐã có dữ liệu")
    else:
        st.warning("⚠️ **Knowledge Base**\nChưa có dữ liệu")

# Kiểm tra DB
with sc3:
    if os.path.exists("draft_history.db"):
        st.success("✅ **SQLite DB**\nHoạt động bình thường")
    else:
        st.warning("⚠️ **SQLite DB**\nChưa khởi tạo")

# Phiên bản
with sc4:
    st.info("ℹ️ **Platform Version**\nv2.5 — Optimized AI")

# Footer
st.markdown("""
    <div style="text-align: center; color: #457B9D; font-size: 0.8rem; padding: 2rem;">
        © 2026 Smart Governance Platform · Powered by Google Gemini AI
    </div>
""", unsafe_allow_html=True)
