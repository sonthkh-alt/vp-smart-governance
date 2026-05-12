try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st
from utils.ui_helper import set_premium_css, draw_module_header, draw_sidebar

st.set_page_config(
    page_title="Smart Governance Platform",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Áp dụng giao diện Premium & Sidebar
set_premium_css()
draw_sidebar()

# Hiển thị Hero Header
draw_module_header(
    "Smart Governance Platform",
    "🏛️",
    "Hệ sinh thái Quản trị dựa trên Dữ liệu và AI dành cho Cơ quan Dân cử"
)

st.markdown("### 🌟 Phân hệ Lõi & Nghiệp vụ")

# Dashboard Grid
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🏛️ Trợ lý Kỳ họp")
    st.markdown("Đối soát văn bản, phân tích số liệu và gợi ý chất vấn bằng công nghệ RAG chuyên sâu.")
    st.page_link("pages/1_🏛️_Legislative_Intelligence.py", label="Truy cập Phân hệ", icon="🚀")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Kiến nghị Cử tri")
    st.markdown("Phân tích xu hướng, bản đồ hóa và theo dõi tiến độ giải quyết kiến nghị của cử tri.")
    st.page_link("pages/2_📊_Petitions.py", label="Truy cập Phân hệ", icon="🚀")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### ⚖️ Thẩm tra Chính sách")
    st.markdown("Đánh giá tác động và tính hợp hiến của chính sách với kinh tế xanh, kinh tế biển.")
    st.page_link("pages/4_⚖️_Policy_Review.py", label="Truy cập Phân hệ", icon="🚀")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Quản trị Điều hành")
    st.markdown("Số hóa hồ sơ chuyên viên và quy trình soạn thảo văn bản chuyên nghiệp chuẩn NĐ 30.")
    st.page_link("pages/3_📝_Document_Drafting.py", label="Truy cập Phân hệ", icon="🚀")
    st.markdown('</div>', unsafe_allow_html=True)

with col5:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📋 Kiểm soát Văn bản")
    st.markdown("Soát lỗi, tối ưu văn phong hành chính và kiểm tra logic quản lý nhà nước tự động.")
    st.page_link("pages/6_📋_Document_Review.py", label="Truy cập Phân hệ", icon="🚀")
    st.markdown('</div>', unsafe_allow_html=True)

with col6:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🎓 Học thuật & Nâng hạng")
    st.markdown("Lộ trình PGS cá nhân hóa, quản lý công trình khoa học và AI gợi ý đề tài nghiên cứu.")
    st.page_link("pages/5_🎓_Academic_Promotion.py", label="Truy cập Phân hệ", icon="🚀")
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
api_key = os.getenv("GEMINI_API_KEY")
with sc1:
    if api_key:
        st.success("✅ **Gemini API Key**\nĐã cấu hình")
    else:
        st.error("❌ **Gemini API Key**\nChưa cấu hình trong .env")

# Kiểm tra ChromaDB
with sc2:
    if os.path.exists("chroma_db"):
        st.success("✅ **Knowledge Base**\nĐã có dữ liệu")
    else:
        st.warning("⚠️ **Knowledge Base**\nChưa có dữ liệu (cần upload tài liệu)")

# Kiểm tra DB
with sc3:
    if os.path.exists("draft_history.db"):
        st.success("✅ **SQLite DB**\nHoạt động bình thường")
    else:
        st.warning("⚠️ **SQLite DB**\nChưa được khởi tạo")

# Phiên bản
with sc4:
    st.info("ℹ️ **Platform Version**\nv2.1 — Python 3.14 Compatible")

# Footer
st.markdown("""
    <div style="text-align: center; color: #457B9D; font-size: 0.8rem; padding: 2rem;">
        © 2026 Smart Governance Platform · Powered by Google Gemini AI
    </div>
""", unsafe_allow_html=True)
