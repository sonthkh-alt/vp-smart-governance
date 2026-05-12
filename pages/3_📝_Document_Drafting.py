import streamlit as st
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.ai_helper import generate_document_content, check_legal_compliance
from utils.doc_helper import extract_text_from_pdf, extract_text_from_docx, create_nd30_document
from utils.ui_helper import set_premium_css, draw_module_header, draw_sidebar
from utils.auth_helper import require_auth
from docx import Document
import io
import database

# Khởi tạo DB
database.init_db()

# Áp dụng giao diện Premium
set_premium_css()

# Hiển thị Header
draw_module_header(
    "Document Drafting",
    "📝",
    "Trợ lý ảo Tham mưu Văn bản: Số hóa quy trình soạn thảo chuẩn Nghị định 30."
)

# Khởi tạo session state để lưu trữ dữ liệu tạm
if "generated_draft" not in st.session_state:
    st.session_state.generated_draft = ""
if "generated_agency_name" not in st.session_state:
    st.session_state.generated_agency_name = ""
if "final_docx_bytes" not in st.session_state:
    st.session_state.final_docx_bytes = None
if "selected_template_name" not in st.session_state:
    st.session_state.selected_template_name = ""
if "legal_check_result" not in st.session_state:
    st.session_state.legal_check_result = ""

# -- SIDEBAR: QUẢN LÝ TEMPLATE --
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Qu%E1%BB%91c_huy_Vi%E1%BB%87t_Nam.svg/1024px-Qu%E1%BB%91c_huy_Vi%E1%BB%87t_Nam.svg.png", width=150)
    st.markdown("### Đề Cương / Khung Mẫu (Tùy chọn)")
    st.info("Nếu bạn có một bản nháp hoặc khung sườn (Outline), hãy tải lên đây. AI sẽ bắt chước bố cục của file này.")
    
    uploaded_template = st.file_uploader("Tải lên Khung sườn (.docx)", type=["docx"])
    
    if uploaded_template is not None:
        st.success(f"Đã tải lên: {uploaded_template.name}")
        st.session_state.selected_template_name = uploaded_template.name
    else:
        st.session_state.selected_template_name = ""
        
    st.markdown("---")
    st.markdown("### 🗄️ Lịch sử Dự thảo")
    
    if st.button("🗑️ Xóa toàn bộ lịch sử", use_container_width=True):
        database.clear_drafts()
        st.success("Đã xóa toàn bộ lịch sử!")
        st.rerun()
            
    drafts = database.get_drafts()
    if drafts:
        for d in drafts[:5]:
            if st.button(f"🕒 {d['created_at']} - {d['doc_type']}", key=f"draft_{d['id']}", use_container_width=True):
                st.session_state.generated_draft = d['ai_content'].get('noi_dung_chinh', '')
                st.session_state.generated_agency_name = d['ai_content'].get('ten_co_quan', '')
                st.session_state.generated_content_dict = d['ai_content'] # Lưu lại toàn bộ meta
                st.success("Đã tải lại dự thảo cũ!")
    else:
        st.caption("Chưa có lịch sử dự thảo.")

# -- MAIN DASHBOARD --
col1, col2 = st.columns([1, 1], gap="large")

