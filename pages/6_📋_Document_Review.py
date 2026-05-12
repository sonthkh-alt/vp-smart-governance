"""
6_📋_Document_Review.py — Kiểm soát Chất lượng Văn bản
Quy trình 3 bước: Soát lỗi → Tối ưu nội dung → Logic quản lý.
"""

import streamlit as st
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.ui_helper import set_premium_css, draw_module_header, draw_sidebar
from utils.gemini_client import generate_text
from utils.doc_helper import extract_text_from_pdf, extract_text_from_docx
from utils.auth_helper import require_auth

st.set_page_config(page_title="Kiểm soát Văn bản", page_icon="📋", layout="wide")

set_premium_css()
draw_sidebar()

draw_module_header(
    "Document Quality Control",
    "📋",
    "Chuyên gia Thư ký Tổng hợp: Soát lỗi, tối ưu văn phong và kiểm tra logic quản lý nhà nước."
)

# ─── Prompt hệ thống ─────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
Bạn là Chuyên gia Thư ký Tổng hợp và Kiểm soát chất lượng văn bản trong cơ quan Nhà nước.

TIÊU CHUẨN VĂN PHONG:
- Khách quan, chuẩn xác, một nghĩa.
- Đúng thuật ngữ: "kính gửi", "thừa lệnh", "căn cứ", "xét đề nghị", v.v.
- Ngôn ngữ sắc bén, súc tích nhưng đầy đủ ý.

QUY TRÌNH 3 BƯỚC (thực hiện tuần tự, self-reflect trước khi xuất):

BƯỚC 1 — SOÁT LỖI:
Phát hiện & sửa lỗi chính tả, ngữ pháp, thể thức văn bản theo Nghị định 30/2020/NĐ-CP.

BƯỚC 2 — TỐI ƯU NỘI DUNG:
Đề xuất sửa câu từ để đảm bảo tính trang trọng, chính xác, không đa nghĩa.

BƯỚC 3 — LOGIC QUẢN LÝ:
Đảm bảo luận điểm có tính kế thừa, đúng thẩm quyền, phù hợp thực tiễn quản lý nhà nước.

RÀNG BUỘC ĐẦU RA (BẮT BUỘC):
- KHÔNG lặp lại toàn bộ văn bản gốc.
- Xuất kết quả theo CẤU TRÚC sau:

## I. TỔNG QUAN ĐÁNH GIÁ
Nhận xét chung về chất lượng văn bản (1-2 câu). Cho điểm chất lượng: X/10.

## II. BẢNG SOÁT LỖI & TỐI ƯU
Sử dụng Markdown Table:
| STT | Vị trí | Bản gốc | Bản sửa đổi | Loại lỗi | Lý do |
Trong đó Loại lỗi: [Chính tả] / [Ngữ pháp] / [Thể thức] / [Văn phong] / [Logic]

## III. KIỂM TRA LOGIC QUẢN LÝ
- Tính kế thừa giữa các luận điểm.
- Tính đúng thẩm quyền của cơ quan ban hành.
- Tính phù hợp với thực tiễn quản lý.
- Cảnh báo nếu có mâu thuẫn nội tại hoặc thiếu căn cứ pháp lý.

## IV. BẢN TỔNG HỢP ĐÃ HOÀN THIỆN
Chỉ xuất lại TOÀN BỘ VĂN BẢN ĐÃ SỬA nếu người dùng yêu cầu ở phần tùy chọn.
Nếu không yêu cầu, chỉ liệt kê tóm tắt các thay đổi.

Tự kiểm tra lại toàn bộ trước khi xuất kết quả cuối cùng (Self-reflect)."""

# ─── Session State ────────────────────────────────────────────────────────────

if "doc_review_text" not in st.session_state:
    st.session_state.doc_review_text = ""
if "doc_review_result" not in st.session_state:
    st.session_state.doc_review_result = ""

# ─── Layout ───────────────────────────────────────────────────────────────────

col_left, col_right = st.columns([1, 1.3], gap="large")

with col_left:
    st.markdown("### 📥 Nhập Văn bản Cần Kiểm tra")

    input_method = st.radio(
        "Phương thức nhập:",
        ["📄 Tải file lên (PDF / DOCX)", "✏️ Dán nội dung trực tiếp"],
        horizontal=True,
    )

    if input_method.startswith("📄"):
        uploaded = st.file_uploader(
            "Chọn file văn bản",
            type=["pdf", "docx"],
            help="Hỗ trợ file PDF và Word (.docx)",
        )
        if uploaded:
            st.success(f"✅ Đã tải: **{uploaded.name}** ({uploaded.size // 1024} KB)")
            with st.spinner("Đang trích xuất văn bản..."):
                if uploaded.name.lower().endswith(".pdf"):
                    st.session_state.doc_review_text = extract_text_from_pdf(uploaded)
                else:
                    st.session_state.doc_review_text = extract_text_from_docx(uploaded)
    else:
        manual_text = st.text_area(
            "Dán nội dung văn bản vào đây:",
            height=300,
            placeholder="Dán toàn bộ nội dung văn bản cần kiểm tra...",
            value=st.session_state.doc_review_text,
        )
        st.session_state.doc_review_text = manual_text

    # Preview
    if st.session_state.doc_review_text:
        preview = st.session_state.doc_review_text
        with st.expander(f"👁️ Xem trước nội dung ({len(preview)} ký tự)", expanded=False):
            st.text(preview[:3000] + ("\n..." if len(preview) > 3000 else ""))

    st.markdown("---")
    st.markdown("### ⚙️ Tùy chọn Kiểm tra")

    review_focus = st.multiselect(
        "Trọng tâm kiểm tra:",
        [
            "Chính tả & Ngữ pháp",
            "Thể thức văn bản (NĐ 30)",
            "Văn phong hành chính",
            "Logic quản lý & Thẩm quyền",
            "Căn cứ pháp lý",
        ],
        default=["Chính tả & Ngữ pháp", "Văn phong hành chính", "Logic quản lý & Thẩm quyền"],
    )

    output_full_text = st.checkbox(
        "📝 Xuất bản tổng hợp đã hoàn thiện (toàn văn đã sửa)",
        value=False,
        help="Nếu bật, AI sẽ xuất lại toàn bộ văn bản đã sửa ở cuối báo cáo.",
    )

    extra_instructions = st.text_area(
        "Ghi chú bổ sung cho AI (tùy chọn):",
        height=80,
        placeholder="VD: Đây là Công văn gửi Sở Tài chính, cần đặc biệt chú ý căn cứ ngân sách...",
    )

    run_btn = st.button(
        "🚀 BẮT ĐẦU KIỂM TRA CHẤT LƯỢNG",
        type="primary",
        use_container_width=True,
    )

    if run_btn:
        if require_auth("Kiểm tra chất lượng văn bản"):
            text = st.session_state.doc_review_text.strip()
            if not text:
                st.error("⚠️ Vui lòng nhập hoặc tải lên văn bản cần kiểm tra!")
            elif len(text) < 50:
                st.warning("⚠️ Nội dung quá ngắn. Vui lòng nhập đầy đủ văn bản.")
            else:
                with st.spinner("🧠 AI đang thực hiện quy trình 3 bước: Soát lỗi → Tối ưu → Logic..."):
                    focus_str = ", ".join(review_focus) if review_focus else "Toàn diện"

                    user_prompt = f"""VĂN BẢN CẦN KIỂM TRA:
{text[:12000]}

