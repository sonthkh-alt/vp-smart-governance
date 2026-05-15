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
    # ÉP BUỘC sử dụng API version v1 chính thức thay vì v1beta
    return genai.Client(api_key=key, http_options={'api_version': 'v1'})

def vectorize_document(doc_id, storage_path, file_name):
    """
    Quy trình Vectorize ép buộc sử dụng API v1 để tránh lỗi 404 trên v1beta.
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
        st.info(f"Đã chia tài liệu thành {len(chunks)} đoạn. Đang tạo Vector qua API v1...")

        # 4. Tạo Vector (Sử dụng model chuẩn nhất của v1)
        for i, chunk_text in enumerate(chunks):
            try:
                resp = client.models.embed_content(
                    model="text-embedding-004",
                    contents=chunk_text,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                )
                vector = resp.embeddings[0].values
                
                # Lưu vào Supabase
                supabase.table("document_chunks").insert({
                    "document_id": doc_id,
                    "content": chunk_text,
                    "embedding": vector,
                    "metadata": {"source": file_name, "chunk_index": i}
                }).execute()
            except Exception as e1:
                # Dự phòng sang model cũ hơn trên v1
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
        return True, f"Thành công! Đã Vectorize {len(chunks)} đoạn qua API v1."

    except Exception as e:
        return False, f"Lỗi Vectorize (v1): {str(e)}"
