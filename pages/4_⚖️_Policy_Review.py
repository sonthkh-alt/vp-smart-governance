"""
4_⚖️_Policy_Review.py — Thẩm tra Chính sách
AI Impact Assessment: Đánh giá tính hợp pháp và tác động socio-economic.
"""

import streamlit as st
import os
import io
from utils.ui_helper import set_premium_css, draw_module_header
from utils.gemini_client import generate_text
from utils.doc_helper import extract_text_from_pdf, extract_text_from_docx, create_nd30_document
import database

st.set_page_config(page_title="Thẩm tra Chính sách", page_icon="⚖️", layout="wide")

database.init_db()
set_premium_css()

draw_module_header(
    "Policy Review & Impact Assessment",
    "⚖️",
    "Đánh giá tính hợp pháp, tác động kinh tế - xã hội và rủi ro thực thi của dự thảo chính sách."
)


def analyze_policy(policy_text: str, policy_name: str, focus_areas: list) -> str:
    """Gọi AI để thực hiện thẩm tra chuyên sâu."""
    focus_str = "\n".join([f"- {f}" for f in focus_areas])
    prompt = f"""
Bạn là Chuyên gia Thẩm tra Chính sách cấp cao của HĐND tỉnh Thanh Hóa, có chuyên môn về pháp chế, kinh tế công và quản trị nhà nước.

TÊN DỰ THẢO: {policy_name}

NỘI DUNG DỰ THẢO:
{policy_text[:8000]}  

TRỌNG TÂM PHÂN TÍCH:
{focus_str}

YÊU CẦU BÁO CÁO THẨM TRA (Cấu trúc bắt buộc):

## I. CĂN CỨ PHÁP LÝ & THẨM QUYỀN BAN HÀNH
- Dự thảo có phù hợp với thẩm quyền của cơ quan ban hành theo quy định của pháp luật hiện hành?
- Căn cứ pháp lý viện dẫn có chính xác, đầy đủ và còn hiệu lực?

## II. SỰ PHÙ HỢP VỀ NỘI DUNG CHÍNH SÁCH
- Đối tượng áp dụng có được xác định rõ ràng?
- Mức hỗ trợ / quy định có phù hợp với thực tiễn và chính sách vĩ mô?

## III. PHÂN TÍCH TÁC ĐỘNG
### 3.1 Tác động Ngân sách
- Ước tính nhu cầu kinh phí và nguồn bảo đảm.
- Cảnh báo nếu nguồn kinh phí chưa được xác định rõ.

### 3.2 Tác động Kinh tế - Xã hội
- Tác động đến tăng trưởng kinh tế, thu hút đầu tư.
- Tác động đến đời sống người dân, công bằng xã hội.

### 3.3 Tác động Môi trường (nếu có liên quan)

## IV. ĐIỂM NGHẼN & RỦI RO THỰC THI
- Chỉ ra các lỗ hổng, mâu thuẫn nội tại hoặc rủi ro khi triển khai.
- Những điều kiện cần thiết chưa được đảm bảo.

## V. KẾT LUẬN & KIẾN NGHỊ
- Tổng kết: Dự thảo có đủ điều kiện trình HĐND thông qua hay cần UBND chỉnh sửa bổ sung?
- Liệt kê cụ thể các điểm PHẢI sửa trước khi thông qua (nếu có).
- Kiến nghị các điều kiện giám sát thực hiện sau khi ban hành.

Sử dụng ngôn ngữ hành chính chuyên nghiệp, sắc bén, trung thực.
"""
    return generate_text(prompt, use_pro=True)


