import streamlit as st
import os
from google import genai
from google.genai import types
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.doc_helper import extract_text_from_pdf, extract_text_from_docx
from utils.storage_helper import supabase
import database
import io

# Khởi tạo client đồng bộ với gemini_client.py
def _get_client():
    key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Thiếu GEMINI_API_KEY trong cấu hình.")
    return genai.Client(api_key=key)

def vectorize_document(doc_id, storage_path, file_name):
    """
    Quy trình Vectorize sử dụng SDK google-genai mới nhất (v1.0+).
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
            return False, "Tài liệu không có nội dung văn bản hoặc quá ngắn."

        # 3. Chia nhỏ văn bản
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text)
        
        st.info(f"Đã chia tài liệu thành {len(chunks)} đoạn tri thức. Đang tạo Vector...")

        # 4. Tạo Vector bằng mô hình embedding-004 (Chuẩn mới nhất của SDK v1.0)
        # Nếu không có embedding-004, hệ thống sẽ tự động dùng mô hình mặc định
        for i, chunk_text in enumerate(chunks):
            try:
                # Gọi API Embed của SDK mới
                resp = client.models.embed_content(
                    model="text-embedding-004",
                    contents=chunk_text,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                )
                
                # Lấy vector từ kết quả
                vector = resp.embeddings[0].values
                
                # Lưu vào Supabase
                supabase.table("document_chunks").insert({
                    "document_id": doc_id,
                    "content": chunk_text,
                    "embedding": vector,
                    "metadata": {"source": file_name, "chunk_index": i}
                }).execute()
                
            except Exception as inner_e:
                # Fallback sang model đời cũ hơn nếu cần
                resp = client.models.embed_content(
                    model="embedding-001",
                    contents=chunk_text,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                )
                vector = resp.embeddings[0].values
                supabase.table("document_chunks").insert({
                    "document_id": doc_id, "content": chunk_text, "embedding": vector, "metadata": {"source": file_name}
                }).execute()

        # 5. Cập nhật trạng thái
        database.mark_as_vectorized(doc_id)
        
        return True, f"Thành công! Đã Vectorize {len(chunks)} đoạn tri thức."

    except Exception as e:
        return False, f"Lỗi Vectorize: {str(e)}"