# CỘT TRÁI: NHẬP LIỆU & NGỮ CẢNH
with col1:
    st.markdown("<h3 class='sub-header'>1. Yêu cầu Trợ lý Ảo</h3>", unsafe_allow_html=True)
    
    # CHẾ ĐỘ LÀM VIỆC
    work_mode = st.radio(
        "Chế độ làm việc:",
        ["Soạn thảo thông thường", "Nghiệp vụ Thẩm tra (HĐND)"],
        horizontal=True
    )
    
    if work_mode == "Soạn thảo thông thường":
        doc_type = st.selectbox(
            "Chọn loại văn bản:",
            ["Tự động nhận diện (Để AI tự quyết định)", "Công văn", "Báo cáo", "Quyết định", "Nghị quyết", "Giấy mời", "Tờ trình", "Thông báo", "Khác"]
        )
        prompt_placeholder = "Ví dụ: Tham mưu Công văn trả lời Sở Tài chính về việc đề xuất cấp kinh phí sửa chữa trụ sở. Từ chối do ngân sách đã phân bổ hết..."
        ref_uploader_label = "Tải lên Văn bản đến / Đề xuất của cơ quan khác (Dữ liệu gốc):"
        notebook_lm_label = "Thông tin nội bộ / Chỉ đạo của Lãnh đạo Văn phòng:"
    else:
        doc_type = "Báo cáo thẩm tra"
        prompt_placeholder = "Ví dụ: Đề nghị thẩm tra Tờ trình số 123 của UBND tỉnh về việc ban hành chính sách hỗ trợ gạo dịp Tết. Trọng tâm: Đánh giá nguồn kinh phí."
        ref_uploader_label = "Tải lên Tờ trình & Dự thảo của UBND (Dữ liệu Cần Thẩm tra):"
        notebook_lm_label = "Dữ liệu Căn cứ Pháp lý (Luật, Nghị quyết HĐND):"
    
    prompt = st.text_area(
        "Nhập yêu cầu (Prompt) chi tiết:",
        height=150,
        placeholder=prompt_placeholder
    )
    
    st.markdown(f"#### {notebook_lm_label}")
    notebook_lm_data = st.text_area(
        "Dán văn bản vào đây:",
        height=150,
        placeholder="Dán nội dung vào đây..."
    )
    legal_files = st.file_uploader("Hoặc tải lên File (Luật, Nghị quyết, Quyết định...):", type=["pdf", "docx"], accept_multiple_files=True)

    st.markdown(f"#### {ref_uploader_label}")
    reference_files = st.file_uploader("Chọn file", type=["pdf", "docx"], accept_multiple_files=True)
    
    if st.button("🚀 TẠO DỰ THẢO VĂN BẢN", use_container_width=True, type="primary"):
        if require_auth("Tạo dự thảo văn bản"):
            if not prompt.strip():
                st.warning("Vui lòng nhập yêu cầu trước khi tạo!")
            else:
                with st.spinner("Đang bóc tách dữ liệu từ file đính kèm..."):
                    # Đọc ngữ cảnh từ các file đính kèm
                    context_text = ""
                    if reference_files:
                        for ref_file in reference_files:
                            if ref_file.name.endswith(".pdf"):
                                context_text += extract_text_from_pdf(ref_file) + "\n"
                            elif ref_file.name.endswith(".docx"):
                                context_text += extract_text_from_docx(ref_file) + "\n"
                    
                    # Đọc nội dung từ các file Căn cứ pháp lý
                    if legal_files:
                        for l_file in legal_files:
                            if l_file.name.endswith(".pdf"):
                                notebook_lm_data += f"\n\n--- Căn cứ pháp lý từ {l_file.name} ---\n" + extract_text_from_pdf(l_file)
                            elif l_file.name.endswith(".docx"):
                                notebook_lm_data += f"\n\n--- Căn cứ pháp lý từ {l_file.name} ---\n" + extract_text_from_docx(l_file)
                    
                    # Lấy đề cương từ template tải lên
                    template_outline_text = ""
                    if uploaded_template:
                        uploaded_template.seek(0)
                        template_outline_text = extract_text_from_docx(uploaded_template)
                
                with st.spinner("AI đang tham mưu và kiểm tra chéo pháp lý..."):
                    # Gọi API Gemini
                    draft_result = generate_document_content(prompt, doc_type=doc_type, context=context_text, notebook_lm_data=notebook_lm_data, template_outline=template_outline_text)
                    
                    if isinstance(draft_result, dict) and "error" not in draft_result:
                        st.session_state.generated_draft = draft_result.get("noi_dung_chinh", "")
                        st.session_state.generated_agency_name = draft_result.get("ten_co_quan", "")
                        st.session_state.generated_content_dict = draft_result
                        
                        # Lưu vào Database
                        database.save_draft(doc_type, prompt, draft_result)
                        
                    elif isinstance(draft_result, dict) and "error" in draft_result:
                        st.session_state.generated_draft = draft_result["error"]
                    else:
                        st.session_state.generated_draft = str(draft_result)
                        
                    st.session_state.legal_check_result = "" # Reset legal check result on new draft
                
# CỘT PHẢI: KẾT QUẢ & DOWNLOAD
with col2:
    st.markdown("<h3 class='sub-header'>2. Kết quả Dự thảo</h3>", unsafe_allow_html=True)
    
    if st.session_state.generated_draft:
        # Cho phép người dùng chỉnh sửa kết quả
        edited_draft = st.text_area(
            "Nội dung do AI đề xuất (có thể chỉnh sửa):",
            value=st.session_state.generated_draft,
            height=300
        )
        st.session_state.generated_draft = edited_draft
        
        # Thêm nút Kiểm tra tính pháp lý
        if st.button("⚖️ Tóm tắt & Kiểm tra tính pháp lý", use_container_width=True):
            if require_auth("Kiểm tra tính pháp lý"):
                if not notebook_lm_data.strip():
                    st.warning("Vui lòng nhập Dữ liệu từ NotebookLM ở cột bên trái để có căn cứ đối chiếu!")
                else:
                    with st.spinner("Đang đối chiếu pháp lý..."):
                        check_result = check_legal_compliance(st.session_state.generated_draft, notebook_lm_data)
                        st.session_state.legal_check_result = check_result
        
        if st.session_state.legal_check_result:
            st.markdown("#### Báo cáo Đối chiếu Pháp lý")
            st.info(st.session_state.legal_check_result)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("#### Xuất File Văn Bản")
        
        st.info("Hệ thống sẽ tự động tạo file Word chuẩn 100% theo Nghị định 30/2020/NĐ-CP (Căn lề chuẩn, bảng Quốc hiệu, Nơi nhận, Chữ ký).")
        
        if st.button("📄 Tạo File Word Chuẩn NĐ 30", use_container_width=True, type="primary"):
            with st.spinner("Đang xây dựng file Word từ con số 0..."):
                # Lấy metadata
                content_dict = st.session_state.get("generated_content_dict", {})
                # Cập nhật nội dung chính từ ô text area (nếu người dùng có sửa)
                content_dict["noi_dung_chinh"] = st.session_state.generated_draft
                
                output_stream = create_nd30_document(content_dict)
                
                if output_stream:
                    st.session_state.final_docx_bytes = output_stream.getvalue()
                    st.success("Đã kết xuất thành công!")
                else:
                    st.error("Có lỗi xảy ra khi tạo file Word.")
        
        # Nút Download
        if st.session_state.final_docx_bytes:
            st.download_button(
                label="⬇️ TẢI XUỐNG VĂN BẢN HOÀN CHỈNH (.DOCX)",
                data=st.session_state.final_docx_bytes,
                file_name="VanBan_DuThao.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True
            )
    else:
        st.info("Nội dung dự thảo sẽ xuất hiện ở đây sau khi bạn nhấn nút 'Tạo Dự Thảo Văn Bản'.")
