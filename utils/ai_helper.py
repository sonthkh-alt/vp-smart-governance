import os
import google.generativeai as genai
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

# Cấu hình API key
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Cấu hình model
generation_config = {
  "temperature": 0.7,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

generation_config_json = {
  "temperature": 0.7,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
]

def generate_document_content(prompt, doc_type="Tự động nhận diện (Để AI tự quyết định)", context="", notebook_lm_data="", template_outline=""):
    """
    Sử dụng Gemini để sinh nội dung văn bản dưới dạng JSON.
    """
    if not api_key:
        return {"error": "Lỗi: Chưa cấu hình GEMINI_API_KEY trong file .env."}

    try:
        import json
        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            generation_config=generation_config_json,
            safety_settings=safety_settings
        )

        # Định hướng cấu trúc văn bản dựa trên loại văn bản
        doc_structure_rule = ""
        if doc_type == "Quyết định":
            doc_structure_rule = "Bắt buộc sinh cấu trúc có Căn cứ pháp lý, và nội dung gồm Điều 1:..., Điều 2:..., Điều 3:..."
        elif doc_type == "Nghị quyết":
            doc_structure_rule = "Bắt buộc sinh cấu trúc có Căn cứ pháp lý, và nội dung là QUYẾT NGHỊ: Điều 1:..., Điều 2:..."
        elif doc_type == "Báo cáo":
            doc_structure_rule = "Bắt buộc chia cấu trúc rõ ràng: I. TÌNH HÌNH/ĐÁNH GIÁ, II. KẾT QUẢ ĐẠT ĐƯỢC, III. PHƯƠNG HƯỚNG NHIỆM VỤ."
        elif doc_type == "Báo cáo thẩm tra":
            doc_structure_rule = """
            [CHUYÊN GIA THẨM TRA HĐND] - Bắt buộc viết Báo cáo thẩm tra sắc bén gồm 4 phần:
            1. Cơ sở pháp lý và sự cần thiết (Kiểm tra thẩm quyền ban hành theo Luật).
            2. Sự phù hợp của nội dung (Đánh giá đối tượng, mức hỗ trợ trong Tờ trình).
            3. Khả năng cân đối nguồn lực (PHẢN BIỆN: Phân tích kỹ nguồn kinh phí. Nếu Tờ trình của UBND chưa nêu rõ nguồn tiền ở đâu ra, phải 'bắt lỗi' và kiến nghị làm rõ).
            4. Kết luận và Kiến nghị (Đồng ý trình HĐND thông qua hay yêu cầu UBND sửa đổi).
            """
        elif doc_type == "Công văn" or doc_type == "Tờ trình":
            doc_structure_rule = "Viết theo lối văn xuôi hành chính, chia thành các đoạn hoặc các mục nhỏ 1., 2., 3. rõ ràng."

        full_prompt = f"""
        Bạn là một Trợ lý ảo chuyên nghiệp hỗ trợ tham mưu, soạn thảo văn bản hành chính nhà nước cho Đoàn ĐBQH & HĐND tỉnh Thanh Hóa.
        
        [KỸ NĂNG LỌC NHIỄU DỮ LIỆU (DENOISE)]
        - Khi đọc các tài liệu tham khảo (đặc biệt là PDF scan), hãy TỰ ĐỘNG BỎ QUA các "rác" định dạng như: số trang ở góc, tiêu đề lặp lại ở đầu mỗi trang, dấu gạch ngang nối chữ bị rớt dòng. Chỉ chắt lọc nội dung lõi.
        
        [VĂN PHONG NGOẠI GIAO HÀNH CHÍNH]
        - Văn phong cần trang trọng, súc tích, rõ ràng, đi thẳng vào vấn đề.
        - Gửi cấp trên: Dùng từ "Kính trình", "Báo cáo".
        - Gửi cơ quan ngang cấp hoặc phối hợp (Sở, Ban, Ngành): Dùng từ "Đề nghị", "Trân trọng".
        - Gửi cấp dưới: Dùng từ "Yêu cầu", "Chỉ đạo".
        - Viết hoa chữ cái đầu của các cơ quan, đơn vị theo quy chuẩn (Ví dụ: Ủy ban nhân dân tỉnh, Sở Tài chính).

        LOẠI VĂN BẢN: {doc_type}
        QUY TẮC CẤU TRÚC: {doc_structure_rule}
        
        NGUYÊN TẮC TỐI MẬT (CHỐNG BỊA ĐẶT DỮ LIỆU):
        Tuyệt đối KHÔNG tự sáng tác, bịa đặt số liệu, ngày tháng, tên cá nhân, hoặc số ký hiệu văn bản pháp luật nếu không có trong dữ liệu tham chiếu. Đối với các thông tin bị thiếu, bắt buộc dùng ngoặc vuông [...] (Ví dụ: ngày [...] tháng [...] năm 2026, hoặc Số: [...]/QĐ-UBND) để chuyên viên tự điền sau.

        YÊU CẦU:
        {prompt}
        """

        if notebook_lm_data:
            full_prompt += f"\n\nKHO TRI THỨC THAM CHIẾU TỪ NOTEBOOKLM:\n{notebook_lm_data}"

        if context:
            full_prompt += f"\n\nNGỮ CẢNH THAM KHẢO (Nội dung tài liệu, pháp lý): \n{context}"
            
        if template_outline:
            full_prompt += f"\n\nĐỀ CƯƠNG THAM KHẢO (Lấy từ Template mẫu của cơ quan - Hãy bắt chước cấu trúc này):\n{template_outline}"

        full_prompt += """
        Hãy xuất kết quả DƯỚI ĐỊNH DẠNG JSON với ĐẦY ĐỦ các trường sau để hệ thống tự động sinh file Word theo Nghị định 30:
        {
            "co_quan_chu_quan": "Tên cơ quan chủ quản (Mặc định: 'ĐOÀN ĐBQH VÀ HĐND TỈNH THANH HÓA' hoặc 'HĐND TỈNH THANH HÓA').",
            "co_quan_ban_hanh": "Tên cơ quan ban hành (Mặc định: 'VĂN PHÒNG ĐOÀN ĐBQH VÀ HĐND TỈNH'. Nếu là Báo cáo thẩm tra, dùng tên Ban tương ứng). Viết in hoa.",
            "so_ky_hieu": "Số ký hiệu văn bản (Ví dụ: Số: [...]/BC-HĐND, Số: [...]/CV-VP).",
            "dia_danh_ngay_thang": "Địa danh, ngày tháng năm (Ví dụ: Thanh Hóa, ngày [...] tháng [...] năm 2026).",
            "loai_van_ban": "Tên loại văn bản in hoa (Ví dụ: QUYẾT ĐỊNH, BÁO CÁO THẨM TRA, CÔNG VĂN thì để trống).",
            "trich_yeu": "Trích yếu (Ví dụ: V/v tham mưu trả lời công văn...).",
            "noi_dung_chinh": "Toàn bộ nội dung thân bài của văn bản. Viết dài, chi tiết, bám sát cấu trúc yêu cầu và văn phong hành chính nhà nước.",
            "noi_nhan": ["Mảng các nơi nhận", "- Thường trực HĐND tỉnh (để b/c);", "- UBND tỉnh;", "- Lưu: VT, Ban KT-NS."],
            "quyen_han_ky": "Chức vụ của người ký (Ví dụ: CHÁNH VĂN PHÒNG, TRƯỞNG BAN, CHỦ TỊCH).",
            "nguoi_ky": "Họ và tên người ký (Ví dụ: Nguyễn Văn A)."
        }
        """

        response = model.generate_content(full_prompt)
        try:
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            return {"error": "Lỗi: Kết quả trả về không đúng định dạng JSON.", "raw_text": response.text}
            
    except Exception as e:
        return {"error": f"Đã xảy ra lỗi khi gọi Gemini API: {str(e)}"}

