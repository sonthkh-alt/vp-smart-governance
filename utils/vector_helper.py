import streamlit as st
import os
from google import genai
from google.genai import types
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.doc_helper import extract_text_from_pdf, extract_text_from_docx
from utils.storage_helper import supabase
import database
import io

def _get_client():
    key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Thiếu GEMINI_API_KEY trong cấu hình.")
    return genai.Client(api_key=key)

def vectorize_document(doc_id, storage_path, file_name):
    """
    Quy trình Vectorize với hệ thống Chẩn đoán và Thử sai đa tầng.
    """
    try:
        client = _get_client()
        
        # 1. CHẨN ĐOÁN & CHỌN MÔ HÌNH
        model_name = None
        try:
            # Liệt kê các mô hình có khả năng Embedding
            available_models = []
            for m in client.models.list():
                # Trong SDK mới, dùng supported_generation_methods
                methods = getattr(m, 'supported_generation_methods', [])
                if "embedContent" in methods or "embed_content" in str(methods).lower():
                    available_models.append(m.name)
            
            if available_models:
                st.info(f"🔍 Tìm thấy mô hình: {', '.join(available_models)}")
                model_name = available_models[0]
            else:
                # Nếu không liệt kê được, dùng danh sách ưu tiên
                st.warning("⚠️ Không liệt kê được mô hình, chuyển sang chế độ Thử sai...")
                model_name = "text-embedding-004"
        except Exception as diag_e:
            st.caption(f"(Chẩn đoán nhẹ: {diag_e})")
            model_name = "text-embedding-004"

        # 2. Tải file từ Supabase Storage
        res = supabase.storage.from_("reference-docs").download(storage_path)
        if not res:
            return False, "Không thể tải file từ Storage."
        
        # 3. Bóc tách văn bản
        text = ""
        file_io = io.BytesIO(res)
        if file_name.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file_io)
        elif file_name.lower().endswith(".docx"):
            text = extract_text_from_docx(file_io)
        
        if not text or len(text.strip()) < 10:
            return False, "Tài liệu không có nội dung văn bản hoặc quá ngắn."

        # 4. Chia nhỏ văn bản
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text)
        st.info(f"Đã chia tài liệu thành {len(chunks)} đoạn. Đang tạo Vector...")

        # 5. Tạo Vector (Có cơ chế dự phòng)
        priority_models = [model_name, "text-embedding-004", "embedding-001", "models/embedding-001"]
        # Loại bỏ các tên trùng lặp và None
        priority_models = [m for m in dict.fromkeys(priority_models) if m]

        for i, chunk_text in enumerate(chunks):
            vector = None
            last_err = ""
            
            for m_test in priority_models:
                try:
                    resp = client.models.embed_content(
                        model=m_test,
                        contents=chunk_text,
                        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                    )
                    vector = resp.embeddings[0].values
                    if vector: break # Thành công
                except Exception as e:
                    last_err = str(e)
                    continue # Thử model tiếp theo
            
            if not vector:
                return False, f"Tất cả các mô hình Embedding đều thất bại. Lỗi cuối: {last_err}"
            
            # Lưu vào Supabase
            supabase.table("document_chunks").insert({
                "document_id": doc_id,
                "content": chunk_text,
                "embedding": vector,
                "metadata": {"source": file_name, "chunk_index": i}
            }).execute()

        # 6. Cập nhật trạng thái
        database.mark_as_vectorized(doc_id)
        return True, f"Thành công! Đã Vectorize {len(chunks)} đoạn tri thức."

    except Exception as e:
        return False, f"Lỗi hệ thống: {str(e)}"
