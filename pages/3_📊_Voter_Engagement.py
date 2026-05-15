import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.ui_helper import set_premium_css, draw_module_header
from utils.gemini_client import generate_text
from utils.auth_helper import require_auth
import database

# Khởi tạo DB
database.init_db()
set_premium_css()

draw_module_header(
    "Văn phòng Cử tri & Kết nối Cộng đồng",
    "📊",
    "Quản lý kiến nghị cử tri và kết nối thông tin đa kênh."
)

tab1, tab2 = st.tabs(["📊 Quản lý Kiến nghị Cử tri", "🌐 Cổng thông tin HĐND (Public)"])

# --- TAB 1: QUẢN LÝ KIẾN NGHỊ ---
with tab1:
    st.markdown("### 📊 Theo dõi & Phân tích Kiến nghị")
    # Tải dữ liệu
    data = database.get_petitions()
    df = pd.DataFrame(data, columns=["id", "created_at", "voter_name", "district", "content", "category", "status", "resolution"])
    
    if not df.empty:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Tổng kiến nghị", len(df))
        k2.metric("Chưa xử lý", len(df[df['status'] == 'Mới']))
        k3.metric("Đang xử lý", len(df[df['status'] == 'Đang xử lý']))
        k4.metric("Hoàn thành", len(df[df['status'] == 'Đã xong']))
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            fig_cat = px.pie(df, names='category', hole=0.5, title="Phân loại Lĩnh vực")
            st.plotly_chart(fig_cat, use_container_width=True)
        with c2:
            cross = df.groupby(['district', 'status']).size().reset_index(name='count')
            fig_dist = px.bar(cross, x='district', y='count', color='status', title="Phân bổ Địa phương")
            st.plotly_chart(fig_dist, use_container_width=True)
            
        if st.button("🔍 CHẠY PHÂN TÍCH AI CHUYÊN SÂU", type="primary", use_container_width=True):
            if require_auth("Phân tích kiến nghị"):
                with st.spinner("AI đang tổng hợp dữ liệu..."):
                    p = f"Phân tích xu hướng kiến nghị cử tri:\n{df[['district', 'category', 'content']].to_string()}"
                    st.session_state.pet_ai = generate_text(p, use_pro=True)
        if "pet_ai" in st.session_state: st.markdown(st.session_state.pet_ai)
    else: st.info("Chưa có dữ liệu kiến nghị.")

    with st.expander("➕ Tiếp nhận kiến nghị mới"):
        with st.form("new_pet"):
            v = st.text_input("Tên cử tri"); d = st.selectbox("Địa phương", ["TP. Thanh Hóa", "Sầm Sơn", "Bỉm Sơn", "Hoằng Hóa", "Quảng Xương", "Thọ Xuân", "Nghi Sơn"])
            cat = st.selectbox("Lĩnh vực", ["Giao thông", "Môi trường", "Y tế", "Giáo dục", "Đất đai"])
            con = st.text_area("Nội dung"); sub = st.form_submit_button("Lưu")
            if sub and con: database.save_petition(v, d, con, cat); st.success("Đã lưu!"); st.rerun()

# --- TAB 2: CỔNG THÔNG TIN HĐND ---
with tab2:
    st.markdown("### 🌐 Kết nối Cổng thông tin Công cộng")
    st.caption("Truy cập trang tin tức và công bố thông tin dành cho cử tri (Web Portal).")
    st.components.v1.iframe("https://hdnd.vercel.app/", height=800, scrolling=True)