def check_legal_compliance(draft, reference_data):
    """
    Kiểm tra tính pháp lý và tóm tắt sự đối chiếu giữa dự thảo và dữ liệu NotebookLM.
    """
    if not api_key:
        return "Lỗi: Chưa cấu hình GEMINI_API_KEY trong file .env."

    try:
        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        full_prompt = f"""
        Bạn là một chuyên gia pháp chế của cơ quan nhà nước. Hãy đọc bản dự thảo văn bản sau và đối chiếu với Kho tri thức tham chiếu (căn cứ pháp lý).
        
        KHO TRI THỨC THAM CHIẾU:
        {reference_data}
        
        BẢN DỰ THẢO:
        {draft}
        
        YÊU CẦU:
        1. Tóm tắt nhanh xem dự thảo đã áp dụng những điểm nào từ Kho tri thức tham chiếu.
        2. Kiểm tra tính pháp lý: Chỉ ra những điểm có thể chưa phù hợp, thiếu sót hoặc cần điều chỉnh để đúng với căn cứ pháp lý đã cung cấp.
        3. Đưa ra kết luận: Dự thảo có đạt yêu cầu pháp lý cơ bản dựa trên thông tin tham chiếu hay không.
        
        Hãy trình bày rõ ràng, súc tích bằng tiếng Việt.
        """

        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Đã xảy ra lỗi khi kiểm tra pháp lý: {str(e)}"

