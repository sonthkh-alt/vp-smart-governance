import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=key)

prompt = """Bạn là Chuyên gia Kiểm soát Chất lượng của Văn phòng HĐND tỉnh Thanh Hóa.
Rà soát toàn bộ văn bản dưới đây, phát hiện ra TẤT CẢ các lỗi sai từ nhỏ nhất đến lớn nhất (chính tả, gõ phím bừa như 'fádf', logic, văn phong) và đề xuất sửa đổi cụ thể dưới dạng bảng.

Văn bản cần soát lỗi:
miền núi có 74 xã, dân số trên 1 triệu người với trên 710 nghìn người
dân tộc thiểu số. Đây là sự thay đổi lớn về tổ chức bộ máy, đặt ra yêu
cầu cao đối với hoạt động của Hội đồng nhân dân (HĐND) các cấp trong
tỉnh. fádf
Ngay sau khi sắp xếp đơn vị hành chính và vận hành mô hình chính
quyền 02 cấp...
"""

print("Calling gemini-2.5-pro...")
try:
    resp = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
    )
    print("PRO SUCCESS:")
    print(resp.text)
except Exception as e:
    print(f"PRO FAILED: {e}")
