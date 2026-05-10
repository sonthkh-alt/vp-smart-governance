"""
ai_helper.py — Tham mưu và soạn thảo văn bản hành chính
Sử dụng gemini_client để gọi AI, tránh phụ thuộc trực tiếp vào SDK.
"""

import os
from dotenv import load_dotenv
from utils.gemini_client import generate_text, generate_json

load_dotenv()

# ─── Cấu hình cấu trúc theo loại văn bản ─────────────────────────────────────
DOC_STRUCTURE_RULES = {
    "Quyết định": "Bắt buộc sinh cấu trúc có Căn cứ pháp lý, và nội dung gồm Điều 1:..., Điều 2:..., Điều 3:...",
    "Nghị quyết": "Bắt buộc sinh cấu trúc có Căn cứ pháp lý, và nội dung là QUYẾT NGHỊ: Điều 1:..., Điều 2:...",
    "Báo cáo": "Bắt buộc chia cấu trúc rõ ràng: I. TÌNH HÌNH/ĐÁNH GIÁ, II. KẾT QUẢ ĐẠT ĐƯỢC, III. PHƯƠNG HƯỚNG NHIỆM VỤ.",
    "Báo cáo thẩm tra": """
        [CHUYÊN GIA THẨM TRA HĐND] - Bắt buộc viết Báo cáo thẩm tra sắc bén gồm 4 phần:
        1. Cơ sở pháp lý và sự cần thiết (Kiểm tra thẩm quyền ban hành theo Luật).
        2. Sự phù hợp của nội dung (Đánh giá đối tượng, mức hỗ trợ trong Tờ trình).
        3. Khả năng cân đối nguồn lực (PHẢN BIỆN: Phân tích kỹ nguồn kinh phí. Nếu Tờ trình của UBND chưa nêu rõ nguồn tiền ở đâu ra, phải 'bắt lỗi' và kiến nghị làm rõ).
        4. Kết luận và Kiến nghị (Đồng ý trình HĐND thông qua hay yêu cầu UBND sửa đổi).
    """,
    "Công văn": "Viết theo lối văn xuôi hành chính, chia thành các đoạn hoặc các mục nhỏ 1., 2., 3. rõ ràng.",
    "Tờ trình": "Viết theo lối văn xuôi hành chính, chia thành các đoạn hoặc các mục nhỏ 1., 2., 3. rõ ràng.",
}

JSON_OUTPUT_SCHEMA = """
Hãy xuất kết quả DƯỚI ĐỊNH DẠNG JSON với ĐẦY ĐỦ các trường sau để hệ thống tự động sinh file Word theo Nghị định 30:
{
    "co_quan_chu_quan": "Tên cơ quan chủ quản (Mặc định: 'ĐOÀN ĐBQH VÀ HĐND TỈNH THANH HÓA').",
    "co_quan_ban_hanh": "Tên cơ quan ban hành. Viết in hoa.",
    "so_ky_hieu": "Số ký hiệu văn bản (Ví dụ: Số: [...]/BC-HĐND).",
    "dia_danh_ngay_thang": "Địa danh, ngày tháng năm (Ví dụ: Thanh Hóa, ngày [...] tháng [...] năm 2026).",
    "loai_van_ban": "Tên loại văn bản in hoa (Ví dụ: QUYẾT ĐỊNH, BÁO CÁO THẨM TRA). Công văn thì để trống.",
    "trich_yeu": "Trích yếu (Ví dụ: V/v tham mưu trả lời công văn...).",
    "noi_dung_chinh": "Toàn bộ nội dung thân bài. Viết dài, chi tiết, bám sát cấu trúc yêu cầu và văn phong hành chính nhà nước.",
    "noi_nhan": ["- Thường trực HĐND tỉnh (để b/c);", "- UBND tỉnh;", "- Lưu: VT."],
    "quyen_han_ky": "Chức vụ của người ký (Ví dụ: CHÁNH VĂN PHÒNG).",
    "nguoi_ky": "Họ và tên người ký (Ví dụ: Nguyễn Văn A)."
}
"""


def generate_document_content(
    prompt: str,
    doc_type: str = "Tự động nhận diện (Để AI tự quyết định)",
    context: str = "",
    notebook_lm_data: str = "",
    template_outline: str = ""
) -> dict:
    """Sinh nội dung văn bản dưới dạng JSON chuẩn NĐ 30."""
    doc_structure_rule = DOC_STRUCTURE_RULES.get(doc_type, "")

    full_prompt = f"""
Bạn là một Trợ lý ảo chuyên nghiệp hỗ trợ tham mưu, soạn thảo văn bản hành chính nhà nước cho Đoàn ĐBQH & HĐND tỉnh Thanh Hóa.

[KỸ NĂNG LỌC NHIỄU DỮ LIỆU (DENOISE)]
Khi đọc tài liệu tham khảo, hãy TỰ ĐỘNG BỎ QUA các "rác" định dạng như: số trang, tiêu đề lặp lại, dấu gạch ngang nối chữ bị rớt dòng. Chỉ chắt lọc nội dung lõi.

[VĂN PHONG NGOẠI GIAO HÀNH CHÍNH]
- Văn phong trang trọng, súc tích, rõ ràng, đi thẳng vào vấn đề.
- Gửi cấp trên: Dùng "Kính trình", "Báo cáo".
- Gửi ngang cấp: Dùng "Đề nghị", "Trân trọng".
- Gửi cấp dưới: Dùng "Yêu cầu", "Chỉ đạo".

LOẠI VĂN BẢN: {doc_type}
QUY TẮC CẤU TRÚC: {doc_structure_rule}

NGUYÊN TẮC CHỐNG BỊA ĐẶT: Tuyệt đối KHÔNG tự sáng tác số liệu, ngày tháng, tên cá nhân, số ký hiệu văn bản nếu không có trong dữ liệu tham chiếu. Dùng ngoặc vuông [...] cho thông tin bị thiếu.

YÊU CẦU:
{prompt}
"""
    if notebook_lm_data:
        full_prompt += f"\n\nKHO TRI THỨC THAM CHIẾU:\n{notebook_lm_data}"
    if context:
        full_prompt += f"\n\nNGỮ CẢNH THAM KHẢO:\n{context}"
    if template_outline:
        full_prompt += f"\n\nĐỀ CƯƠNG MẪU (Bắt chước cấu trúc):\n{template_outline}"

    full_prompt += f"\n\n{JSON_OUTPUT_SCHEMA}"

    result = generate_json(full_prompt)
    return result


def check_legal_compliance(draft: str, reference_data: str) -> str:
    """Kiểm tra tính pháp lý và tóm tắt sự đối chiếu giữa dự thảo và căn cứ pháp lý."""
    prompt = f"""
Bạn là một chuyên gia pháp chế của cơ quan nhà nước. Hãy đọc bản dự thảo văn bản sau và đối chiếu với Kho tri thức tham chiếu (căn cứ pháp lý).

KHO TRI THỨC THAM CHIẾU:
{reference_data}

BẢN DỰ THẢO:
{draft}

YÊU CẦU:
1. Tóm tắt nhanh xem dự thảo đã áp dụng những điểm nào từ Kho tri thức tham chiếu.
2. Kiểm tra tính pháp lý: Chỉ ra những điểm có thể chưa phù hợp, thiếu sót hoặc cần điều chỉnh.
3. Đưa ra kết luận: Dự thảo có đạt yêu cầu pháp lý cơ bản dựa trên thông tin tham chiếu hay không.

Hãy trình bày rõ ràng, súc tích bằng tiếng Việt.
"""
    return generate_text(prompt)
