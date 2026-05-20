import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st
import sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.doc_helper import extract_text_from_pdf, extract_text_from_docx, create_tham_tra_document
from utils.ui_helper import set_premium_css, draw_module_header
from utils.auth_helper import require_auth
from utils.gemini_client import generate_text
import database

# Khởi tạo DB
database.init_db()
set_premium_css()

draw_module_header(
    "Thẩm tra Dự thảo Nghị quyết",
    "🔍",
    "Hệ thống AI chuyên gia thẩm tra tự động phân tích Tờ trình, Dự thảo NQ và các văn bản liên quan để tạo Báo cáo thẩm tra chuyên nghiệp."
)

# --- Cấu hình AI chung cho trang ---
with st.sidebar:
    st.markdown("### 🤖 Cấu hình AI")
    ai_provider = st.radio("Chọn mô hình AI ưu tiên:", ["Anthropic Claude (Mặc định)", "OpenAI ChatGPT", "Google Gemini", "Groq (Llama 3.3)"], index=0, key="global_ai_provider")
    if "Anthropic" in ai_provider:
        provider_key = "claude"
    elif "OpenAI" in ai_provider:
        provider_key = "openai"
    elif "Gemini" in ai_provider:
        provider_key = "gemini"
    else:
        provider_key = "groq"

tt_col1, tt_col2 = st.columns([1, 1.2], gap="large")
with tt_col1:
    st.markdown("#### 📥 Tài liệu đầu vào")
    ban_select = st.selectbox("🏛️ Ban thẩm tra:", [
        "Kinh tế - Ngân sách",
        "Pháp chế",
        "Văn hóa - Xã hội",
        "Dân tộc"
    ], key="tt_ban")
    
    nq_name = st.text_input("📋 Tên Dự thảo Nghị quyết:", placeholder="Ví dụ: Nghị quyết về phân bổ ngân sách địa phương năm 2026", key="tt_nq_name")
    
    tt_files = st.file_uploader("📄 Tờ trình UBND tỉnh, Dự thảo Nghị quyết:", type=["pdf", "docx"], accept_multiple_files=True, key="tt_files")
    tt_lien_quan = st.file_uploader("📄 Văn bản liên quan (nếu có):", type=["pdf", "docx"], accept_multiple_files=True, key="tt_lienquan")
    
    tt_note = st.text_area("📝 Ghi chú / Yêu cầu đặc biệt (nếu có):", height=100, placeholder="Ví dụ: Tập trung phản biện nguồn kinh phí bố trí...", key="tt_note")
    
    tt_c1, tt_c2 = st.columns([2, 1])
    with tt_c1:
        if st.button("🚀 TẠO BÁO CÁO THẨM TRA", type="primary", use_container_width=True, key="tt_run"):
            if require_auth("Thẩm tra dự thảo NQ"):
                if not tt_files:
                    st.error("⚠️ Vui lòng tải lên Tờ trình UBND tỉnh và Dự thảo Nghị quyết!")
                else:
                    with st.spinner(f"AI ({ai_provider}) đang thẩm tra chuyên sâu..."):
                        to_trinh_du_thao_text = ""
                        lien_quan_text = ""
                        
                        for f in tt_files:
                            to_trinh_du_thao_text += (extract_text_from_pdf(f) if f.name.endswith(".pdf") else extract_text_from_docx(f)) + "\n---\n"
                        if tt_lien_quan:
                            for f in tt_lien_quan:
                                lien_quan_text += (extract_text_from_pdf(f) if f.name.endswith(".pdf") else extract_text_from_docx(f)) + "\n---\n"
                        
                        prompt = f"""Bạn là Chuyên gia thẩm tra cao cấp của Ban {ban_select} - Hội đồng nhân dân tỉnh Thanh Hóa.
Bạn đang thực hiện thẩm tra dự thảo Nghị quyết trước khi trình Kỳ họp HĐND tỉnh.

NHIỆM VỤ THẨM TRA:
Viết BÁO CÁO THẨM TRA hoàn chỉnh, chuyên nghiệp theo đúng cấu trúc của báo cáo thẩm tra chuẩn HĐND, gồm 4 phần chính:

I. CƠ SỞ PHÁP LÝ VÀ THẨM QUYỀN BAN HÀNH
- Căn cứ pháp lý: Liệt kê và đánh giá các căn cứ luật, pháp lệnh, nghị định mà Tờ trình viện dẫn.
- Thẩm quyền ban hành: Xác nhận HĐND tỉnh có thẩm quyền ban hành nghị quyết này không.
- Trình tự thủ tục: Đánh giá quy trình xây dựng dự thảo có đúng quy định không.

II. SỰ PHÙ HỢP VỀ NỘI DUNG
- Phân tích sự phù hợp của nội dung dự thảo với chủ trương, đường lối của Đảng, chính sách pháp luật của Nhà nước.
- Đánh giá tính khả thi, phù hợp với điều kiện thực tiễn địa phương.
- Phát hiện các điểm bất cập, thiếu sót, mâu thuẫn trong nội dung dự thảo.
- So sánh đối chiếu giữa Tờ trình và Dự thảo NQ: nội dung có nhất quán không.

III. KHẢ NĂNG CÂN ĐỐI NGUỒN LỰC
- Phản biện nguồn kinh phí: Đánh giá tính hợp lý của dự toán kinh phí.
- Nguồn nhân lực: Đánh giá năng lực tổ chức thực hiện.
- Khả năng cân đối ngân sách địa phương.
- Rủi ro tài chính và các phương án dự phòng.

IV. KẾT LUẬN VÀ KIẾN NGHỊ
- Ý kiến thống nhất hoặc không thống nhất với nội dung dự thảo.
- Các nội dung đề nghị chỉnh sửa, bổ sung cụ thể.
- Kiến nghị HĐND tỉnh xem xét, quyết định.

YÊU CẦU VĂN PHONG:
- Ngôn ngữ trang trọng, chuẩn mực công vụ, văn phong thẩm tra chuyên nghiệp.
- Phân tích sâu sắc, có lập luận chặt chẽ, dẫn chứng cụ thể từ tài liệu.
- KHÔNG dùng markdown heading (#, ##), chỉ dùng ký hiệu I., II., 1., 2., a), b) theo chuẩn văn bản hành chính.

{f"GHI CHÚ CỦA NGƯỜI DÙNG: {tt_note}" if tt_note else ""}

--- TỜ TRÌNH UBND TỈNH VÀ DỰ THẢO NGHỊ QUYẾT ---
{to_trinh_du_thao_text}

--- VĂN BẢN LIÊN QUAN ---
{lien_quan_text if lien_quan_text else "(Không có)"}
"""
                        res = generate_text(prompt, use_pro=True, provider=provider_key, use_search=False)
                        st.session_state.tt_result = res
                        st.session_state.tt_ban_name = ban_select
                        st.session_state.tt_nq_display = nq_name
                        database.save_draft("Báo cáo Thẩm tra", f"Thẩm tra: {nq_name}", {"noi_dung_chinh": res, "ban": ban_select})
    with tt_c2:
        if st.button("🧹 LÀM MỚI", use_container_width=True, key="tt_clear"):
            for k in ["tt_result", "tt_ban_name", "tt_nq_display", "tt_nq_name", "tt_note"]:
                st.session_state.pop(k, None)
            st.rerun()