def analyze_template_structure(paragraphs_list):
    """
    Sử dụng Gemini để phân tích cấu trúc mảng các đoạn văn bản trong file Word mẫu,
    trả về tọa độ bắt đầu và kết thúc của phần thân bài.
    """
    if not api_key:
        return {"error": "Lỗi: Chưa cấu hình GEMINI_API_KEY"}

    try:
        import json
        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            generation_config=generation_config_json,
            safety_settings=safety_settings
        )

        numbered_text = ""
        for i, text in enumerate(paragraphs_list):
            # Cắt bớt văn bản quá dài trên mỗi dòng để tiết kiệm token
            short_text = text[:200].replace('\n', ' ')
            numbered_text += f"[{i}] {short_text}\n"

        full_prompt = f"""
        Bạn là một chuyên gia phân tích cấu trúc văn bản hành chính Việt Nam (Nghị quyết, Quyết định, Báo cáo, Công văn, Giấy mời...).
        Dưới đây là danh sách các đoạn văn bản (đã được đánh số thứ tự chỉ mục ở đầu) được trích xuất từ một file Word mẫu.
        
        VĂN BẢN MẪU:
        {numbered_text}
        
        NHIỆM VỤ:
        Hãy xác định chính xác vị trí CỦA PHẦN THÂN BÀI (Nội dung chính) cần được thay thế.
        - Đoạn bắt đầu: Là đoạn văn đầu tiên của phần nội dung chính, nằm ngay SAU các phần khung cố định như: Quốc hiệu, Tiêu ngữ, Tên cơ quan, Số/Ký hiệu, Địa danh, Tiêu đề văn bản (Ví dụ: BÁO CÁO, QUYẾT ĐỊNH), Kính gửi, hoặc các Căn cứ pháp lý.
        - Đoạn kết thúc: Là đoạn văn cuối cùng của phần nội dung chính, nằm ngay TRƯỚC các phần khung cố định như: Nơi nhận, Thẩm quyền ký (Chủ tịch/Giám đốc...), Chữ ký.
        
        Hãy xuất kết quả DƯỚI ĐỊNH DẠNG JSON với đúng 2 trường:
        {{
            "start_idx": Số nguyên, là chỉ mục (index) của đoạn văn đầu tiên thuộc thân bài (Ví dụ: 5),
            "end_idx": Số nguyên, là chỉ mục (index) của đoạn văn cuối cùng thuộc thân bài (Ví dụ: 12)
        }}
        
        Nếu phần thân bài hoàn toàn trống rỗng (ví dụ: ngay sau Kính gửi đã tới luôn Nơi nhận), hãy để start_idx và end_idx là chỉ mục của khoảng trống ở giữa.
        """

        response = model.generate_content(full_prompt)
        try:
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            return {"error": "JSON Decode Error"}
            
    except Exception as e:
        return {"error": f"Lỗi gọi API: {str(e)}"}
