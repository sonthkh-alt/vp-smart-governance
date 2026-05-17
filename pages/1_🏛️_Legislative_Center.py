import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.rag_engine import process_documents, query_rag
from utils.ui_helper import set_premium_css, draw_module_header
from utils.auth_helper import require_auth
from utils.gemini_client import generate_text
from utils.doc_helper import extract_text_from_pdf, extract_text_from_docx, create_nd30_document
from utils.storage_helper import upload_file, get_file_url, delete_file
from utils.vector_helper import vectorize_document
import database
import io
import pandas as pd
import plotly.express as px

# Áp dụng giao diện Premium
database.init_db()
set_premium_css()

draw_module_header(
    "Nghiệp vụ Dân cử & Thư viện Pháp luật",
    "🏛️",
    "Trung tâm trí tuệ hỗ trợ Thẩm tra, Kỳ họp và Quản trị Tri thức tập trung."
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏛️ Trợ lý Kỳ họp (RAG)", 
    "⚖️ Thẩm tra Chính sách", 
    "📊 Kiến nghị Cử tri", 
    "🌐 Cổng thông tin HĐND", 
    "📚 Thư viện & Kho tri thức"
])

# --- TAB 1: TRỢ LÝ KỲ HỌP ---
with tab1:
    st.markdown("### 🤖 Trợ lý Phân tích & Gợi ý Chất vấn")
    col1, col2 = st.columns([1, 1.2], gap="large")
    
    with col1:
        st.markdown("#### 📥 Cập nhật tài liệu Kỳ họp")
        st.info("Tải lên báo cáo, nghị quyết phục vụ đối soát số liệu.")
        uploaded_files = st.file_uploader("Chọn tài liệu (PDF, DOCX)", type=["pdf", "docx"], accept_multiple_files=True, key="rag_upload")
        if st.button("🔄 Vector hóa tài liệu", use_container_width=True, key="rag_btn"):
            if require_auth("Vector hóa tài liệu"):
                if not uploaded_files:
                    st.warning("⚠️ Vui lòng tải lên ít nhất 1 tài liệu!")
                else:
                    with st.spinner("Đang trích xuất và Vector hóa..."):
                        status, msg = process_documents(uploaded_files)
                        if status: st.success("✅ Đã xây dựng xong CSDL tri thức!")
                        else: st.error(f"❌ Có lỗi: {msg}")

    with col2:
        st.markdown("#### 🧠 Phân tích Nghiệp vụ")
        analysis_type = st.selectbox("Chọn tác vụ phân tích:", [
            "1. So sánh số liệu (Tìm điểm mâu thuẫn)",
            "2. Đề xuất danh sách Câu hỏi Chất vấn",
            "3. Kiểm tra tính tuân thủ Nghị quyết HĐND",
            "4. Phân tích điểm nghẽn Ngân sách",
            "5. Tóm tắt rủi ro chính sách",
            "6. Đặt câu hỏi tùy chọn (Tự nhập)"
        ], key="rag_task")
        
        custom_query = ""
        if "6" in analysis_type:
            custom_query = st.text_area("Nhập yêu cầu cụ thể:", placeholder="Ví dụ: Chỉ ra các rủi ro trong đầu tư công...", key="rag_custom")
        
        if st.button("🚀 THỰC HIỆN PHÂN TÍCH", type="primary", use_container_width=True, key="rag_run"):
            if require_auth("Phân tích AI"):
                query = custom_query if custom_query.strip() else analysis_type
                with st.spinner("🧠 AI đang lập luận logic..."):
                    response = query_rag(query)
                    if response and not response.startswith("Lỗi"):
                        st.markdown("#### 📊 Kết quả Phản biện:")
                        st.info(response)
                    else: st.error(response)

