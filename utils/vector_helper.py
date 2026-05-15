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
    Quy trình Vectorize vạn năng: Quét sạch mọi mô hình khả dụng trong tài khoản.
    """
    try:
        client = _get_client()
        
        # 1. Tìm kiếm mô hình Embedding thực tế
        embedding_models = []
        try:
            for m in client.models.list():
                methods = getattr(m, 'supported_generation_methods', [])
                if "embedContent" in methods or "embed_content" in str(methods).lower() or "embedding" in m.name.lower():
                    embedding_models.append(m.name)
        except:
            pass
        
        # Danh sách dự phòng cứng
        fallback_list = ["text-embedding-004", "embedding-001", "models/text-embedding-004", "models/embedding-001"]
        all_to_try = list(dict.fromkeys(embedding_models + fallback_list))
        
        st.info(f"Đang kiểm tra {len(all_to_try)} mô hình tiềm năng...")

        # 2. Tải file
        res = supabase.storage.from_("reference-docs").download(storage_path)
        file_io = io.BytesIO(res)
        text = extract_text_from_pdf(file_io) if file_name.lower().endswith(".pdf") else extract_text_from_docx(file_io)
        
        if not text or len(text.strip()) < 10:
            return False, "Tài liệu không có nội dung."

        # 3. Chia nhỏ
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text)
        
        # 4. Thử Vectorize với từng mô hình cho đến khi thành công
        working_model = None
        for test_model in all_to_try:
            try:
                # Thử với đoạn đầu tiên
                resp = client.models.embed_content(
                    model=test_model,
                    contents=chunks[0],
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                )
                if resp.embeddings:
                    working_model = test_model
                    st.success(f"✅ Đã tìm thấy mô hình hoạt động: {working_model}")
                    break
            except:
                continue
        
        if not working_model:
            return False, f"Không tìm thấy mô hình Embedding nào hoạt động trong tài khoản của bạn. Đã thử: {', '.join(all_to_try)}"

        # 5. Tiến hành Vectorize toàn bộ bằng mô hình đã tìm thấy
        for i, chunk_text in enumerate(chunks):
            resp = client.models.embed_content(
                model=working_model,
                contents=chunk_text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
            )
            vector = resp.embeddings[0].values
            supabase.table("document_chunks").insert({
                "document_id": doc_id, "content": chunk_text, "embedding": vector, "metadata": {"source": file_name}
            }).execute()

        database.mark_as_vectorized(doc_id)
        return True, f"Thành công! Đã xử lý bằng mô hình {working_model}."

    except Exception as e:
        return False, f"Lỗi: {str(e)}"
