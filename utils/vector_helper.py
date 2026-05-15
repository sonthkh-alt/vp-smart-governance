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
    return genai.Client(api_key=key, http_options={'api_version': 'v1'})

def vectorize_document(doc_id, storage_path, file_name):
    """
    Quy trình Vectorize hợp nhất: Dùng chung kết nối SQL của database.py để đảm bảo ID chính xác.
    """
    try:
        client = _get_client()
        
        # 1. Tải file từ Supabase Storage
        res = supabase.storage.from_("reference-docs").download(storage_path)
        if not res:
            return False, "Không thể tải file từ Storage."
        
        # 2. Bóc tách văn bản
        text = ""
        file_io = io.BytesIO(res)
        if file_name.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file_io)
        elif file_name.lower().endswith(".docx"):
            text = extract_text_from_docx(file_io)
        
        if not text or len(text.strip()) < 10:
            return False, "Tài liệu không có nội dung văn bản."

        # 3. Chia nhỏ văn bản
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text)
        st.info(f"Đã chia {len(chunks)} đoạn. Đang tạo Vector và lưu trực tiếp qua SQL...")

        # 4. Tạo Vector và lưu bằng kết nối SQL duy nhất
        working_model = "text-embedding-004"
        
        for i, chunk_text in enumerate(chunks):
            try:
                resp = client.models.embed_content(
                    model=working_model,
                    contents=chunk_text,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=768
                    )
                )
                vector = resp.embeddings[0].values
                
                # Cắt bớt nếu cần
                if len(vector) > 768: vector = vector[:768]

                # LƯU TRỰC TIẾP QUA DATABASE.PY (Hợp nhất kết nối)
                # Chuyển vector list thành chuỗi định dạng PostgreSQL: [1.2, 3.4, ...]
                vector_str = "[" + ",".join(map(str, vector)) + "]"
                
                database._execute(
                    "INSERT INTO document_chunks (document_id, content, embedding, metadata) VALUES (%s, %s, %s::vector, %s)",
                    (doc_id, chunk_text, vector_str, '{"source": "' + file_name + '"}')
                )
                
            except Exception as e:
                # Fallback model nếu cần
                st.warning(f"Đang thử model dự phòng cho đoạn {i}...")
                resp = client.models.embed_content(
                    model="embedding-001",
                    contents=chunk_text,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                )
                vector = resp.embeddings[0].values
                if len(vector) > 768: vector = vector[:768]
                vector_str = "[" + ",".join(map(str, vector)) + "]"
                
                database._execute(
                    "INSERT INTO document_chunks (document_id, content, embedding, metadata) VALUES (%s, %s, %s::vector, %s)",
                    (doc_id, chunk_text, vector_str, '{}')
                )

        # 5. Cập nhật trạng thái
        database.mark_as_vectorized(doc_id)
        return True, f"Thành công mỹ mãn! Đã xử lý {len(chunks)} đoạn tri thức."

    except Exception as e:
        return False, f"Lỗi xử lý: {str(e)}"
