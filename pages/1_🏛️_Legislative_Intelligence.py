import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st
import os
from utils.rag_engine import process_documents, query_rag
from utils.ui_helper import set_premium_css, draw_module_header, draw_sidebar
from utils.auth_helper import require_auth

st.set_page_config(page_title="Trợ lý Kỳ họp", page_icon="🏛️", layout="wide")

# Áp dụng giao diện Premium & Sidebar
set_premium_css()
draw_sidebar()

# Hiển thị Header
draw_module_header(
    "Legislative Intelligence",
    "🏛️",
    "Trợ lý Thẩm tra & Kỳ họp: Tự động đọc hiểu, đối chiếu số liệu thông qua công nghệ RAG."
)
st.markdown("---")

col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    st.markdown("### 📥 1. Xây dựng Cơ sở Tri thức (Knowledge Base)")
    st.info("Tải lên các tài liệu phục vụ kỳ họp: Báo cáo kinh tế - xã hội, Báo cáo thẩm tra, và các Nghị quyết/Luật liên quan. Hệ thống sẽ tự động đọc, nhúng (embed) và lưu trữ.")
    
    uploaded_files = st.file_uploader("Chọn tài liệu (PDF, DOCX)", type=["pdf", "docx"], accept_multiple_files=True)
    
    if st.button("🔄 Vector hóa & Xây dựng CSDL Tri thức", use_container_width=True):
        if require_auth("Vector hóa tài liệu"):
            if not uploaded_files:
            st.warning("⚠️ Vui lòng tải lên ít nhất 1 tài liệu!")
        else:
            with st.spinner("Đang trích xuất văn bản, phân mảnh (chunking) và Vector hóa... Quá trình này có thể mất vài phút."):
                status, msg = process_documents(uploaded_files)
                if status:
                    st.success("✅ Đã xây dựng xong cơ sở dữ liệu tri thức! Các tài liệu đã sẵn sàng để đối chiếu.")
                else:
                    st.error(f"❌ Có lỗi: {msg}")

with col2:
    st.markdown("### 🤖 2. Trợ lý Phân tích & Gợi ý Chất vấn")
    
    st.markdown("Chọn một tác vụ phân tích tự động hoặc đặt câu hỏi trực tiếp cho AI.")
    
    analysis_type = st.selectbox("Nghiệp vụ Thẩm tra chuyên sâu:", [
        "1. So sánh số liệu (Tìm điểm mâu thuẫn giữa Báo cáo UBND và Báo cáo Thẩm tra)",
        "2. Đề xuất danh sách Câu hỏi Chất vấn sắc bén (Dành cho Đại biểu)",
        "3. Kiểm tra tính tuân thủ Nghị quyết HĐND (Đối soát chỉ tiêu KT-XH)",
        "4. Phân tích điểm nghẽn Ngân sách & Đầu tư công",
        "5. Tóm tắt rủi ro chính sách & Tác động xã hội",
        "6. Đặt câu hỏi tùy chọn (Tự nhập)"
    ])
    
    custom_query = ""
    if "6" in analysis_type:
        custom_query = st.text_area("Nhập yêu cầu phân tích cụ thể:", placeholder="Ví dụ: Chỉ ra các rủi ro trong việc phân bổ vốn đầu tư công dựa trên các báo cáo vừa tải lên...")
    
    if st.button("🚀 THỰC HIỆN PHÂN TÍCH", type="primary", use_container_width=True):
        if require_auth("Phân tích AI chuyên sâu"):
            query = custom_query if custom_query.strip() else analysis_type
        
        with st.spinner("🧠 Trợ lý AI đang truy xuất dữ liệu đối chiếu và lập luận logic..."):
            response = query_rag(query)
            
            if response and not response.startswith("Lỗi") and not "chưa được xây dựng" in response:
                st.markdown("#### 📊 Báo cáo Phản biện:")
                st.info(response)
            else:
                st.error(response)
