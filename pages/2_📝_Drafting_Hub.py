import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.ai_helper import generate_document_content, check_legal_compliance
from utils.doc_helper import extract_text_from_pdf, extract_text_from_docx, create_nd30_document
from utils.ui_helper import set_premium_css, draw_module_header
from utils.auth_helper import require_auth
from utils.gemini_client import generate_text
import database
import io
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Khởi tạo DB
database.init_db()
set_premium_css()

# Khởi tạo Session State
if "rev_text_content" not in st.session_state:
    st.session_state.rev_text_content = ""

draw_module_header(
    "Trung tâm Soạn thảo & Kiểm soát Chất lượng",
    "📝",
    "Hệ sinh thái AI hỗ trợ soạn thảo văn bản hành chính, bài phát biểu và soát xét lỗi chuyên nghiệp."
)
st.caption("🚀 Phiên bản: 2.5.1 (Cập nhật tính năng Upload file)")

tab1, tab2, tab3 = st.tabs(["📝 Soạn thảo Văn bản", "🎤 Soạn thảo Phát biểu", "📋 Soát xét & Kiểm lỗi"])

# --- Cấu hình AI chung cho trang ---
with st.sidebar:
    st.markdown("### 🤖 Cấu hình AI")
    ai_provider = st.radio("Chọn mô hình AI ưu tiên:", ["Google Gemini", "Anthropic Claude"], index=0, key="global_ai_provider")
    provider_key = "gemini" if ai_provider == "Google Gemini" else "claude"

# --- TAB 1: SOẠN THẢO VĂN BẢN ---
with tab1:
    st.markdown("### 📝 Tham mưu & Soạn thảo chuẩn NĐ 30")
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        doc_type = st.selectbox("Loại văn bản:", ["Tự động", "Công văn", "Báo cáo", "Quyết định", "Nghị quyết", "Tờ trình"], key="draft_type")
        prompt = st.text_area("Yêu cầu chi tiết:", height=150, placeholder="Ví dụ: Soạn công văn trả lời đề xuất kinh phí...", key="draft_prompt")
        legal_data = st.text_area("Căn cứ pháp lý (NotebookLM):", height=150, placeholder="Dán nội dung luật hoặc quy định tại đây...", key="draft_legal")
        ref_files = st.file_uploader("Tài liệu tham khảo:", type=["pdf", "docx"], accept_multiple_files=True, key="draft_ref")
        if st.button("🚀 TẠO DỰ THẢO VĂN BẢN", type="primary", use_container_width=True, key="draft_run"):
            if require_auth("Soạn thảo văn bản"):
                with st.spinner(f"AI ({ai_provider}) đang soạn thảo..."):
                    context = ""
                    if ref_files:
                        for f in ref_files: context += (extract_text_from_pdf(f) if f.name.endswith(".pdf") else extract_text_from_docx(f)) + "\n"
                    res = generate_document_content(prompt, doc_type=doc_type, context=context, notebook_lm_data=legal_data, provider=provider_key)
                    if isinstance(res, dict) and "error" not in res:
                        st.session_state.draft_res = res.get("noi_dung_chinh", "")
                        st.session_state.draft_dict = res
                        database.save_draft(doc_type, prompt, res)
                    else: st.error(f"Lỗi: {res.get('error') if isinstance(res, dict) else res}")
    with col2:
        if "draft_res" in st.session_state:
            edited = st.text_area("Nội dung dự thảo:", value=st.session_state.draft_res, height=400, key="draft_edit")
            st.session_state.draft_res = edited
            if st.button("📄 Xuất file Word chuẩn NĐ 30", use_container_width=True, type="primary", key="draft_word"):
                dict_meta = st.session_state.get("draft_dict", {})
                dict_meta["noi_dung_chinh"] = edited
                out = create_nd30_document(dict_meta)
                st.download_button("⬇️ Tải xuống (.docx)", out.getvalue(), "VanBan_DuThao.docx", key="draft_dl")
        else: st.info("Dự thảo sẽ hiển thị ở đây.")