TRỌNG TÂM: {focus_str}
{"XUẤT TOÀN VĂN ĐÃ SỬA Ở PHẦN IV." if output_full_text else "KHÔNG cần xuất toàn văn ở phần IV, chỉ tóm tắt thay đổi."}
{f"GHI CHÚ BỔ SUNG: {extra_instructions}" if extra_instructions.strip() else ""}"""

                    result = generate_text(
                        f"{_SYSTEM_PROMPT}\n\n{user_prompt}",
                        use_pro=True,
                    )
                    st.session_state.doc_review_result = result
                    st.success("✅ Kiểm tra hoàn tất!")

with col_right:
    st.markdown("### 📋 Báo cáo Kiểm soát Chất lượng")

    if st.session_state.doc_review_result:
        st.markdown(st.session_state.doc_review_result)

        st.markdown("---")
        st.markdown("#### 📤 Xuất Kết quả")

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                label="⬇️ Tải Báo cáo (.txt)",
                data=st.session_state.doc_review_result.encode("utf-8"),
                file_name="BaoCao_KiemSoatChatLuong.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with dl2:
            st.download_button(
                label="⬇️ Tải Báo cáo (.md)",
                data=st.session_state.doc_review_result.encode("utf-8"),
                file_name="BaoCao_KiemSoatChatLuong.md",
                mime="text/markdown",
                use_container_width=True,
            )

        st.markdown("---")

        # Cho phép kiểm tra lại với chỉ dẫn bổ sung
        st.markdown("#### 🔄 Yêu cầu AI phân tích thêm")
        followup = st.text_area(
            "Câu hỏi hoặc yêu cầu bổ sung:",
            height=80,
            placeholder="VD: Kiểm tra lại phần căn cứ pháp lý, bổ sung Luật Ngân sách 2015...",
            key="followup_input",
        )
        if st.button("🔍 PHÂN TÍCH BỔ SUNG", use_container_width=True):
            if require_auth("Phân tích AI bổ sung"):
                if followup.strip():
                    with st.spinner("🧠 AI đang phân tích bổ sung..."):
                        followup_prompt = f"""Dựa trên báo cáo kiểm tra trước đó:
{st.session_state.doc_review_result[:4000]}

VĂN BẢN GỐC (tóm tắt):
{st.session_state.doc_review_text[:4000]}

YÊU CẦU BỔ SUNG:
{followup}

Trả lời ngắn gọn, tập trung vào yêu cầu. Dùng Markdown Table nếu cần so sánh."""
                        extra_result = generate_text(followup_prompt, use_pro=True)
                        st.session_state.doc_review_result += f"\n\n---\n## 📌 PHÂN TÍCH BỔ SUNG\n{extra_result}"
                        st.rerun()
                else:
                    st.warning("Vui lòng nhập yêu cầu bổ sung.")
    else:
        st.info("💡 Kết quả kiểm tra sẽ hiển thị ở đây sau khi bạn tải lên văn bản và nhấn 'Bắt đầu Kiểm tra'.")

        # Hướng dẫn sử dụng
        st.markdown("---")
        st.markdown("### 📖 Hướng dẫn sử dụng")
        st.markdown("""
**Quy trình 3 bước tự động:**

1. **Soát lỗi** — Phát hiện lỗi chính tả, ngữ pháp, thể thức theo NĐ 30/2020/NĐ-CP.
2. **Tối ưu nội dung** — Sửa câu từ để đảm bảo tính trang trọng, chính xác, một nghĩa.
3. **Logic quản lý** — Kiểm tra tính kế thừa, thẩm quyền và phù hợp thực tiễn.

**Kết quả đầu ra:**
- Bảng so sánh chi tiết: `Bản gốc` → `Bản sửa` → `Lý do`
- Đánh giá logic quản lý và cảnh báo rủi ro
- Bản tổng hợp hoàn thiện (tùy chọn)

**Mẹo:** Bật tùy chọn "Xuất bản tổng hợp" nếu bạn muốn nhận lại toàn bộ văn bản đã sửa, sẵn sàng để sử dụng.
        """)
