"""ai_helper.py — Tham mưu và soạn thảo văn bản hành chính (Gemini AI)."""

from .gemini_client import generate_text, generate_json

DOC_STRUCTURE_RULES = {
    "Quyết định": "Sinh cấu trúc: Căn cứ pháp lý → Điều 1, Điều 2, Điều 3.",
    "Nghị quyết": "Sinh cấu trúc: Căn cứ pháp lý → QUYẾT NGHỊ: Điều 1, Điều 2.",
    "Báo cáo": "Chia: I. TÌNH HÌNH/ĐÁNH GIÁ, II. KẾT QUẢ, III. PHƯƠNG HƯỚNG.",
    "Báo cáo thẩm tra": (
        "[CHUYÊN GIA THẨM TRA HĐND] Viết 4 phần: "
        "1) Cơ sở pháp lý & thẩm quyền; "
        "2) Sự phù hợp nội dung; "
        "3) Khả năng cân đối nguồn lực (phản biện nguồn kinh phí); "
        "4) Kết luận & kiến nghị."
    ),
    "Công văn": "Văn xuôi hành chính, chia mục 1., 2., 3.",
    "Tờ trình": "Văn xuôi hành chính, chia mục 1., 2., 3.",
    "Bài phát biểu": "Cấu trúc: Kính thưa (đúng thứ bậc) → Phần mở đầu (lý do) → Phần nội dung (đánh giá, nhiệm vụ trọng tâm) → Phần kết thúc (lời chúc, bế mạc).",
}

_JSON_SCHEMA = """\
Xuất JSON với các trường:
{"co_quan_chu_quan":"...","co_quan_ban_hanh":"...","so_ky_hieu":"Số: [...]/...",
"dia_danh_ngay_thang":"Thanh Hóa, ngày...","loai_van_ban":"IN HOA (Công văn để trống)",
"trich_yeu":"V/v...","noi_dung_chinh":"Toàn bộ thân bài chi tiết",
"noi_nhan":["- Thường trực HĐND tỉnh;","- Lưu: VT."],
"quyen_han_ky":"Chức vụ người ký","nguoi_ky":"Họ tên"}"""


def generate_document_content(prompt, doc_type="Tự động nhận diện (Để AI tự quyết định)",
                              context="", notebook_lm_data="", template_outline=""):
    """Sinh nội dung văn bản dưới dạng JSON chuẩn NĐ 30."""
    rule = DOC_STRUCTURE_RULES.get(doc_type, "")

    parts = [
        "Bạn là Trợ lý tham mưu văn bản hành chính cao cấp cho Đoàn ĐBQH & HĐND tỉnh Thanh Hóa.",
        "QUAN ĐIỂM PHÁP LÝ: Bạn BẮT BUỘC phải sử dụng công cụ tìm kiếm (Google Search) để tra cứu, đối chiếu và cập nhật các Luật, Nghị định, Thông tư và quy định mới nhất đang có hiệu lực liên quan đến nội dung tham mưu. Tuyệt đối không sử dụng các quy định cũ đã hết hiệu lực.",
        "LƯU Ý: Ưu tiên áp dụng các văn bản quy phạm pháp luật chuyên ngành mới nhất (bao gồm cả các Luật mới ban hành như Luật Tổ chức chính quyền địa phương năm 2025 nếu liên quan đến tổ chức bộ máy). Phải tuân thủ triệt để nguyên tắc phân cấp, phân quyền và đẩy mạnh chuyển đổi số trong quản lý nhà nước.",
        "Bỏ qua rác định dạng. Văn phong trang trọng, súc tích chuẩn Nhà nước.",
        "KHÔNG bịa số liệu/ngày tháng/tên. Dùng [...] cho thông tin thiếu.",
        f"LOẠI VĂN BẢN: {doc_type}",
        f"CẤU TRÚC: {rule}" if rule else "",
        f"YÊU CẦU:\n{prompt}",
    ]

    if notebook_lm_data:
        parts.append(f"KHO TRI THỨC:\n{notebook_lm_data}")
    if context:
        parts.append(f"NGỮ CẢNH:\n{context}")
    if template_outline:
        parts.append(f"ĐỀ CƯƠNG MẪU:\n{template_outline}")
    parts.append(_JSON_SCHEMA)

    return generate_json("\n\n".join(p for p in parts if p))


def check_legal_compliance(draft, reference_data):
    """Đối chiếu pháp lý giữa dự thảo và căn cứ tham chiếu."""
    prompt = f"""Chuyên gia pháp chế. Đối chiếu dự thảo với căn cứ pháp lý:

KHO TRI THỨC: {reference_data}

DỰ THẢO: {draft}

1. Tóm tắt điểm áp dụng từ kho tri thức.
2. Kiểm tra tính pháp lý: chỉ ra thiếu sót.
3. Kết luận: đạt yêu cầu pháp lý hay không.

Trình bày súc tích bằng tiếng Việt."""
    return generate_text(prompt)
