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


def generate_document_content(prompt: str, doc_type: str = "Tự động", context: str = "", notebook_lm_data: str = "", provider: str = "claude") -> dict:
    """
    Sinh nội dung văn bản dưới dạng JSON chuẩn NĐ 30, hỗ trợ đa mô hình.
    """
    rule = DOC_STRUCTURE_RULES.get(doc_type, "")
    
    parts = [
        "Bạn là Trợ lý tham mưu văn bản hành chính cao cấp cho Đoàn ĐBQH & HĐND tỉnh Thanh Hóa.",
        "QUAN ĐIỂM PHÁP LÝ: Bạn nên ưu tiên các quy định pháp luật Việt Nam mới nhất đang có hiệu lực. Văn phong trang trọng, chuẩn mực công vụ.",
        f"LOẠI VĂN BẢN: {doc_type}",
        f"CẤU TRÚC ĐẶC THÙ: {rule}" if rule else "",
        f"YÊU CẦU CỦA NGƯỜI DÙNG: {prompt}",
    ]

    if notebook_lm_data:
        parts.append(f"DỮ LIỆU TRI THỨC (NotebookLM):\n{notebook_lm_data}")
    if context:
        parts.append(f"NGỮ CẢNH/TÀI LIỆU THAM KHẢO:\n{context}")
        
    parts.append(_JSON_SCHEMA)
    
    full_prompt = "\n\n".join(p for p in parts if p)
    return generate_json(full_prompt, use_pro=True, provider=provider)


def check_legal_compliance(draft: str, reference_data: str = "", provider: str = "claude") -> str:
    """
    Đối chiếu pháp lý giữa dự thảo và căn cứ tham chiếu, hỗ trợ đa mô hình.
    """
    prompt = f"""
    Bạn là chuyên gia pháp chế cao cấp. Hãy đối chiếu dự thảo văn bản với các căn cứ pháp lý sau:

    KHO TRI THỨC/QUY ĐỊNH: {reference_data}

    DỰ THẢO VĂN BẢN:
    {draft}

    NHIỆM VỤ:
    1. Tóm tắt các điểm pháp lý cốt lõi cần áp dụng từ kho tri thức.
    2. Kiểm tra tính pháp lý của dự thảo: chỉ ra các điểm thiếu sót, sai sót hoặc rủi ro.
    3. Đề xuất nội dung sửa đổi cụ thể để đảm bảo tuân thủ pháp luật.
    4. Kết luận: Dự thảo có đạt yêu cầu pháp lý hay không?

    Trình bày súc tích, chuyên nghiệp bằng tiếng Việt.
    """
    return generate_text(prompt, provider=provider)
