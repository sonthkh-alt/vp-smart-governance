import streamlit as st
import os
import time
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
    Quy trình Vectorize với bước THANH TRA mô hình công khai.
    """
    try:
        client = _get_client()
        
        # BƯỚC THANH TRA: Hiện danh sách mô hình lên màn hình
        models = []
        try:
            for m in client.models.list():
                models.append(m.name)
            st.success(f"🔍 DANH SÁCH MÔ HÌNH CỦA BẠN: {', '.join(models)}")
        except Exception as e_list:
            st.error(f"Không thể liệt kê mô hình: {e_list}")

        # Thử một danh sách tên mô hình đa dạng nhất có thể
        to_try = ["models/gemini-embedding-2", "text-embedding-004", "embedding-001"]
        # Lọc trùng
        to_try = list(dict.fromkeys(to_try))

        # 1. Tải file
        res = supabase.storage.from_("reference-docs").download(storage_path)
        file_io = io.BytesIO(res)
        text = extract_text_from_pdf(file_io) if file_name.lower().endswith(".pdf") else extract_text_from_docx(file_io)
        
        if not text: return False, "Lỗi bóc tách văn bản."

        # 2. Chia nhỏ
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text)
        
        # 3. Thử tìm mô hình sống
        working_model = None
        for m_name in to_try:
            try:
                resp = client.models.embed_content(
                    model=m_name, contents=chunks[0],
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                )
                if resp.embeddings:
                    working_model = m_name
                    break
            except:
                continue
        
        if not working_model:
            return False, "Vẫn không tìm thấy mô hình nào hỗ trợ Embedding trong danh sách trên."

        # 4. Lưu dữ liệu
        for i, chunk_text in enumerate(chunks):
            # Nghỉ 1 giây để tránh lỗi Rate Limit (RESOURCE_EXHAUSTED) của gói miễn phí
            time.sleep(1)
            
            resp = client.models.embed_content(
                model=working_model, contents=chunk_text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
            )
            vector = resp.embeddings[0].values
            if len(vector) > 768: vector = vector[:768] # Cắt về 768 để khớp DB
            
            vector_str = "[" + ",".join(map(str, vector)) + "]"
            database._execute(
                "INSERT INTO document_chunks (document_id, content, embedding, metadata) VALUES (%s, %s, %s::vector, %s)",
                (doc_id, chunk_text, vector_str, '{}')
            )

        database.mark_as_vectorized(doc_id)
        return True, f"Thành công với mô hình: {working_model}"

    except Exception as e:
        return False, f"Lỗi: {str(e)}"