# --- TAB 2: THẨM TRA CHÍNH SÁCH ---
with tab2:
    st.markdown("### ⚖️ Đánh giá Tác động & Thẩm quyền")
    col_left, col_right = st.columns([1, 1.5], gap="large")
    
    with col_left:
        p_name = st.text_input("Tên dự thảo chính sách", key="policy_name_in")
        p_file = st.file_uploader("Tải file dự thảo (PDF/DOCX)", type=["pdf", "docx"], key="policy_upload")
        p_focus = st.multiselect("Trọng tâm Thẩm tra:", [
            "Tính hợp pháp & Thẩm quyền ban hành", "Tác động Ngân sách", "Tác động Kinh tế - Xã hội", "Kinh tế xanh", "An sinh xã hội"
        ], default=["Tính hợp pháp & Thẩm quyền ban hành"], key="policy_focus")

        if st.button("🚀 BẮT ĐẦU THẨM TRA AI", type="primary", use_container_width=True, key="policy_run"):
            if require_auth("Thẩm tra chính sách"):
                if not p_file or not p_name.strip(): st.error("⚠️ Vui lòng điền đủ thông tin!")
                else:
                    with st.spinner("🧠 AI đang soạn báo cáo thẩm tra..."):
                        text = extract_text_from_pdf(p_file) if p_file.name.endswith(".pdf") else extract_text_from_docx(p_file)
                        prompt = f"Thẩm tra dự thảo: {p_name}\nTrọng tâm: {', '.join(p_focus)}\nNội dung:\n{text[:8000]}"
                        res = generate_text(prompt, use_pro=True)
                        st.session_state.p_res = res
                        st.session_state.p_n = p_name
                        database.save_policy_review(p_name, res)
                        st.success("✅ Hoàn tất!")

    with col_right:
        st.markdown("#### 📋 Báo cáo Thẩm tra AI")
        if "p_res" in st.session_state:
            st.markdown(st.session_state.p_res)
            if st.button("📄 Xuất Word (NĐ 30)", key="policy_word"):
                content_dict = {
                    "co_quan_ban_hanh": "BAN KINH TẾ - NGÂN SÁCH", "so_ky_hieu": "BC/HĐND",
                    "dia_danh_ngay_thang": "Thanh Hóa, ngày... tháng... năm...", "loai_van_ban": "BÁO CÁO THẨM TRA",
                    "trich_yeu": f"Thẩm tra {st.session_state.p_n}", "noi_dung_chinh": st.session_state.p_res,
                    "noi_nhan": ["- Thường trực HĐND;", "- Lưu VT."], "quyen_han_ky": "TRƯỞNG BAN", "nguoi_ky": "[...]"
                }
                out = create_nd30_document(content_dict)
                st.download_button("⬇️ Tải file .docx", out.getvalue(), f"ThamTra_{st.session_state.p_n}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else: st.info("Kết quả sẽ hiển thị ở đây.")

# --- TAB 3: KIẾN NGHỊ CỬ TRI ---
with tab3:
    st.markdown("### 📊 Theo dõi & Phân tích Kiến nghị Cử tri")
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
            
        if st.button("🔍 CHẠY PHÂN TÍCH AI CHUYÊN SÂU", type="primary", use_container_width=True, key="policy_pet_ai_btn"):
            if require_auth("Phân tích kiến nghị"):
                with st.spinner("AI đang tổng hợp dữ liệu..."):
                    p = f"Phân tích xu hướng kiến nghị cử tri:\n{df[['district', 'category', 'content']].to_string()}"
                    st.session_state.pet_ai = generate_text(p, use_pro=True)
        if "pet_ai" in st.session_state: st.markdown(st.session_state.pet_ai)
    else: st.info("Chưa có dữ liệu kiến nghị.")

    with st.expander("➕ Tiếp nhận kiến nghị mới"):
        with st.form("new_pet_sub"):
            v = st.text_input("Tên cử tri"); d = st.selectbox("Địa phương", ["TP. Thanh Hóa", "Sầm Sơn", "Bỉm Sơn", "Hoằng Hóa", "Quảng Xương", "Thọ Xuân", "Nghi Sơn"])
            cat = st.selectbox("Lĩnh vực", ["Giao thông", "Môi trường", "Y tế", "Giáo dục", "Đất đai"])
            con = st.text_area("Nội dung"); sub = st.form_submit_button("Lưu")
            if sub and con: database.save_petition(v, d, con, cat); st.success("Đã lưu!"); st.rerun()

# --- TAB 4: CỔNG THÔNG TIN HĐND ---
with tab4:
    st.markdown("### 🌐 Cổng thông tin Công cộng dành cho Cử tri")
    st.caption("Truy cập trang tin tức và công bố thông tin phục vụ Cử tri (Web Portal).")
    st.components.v1.iframe("https://hdnd.vercel.app/", height=800, scrolling=True)

# --- TAB 5: THƯ VIỆN & KHO TRI THỨC ---
with tab5:
    st.markdown("### 📚 Quản trị Tài liệu & Thư viện Số")
    with st.expander("➕ Tải tài liệu lên Kho tri thức", expanded=False):
        c1, c2 = st.columns([2, 1])
        u_files = c1.file_uploader("Chọn file:", type=["pdf", "docx"], accept_multiple_files=True, key="lib_upload")
        u_mod = c2.selectbox("Phân loại:", ["Chung", "Phát biểu", "Thẩm tra", "Kiến nghị"], key="lib_mod")
        if st.button("🚀 TẢI LÊN KHO", use_container_width=True, key="lib_push"):
            if require_auth("Tải lên tài liệu"):
                if u_files:
                    for f in u_files: upload_file(f, module=u_mod)
                    st.success("Đã tải lên thành công!")
                    st.rerun()

    st.markdown("#### 📋 Danh mục tài liệu")
    docs = database.get_all_documents()
    if docs:
        for d in docs:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            col1.markdown(f"**{d['file_name']}**")
            col1.caption(f"📅 {d['created_at']} | 👤 {d['uploader_email']} | 🏷️ {d['module']}")
            url = get_file_url(d['storage_path'])
            if url: col2.link_button("🌐 Xem/Tải", url, use_container_width=True)
            if col3.button("🗑️ Xóa", key=f"del_{d['id']}", use_container_width=True):
                if require_auth("Xóa tài liệu") and delete_file(d['id'], d['storage_path']): st.rerun()
            is_v = d['is_vectorized'] == 1
            if col4.button("✅" if is_v else "🧠 Vector", key=f"v_{d['id']}", disabled=is_v, use_container_width=True):
                if require_auth("AI Vectorize"):
                    with st.spinner("Đang xử lý..."):
                        s, m = vectorize_document(d['id'], d['storage_path'], d['file_name'])
                        if s: st.success(m); st.rerun()
                        else: st.error(m)
            st.markdown("---")
    else: st.info("Kho tri thức trống.")
