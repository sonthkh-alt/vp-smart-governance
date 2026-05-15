import streamlit as st
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from utils.storage_helper import upload_file, get_file_url, delete_file
from utils.vector_helper import vectorize_document
from utils.ui_helper import set_premium_css, draw_module_header, draw_sidebar
from utils.auth_helper import require_auth
import pandas as pd

# Khởi tạo DB
database.init_db()

# Áp dụng giao diện Premium
set_premium_css()

# Hiển thị Header
draw_module_header(
    "Knowledge Base",
    "📚",
    "Kho tri thức tập trung: Lưu trữ và quản lý tài liệu tham khảo cho toàn hệ thống."
)

# ─── TẢI LÊN TÀI LIỆU MỚI ──────────────────────────────────────────────────
with st.expander("➕ Tải lên tài liệu mới vào Kho tri thức", expanded=False):
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_files = st.file_uploader("Chọn các file tài liệu (PDF, DOCX):", type=["pdf", "docx"], accept_multiple_files=True)
    with col2:
        target_module = st.selectbox("Phân loại vào Module:", ["Chung", "Phát biểu", "Thẩm tra", "Kiến nghị", "Văn bản"])
    
    if st.button("🚀 BẮT ĐẦU TẢI LÊN", use_container_width=True, type="primary"):
        if require_auth("Tải lên tài liệu"):
            if uploaded_files:
                progress_bar = st.progress(0)
                for i, file in enumerate(uploaded_files):
                    with st.spinner(f"Đang tải lên {file.name}..."):
                        upload_file(file, module=target_module)
                    progress_bar.progress((i + 1) / len(uploaded_files))
                st.success(f"Đã tải lên thành công {len(uploaded_files)} tài liệu!")
                st.rerun()
            else:
                st.warning("Vui lòng chọn file trước khi tải lên.")

st.markdown("---")

# ─── QUẢN LÝ DANH SÁCH TÀI LIỆU ─────────────────────────────────────────────
st.markdown("### 📋 Danh sách tài liệu hiện có")

docs = database.get_all_documents()

if docs:
    # Chuyển đổi sang DataFrame để hiển thị đẹp hơn (tùy chọn) hoặc dùng bảng
    df_data = []
    for d in docs:
        size_mb = round(d['file_size'] / (1024 * 1024), 2)
        df_data.append({
            "ID": d['id'],
            "Ngày tải": d['created_at'],
            "Tên file": d['file_name'],
            "Loại": d['module'],
            "Dung lượng": f"{size_mb} MB",
            "Người tải": d['uploader_email'],
            "Path": d['storage_path']
        })
    
    # Hiển thị từng file với các nút thao tác
    for doc in df_data:
        with st.container():
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            with c1:
                st.markdown(f"**{doc['Tên file']}**")
                st.caption(f"📅 {doc['Ngày tải']} | 👤 {doc['Người tải']} | 🏷️ {doc['Loại']}")
            with c2:
                # Nút xem/tải
                url = get_file_url(doc['Path'])
                if url:
                    st.link_button("🌐 Xem/Tải", url, use_container_width=True)
            with c3:
                # Nút Xóa (Chỉ Admin hoặc người tải mới được xóa - tạm thời cho Admin)
                if st.button("🗑️ Xóa", key=f"del_{doc['ID']}", use_container_width=True):
                    if require_auth("Xóa tài liệu"):
                        if delete_file(doc['ID'], doc['Path']):
                            st.success(f"Đã xóa {doc['Tên file']}")
                            st.rerun()
            with c4:
                # Nút Vectorize
                is_vec = d['is_vectorized'] == 1
                btn_label = "✅ Đã xử lý" if is_vec else "🧠 Vectorize"
                if st.button(btn_label, key=f"vec_{doc['ID']}", use_container_width=True, disabled=is_vec):
                    if require_auth("Xử lý dữ liệu AI"):
                        with st.spinner(f"AI đang đọc hiểu: {doc['Tên file']}..."):
                            success, msg = vectorize_document(doc['ID'], doc['Path'], doc['Tên file'])
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
            st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.2;'>", unsafe_allow_html=True)
else:
    st.info("Kho tri thức hiện đang trống. Hãy tải lên tài liệu đầu tiên!")

st.markdown("---")
st.caption("Hệ thống Kho tri thức - Lưu trữ tập trung trên Supabase Storage.")