# --- TAB 2: SOẠN THẢO PHÁT BIỂU ---
with tab2:
    st.markdown("### 🎤 Trợ lý soạn thảo bài phát biểu Lãnh đạo")
    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        s_role = st.text_input("Chức danh người phát biểu:", placeholder="Ví dụ: Chủ tịch HĐND tỉnh", key="speech_role")
        s_event = st.text_input("Tên sự kiện:", placeholder="Ví dụ: Kỳ họp thứ 20 HĐND tỉnh", key="speech_event")
        s_key = st.text_area("Ý chính cần nhấn mạnh:", height=150, key="speech_key")
        if st.button("🚀 SOẠN THẢO BÀI PHÁT BIỂU", type="primary", use_container_width=True, key="speech_run"):
            if require_auth("Soạn thảo phát biểu"):
                prompt = f"Soạn bài phát biểu cho {s_role} tại {s_event}. Ý chính: {s_key}"
                with st.spinner(f"AI ({ai_provider}) đang soạn thảo..."):
                    res = generate_document_content(prompt, doc_type="Bài phát biểu", provider=provider_key)
                    if isinstance(res, dict) and "error" not in res:
                        st.session_state.speech_res = res.get("noi_dung_chinh", "")
                        database.save_draft("Bài phát biểu", prompt, res)
                    else: st.error("Lỗi tạo nội dung.")
    with c2:
        if "speech_res" in st.session_state:
            s_edit = st.text_area("Nội dung bài phát biểu:", value=st.session_state.speech_res, height=400, key="speech_edit")
            st.session_state.speech_res = s_edit
            if st.button("📄 Xuất file Word Phát biểu", use_container_width=True, key="speech_word"):
                doc = Document()
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(f"BÀI PHÁT BIỂU CỦA {s_role.upper()}\nTẠI {s_event.upper()}")
                run.bold = True
                for line in s_edit.split('\n'): doc.add_paragraph(line)
                out = io.BytesIO(); doc.save(out)
                st.download_button("⬇️ Tải xuống (.docx)", out.getvalue(), "BaiPhatBieu.docx", key="speech_dl")
        else: st.info("Bài phát biểu sẽ hiển thị ở đây.")

# --- TAB 3: SOÁT XÉT & KIỂM LỖI ---
with tab3:
    st.markdown("### 📋 Kiểm soát Chất lượng & Văn phong")
    cl, cr = st.columns([1, 1.3], gap="large")
    with cl:
        st.markdown("#### 📥 Nhập Văn bản")
        rev_file = st.file_uploader("Tải lên văn bản (PDF/DOCX):", type=["pdf", "docx"], key="rev_file")
        
        # Xử lý trích xuất text từ file upload
        if rev_file and ("last_rev_file" not in st.session_state or st.session_state.last_rev_file != rev_file.name):
            with st.spinner("🔍 Đang trích xuất văn bản..."):
                extracted_text = ""
                if rev_file.name.endswith(".pdf"):
                    extracted_text = extract_text_from_pdf(rev_file)
                else:
                    extracted_text = extract_text_from_docx(rev_file)
                
                if extracted_text.strip():
                    st.session_state.rev_text_content = extracted_text
                else:
                    st.warning("⚠️ Không thể trích xuất văn bản từ file này hoặc file trống.")
                st.session_state.last_rev_file = rev_file.name

        # Hiển thị text area - Tự động đồng bộ với st.session_state.rev_text_content
        st.text_area("Nội dung văn bản cần kiểm tra:", height=300, key="rev_text_content")
        
        rev_focus = st.multiselect("Trọng tâm kiểm tra:", ["Chính tả & Ngữ pháp", "Thể thức NĐ 30", "Văn phong hành chính", "Logic quản lý"], default=["Chính tả & Ngữ pháp", "Văn phong hành chính"], key="rev_focus")
        if st.button("🚀 BẮT ĐẦU KIỂM TRA", type="primary", use_container_width=True, key="rev_run"):
            if require_auth("Kiểm tra văn bản"):
                if not st.session_state.rev_text_content.strip():
                    st.error("⚠️ Vui lòng tải file hoặc nhập nội dung văn bản!")
                else:
                    with st.spinner(f"AI ({ai_provider}) đang soát lỗi..."):
                        p = f"Hãy soát lỗi và tối ưu văn bản sau. Trọng tâm: {', '.join(rev_focus)}\n\nNội dung:\n{st.session_state.rev_text_content}"
                        res = generate_text(p, use_pro=True, provider=provider_key)
                        st.session_state.rev_res = res
    with cr:
        if "rev_res" in st.session_state:
            st.markdown(st.session_state.rev_res)
            st.download_button("⬇️ Tải Báo cáo (.txt)", st.session_state.rev_res.encode("utf-8"), "BaoCao_SoatLoi.txt", key="rev_dl")
        else: st.info("Kết quả soát lỗi sẽ hiển thị ở đây.")
