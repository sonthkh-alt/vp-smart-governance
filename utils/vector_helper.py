import streamlit as st
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.doc_helper import extract_text_from_pdf, extract_text_from_docx
from utils.storage_helper import supabase
import database
import io

# Khởi tạo mô hình Embedding của Google
# text-embedding-004 là mô hình mới nhất và tối ưu nhất của Google hiện nay (768 chiều)
embeddings_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

def vectorize_document(doc_id, storage_path, file_name):
    """
    Quy trình Vectorize: Tải file -> Bóc tách -> Chia nhỏ -> Tạo Embedding -> Lưu Supabase.
    """
    try:
        # 1. Tải file từ Supabase Storage
        res = supabase.storage.from_("reference-docs").download(storage_path)
        if not res:
            return False, "Không thể tải file từ Storage."
        
        # 2. Bóc tách văn bản dựa trên loại file
        text = ""
        file_io = io.BytesIO(res)
        if file_name.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file_io)
        elif file_name.lower().endswith(".docx"):
            text = extract_text_from_docx(file_io)
        
        if not text or len(text.strip()) < 10:
            return False, "Tài liệu không có nội dung văn bản hoặc quá ngắn."

        # 3. Chia nhỏ văn bản (Chunking)
        # Mỗi đoạn khoảng 1000 ký tự, gối đầu 200 ký tự để không mất ngữ cảnh
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text)
        
        st.info(f"Đã chia tài liệu thành {len(chunks)} đoạn tri thức. Đang tạo Vector...")

        # 4. Tạo Vector và lưu vào Supabase
        # Chúng ta thực hiện lưu từng đoạn để tránh quá tải API
        for i, chunk_text in enumerate(chunks):
            # Gọi Gemini API để tạo Vector cho đoạn này
            vector = embeddings_model.embed_query(chunk_text)
            
            # Lưu vào bảng document_chunks trực tiếp qua Supabase Client (do có kiểu dữ liệu VECTOR)
            supabase.table("document_chunks").insert({
                "document_id": doc_id,
                "content": chunk_text,
                "embedding": vector,
                "metadata": {"source": file_name, "chunk_index": i}
            }).execute()

        # 5. Cập nhật trạng thái trong Database chính
        database.mark_as_vectorized(doc_id)
        
        return True, f"Thành công! Đã Vectorize {len(chunks)} đoạn tri thức."

    except Exception as e:
        return False, f"Lỗi Vectorize: {str(e)}"