with tt_col2:
    if "tt_result" in st.session_state:
        st.markdown("#### 📄 Kết quả Báo cáo Thẩm tra")
        ban_display = st.session_state.get("tt_ban_name", "")
        nq_display = st.session_state.get("tt_nq_display", "")
        st.info(f"🏛️ **Ban {ban_display}** | 📋 {nq_display if nq_display else 'Dự thảo Nghị quyết'}")
        
        edited_tt = st.text_area("Nội dung báo cáo (có thể chỉnh sửa):", value=st.session_state.tt_result, height=500, key="tt_edit")
        st.session_state.tt_result = edited_tt
        
        if st.button("📄 Xuất file Word chuẩn NĐ 30", use_container_width=True, type="primary", key="tt_word"):
            out = create_tham_tra_document(
                report_text=edited_tt,
                ban_name=ban_display,
                nghi_quyet_name=nq_display
            )
            if out:
                st.download_button(
                    "⬇️ Tải Báo cáo Thẩm tra (.docx)",
                    out.getvalue(),
                    f"BaoCao_ThamTra_{ban_display.replace(' ', '_')}.docx",
                    key="tt_dl"
                )
            else:
                st.error("Lỗi khi tạo file Word.")
    else:
        st.info("Kết quả thẩm tra sẽ hiển thị ở đây sau khi AI hoàn tất phân tích.")