# ─── Layout ───────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    st.markdown("### 📥 Thông tin Dự thảo")
    policy_name = st.text_input(
        "Tên dự thảo chính sách",
        placeholder="Ví dụ: Nghị quyết hỗ trợ phát triển kinh tế biển tỉnh Thanh Hóa giai đoạn 2026-2030"
    )
    uploaded_file = st.file_uploader(
        "Tải lên file dự thảo (PDF hoặc DOCX)",
        type=["pdf", "docx"],
        help="Hỗ trợ file PDF và Word (.docx)"
    )

    if uploaded_file:
        st.success(f"✅ Đã tải: **{uploaded_file.name}** ({uploaded_file.size // 1024} KB)")

    st.markdown("### 🎯 Trọng tâm Thẩm tra")
    focus = st.multiselect(
        "Chọn các khía cạnh AI cần tập trung:",
        [
            "Tính hợp pháp & Thẩm quyền ban hành",
            "Tác động Ngân sách & Nguồn kinh phí",
            "Tác động Kinh tế - Xã hội",
            "Kinh tế xanh & Phát triển bền vững",
            "An sinh xã hội & Công bằng",
            "Thủ tục hành chính & Điều kiện thực thi",
            "Rủi ro pháp lý & Tranh chấp tiềm ẩn"
        ],
        default=["Tính hợp pháp & Thẩm quyền ban hành", "Tác động Ngân sách & Nguồn kinh phí"]
    )

    run_btn = st.button("🚀 BẮT ĐẦU THẨM TRA AI", type="primary", use_container_width=True)

    if run_btn:
        if not uploaded_file:
            st.error("⚠️ Vui lòng tải lên file dự thảo!")
        elif not policy_name.strip():
            st.error("⚠️ Vui lòng nhập tên dự thảo!")
        elif not focus:
            st.warning("Vui lòng chọn ít nhất 1 trọng tâm phân tích.")
        else:
            with st.spinner("🧠 AI đang nghiên cứu tài liệu và soạn báo cáo thẩm tra..."):
                # Trích xuất văn bản
                if uploaded_file.name.endswith(".pdf"):
                    text = extract_text_from_pdf(uploaded_file)
                else:
                    text = extract_text_from_docx(uploaded_file)

                result = analyze_policy(text, policy_name, focus)
                st.session_state.policy_result = result
                st.session_state.policy_name   = policy_name

                # Lưu vào DB
                database.save_policy_review(policy_name, result)
                st.success("✅ Phân tích hoàn tất!")

with col_right:
    st.markdown("### 📋 Báo cáo Thẩm tra AI")

    if "policy_result" in st.session_state:
        st.markdown(st.session_state.policy_result)

        st.markdown("---")
        st.markdown("#### 📤 Xuất Kết quả")
        btn1, btn2 = st.columns(2)

        with btn1:
            # Xuất báo cáo thẩm tra thành file Word
            if st.button("📄 Xuất Word (NĐ 30)", use_container_width=True):
                with st.spinner("Đang tạo file Word..."):
                    content_dict = {
                        "co_quan_chu_quan": "ĐOÀN ĐBQH VÀ HĐND TỈNH THANH HÓA",
                        "co_quan_ban_hanh": "BAN KINH TẾ - NGÂN SÁCH HĐND TỈNH",
                        "so_ky_hieu": "Số: [...]/BC-HĐND",
                        "dia_danh_ngay_thang": "Thanh Hóa, ngày [...] tháng [...] năm 2026",
                        "loai_van_ban": "BÁO CÁO THẨM TRA",
                        "trich_yeu": f"V/v thẩm tra {st.session_state.policy_name}",
                        "noi_dung_chinh": st.session_state.policy_result,
                        "noi_nhan": [
                            "- Thường trực HĐND tỉnh (để b/c);",
                            "- Các Ban HĐND tỉnh;",
                            "- UBND tỉnh (để phối hợp);",
                            "- Lưu: VT, Ban KT-NS."
                        ],
                        "quyen_han_ky": "TRƯỞNG BAN",
                        "nguoi_ky": "[...]"
                    }
                    output = create_nd30_document(content_dict)
                    if output:
                        st.download_button(
                            label="⬇️ Tải xuống Báo cáo Thẩm tra (.docx)",
                            data=output.getvalue(),
                            file_name=f"BaoCaoThamTra_{st.session_state.policy_name[:30]}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="primary",
                            use_container_width=True
                        )
                    else:
                        st.error("Có lỗi khi tạo file Word.")

        with btn2:
            # Copy to clipboard (hiển thị nội dung để copy thủ công)
            st.download_button(
                label="📋 Tải xuống (.txt)",
                data=st.session_state.policy_result.encode("utf-8"),
                file_name=f"ThamTra_{st.session_state.policy_name[:30]}.txt",
                mime="text/plain",
                use_container_width=True
            )
    else:
        st.info("💡 Kết quả phân tích chuyên sâu sẽ hiển thị ở đây sau khi bạn tải lên dự thảo và nhấn 'Bắt đầu Thẩm tra'.")

# ─── Lịch sử ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🕒 Lịch sử Thẩm tra")

history = database.get_policy_reviews()
if history:
    for h in history[:5]:
        with st.expander(f"📅 {h[1]}  ·  📄 {h[2]}"):
            st.markdown(h[3])
            st.download_button(
                f"⬇️ Tải (.txt)",
                data=h[3].encode("utf-8"),
                file_name=f"ThamTra_{h[2][:20]}.txt",
                key=f"dl_{h[0]}"
            )
else:
    st.caption("Chưa có lịch sử thẩm tra nào.")
