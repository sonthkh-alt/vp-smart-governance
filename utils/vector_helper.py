import streamlit as st
import os
import time
from google import genai
from google.genai import types
from langchain_text_splitters import RecursiveCharacterTextSplitter

import database
import io

def _get_client():
    key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Thiếu GEMINI_API_KEY trong cấu hình.")
    return genai.Client(api_key=key, http_options={'api_version': 'v1beta'})

def vectorize_document(doc_id, storage_path, file_name):
    """
    Quy trình Vectorize với bước THANH TRA mô hình công khai.
    """
    from utils.doc_helper import extract_text_from_pdf, extract_text_from_docx
    from utils.storage_helper import supabase
    try:
        client = _get_client()
        
        # BƯỚC THANH TRA: Hiện danh sách mô hình và tìm mô hình hỗ trợ Embedding
        all_models = []
        detected_embed_models = []
        try:
            for m in client.models.list():
                all_models.append(m.name)
                # Kiểm tra xem mô hình có hỗ trợ 'embedContent' không
                if hasattr(m, "supported_generation_methods"):
                    if "embedContent" in m.supported_generation_methods:
                        detected_embed_models.append(m.name)
                elif "embed" in m.name.lower(): # Fallback nếu không có thuộc tính trên
                    detected_embed_models.append(m.name)
            
            st.success(f"🔍 TỔNG SỐ MÔ HÌNH: {len(all_models)}. ĐÃ TÌM THẤY {len(detected_embed_models)} MÔ HÌNH EMBEDDING.")
            if detected_embed_models:
                st.info(f"💡 Mô hình tiềm năng: {', '.join(detected_embed_models)}")
        except Exception as e_list:
            st.error(f"Không thể liệt kê mô hình: {e_list}")

        # Danh sách thử nghiệm
        to_try = detected_embed_models + [
            "models/text-embedding-004", 
            "models/embedding-001",
            "text-embedding-004", 
            "embedding-001"
        ]
        
        # Lọc trùng và giữ nguyên thứ tự ưu tiên (mô hình detected được ưu tiên trước)
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

        # 4. Lưu dữ liệu theo batch (tối đa 50 chunks mỗi đợt) để tối ưu hóa API và kết nối database
        batch_size = 50
        chunks_data = []
        
        for idx in range(0, len(chunks), batch_size):
            batch_chunks = chunks[idx : idx + batch_size]
            
            # Gọi API nhúng hàng loạt
            resp = client.models.embed_content(
                model=working_model, 
                contents=batch_chunks,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
            )
            
            # Duyệt và trích xuất vector cho từng chunk trong batch
            for j, chunk_text in enumerate(batch_chunks):
                vector = resp.embeddings[j].values
                if len(vector) > 768: 
                    vector = vector[:768]  # Cắt về 768 để khớp DB
                vector_str = "[" + ",".join(map(str, vector)) + "]"
                chunks_data.append((doc_id, chunk_text, vector_str, '{}'))
            
            # Nghỉ ngắn giữa các batch nếu còn đợt tiếp theo để tránh chạm giới hạn API
            if idx + batch_size < len(chunks):
                time.sleep(1)
        
        # Ghi toàn bộ dữ liệu vào Database chỉ trong một lần gọi mạng duy nhất
        database.save_document_chunks(chunks_data)

        database.mark_as_vectorized(doc_id)
        return True, f"Thành công với mô hình: {working_model}"

    except Exception as e:
        return False, f"Lỗi: {str(e)}"
