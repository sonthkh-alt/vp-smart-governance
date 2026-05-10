"""
rag_engine.py — RAG cho Legislative Intelligence
Sử dụng LangChain + ChromaDB + Gemini Embeddings.
Isolation per session dùng session_id trong collection name.
"""

import os
import uuid
import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv
from utils.doc_helper import extract_text_from_pdf, extract_text_from_docx
from utils.gemini_client import generate_text

load_dotenv()

PERSIST_DIRECTORY = "chroma_db"


def _get_session_collection() -> str:
    """
    Trả về tên collection riêng cho mỗi session người dùng.
    Tránh trộn lẫn dữ liệu giữa các phiên làm việc khác nhau.
    """
    if "rag_session_id" not in st.session_state:
        st.session_state.rag_session_id = str(uuid.uuid4())[:8]
    return f"rag_{st.session_state.rag_session_id}"


def get_gemini_embeddings():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key
    )


def extract_text(file_obj) -> str:
    name = file_obj.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_obj)
    elif name.endswith(".docx"):
        return extract_text_from_docx(file_obj)
    return ""


def process_documents(uploaded_files):
    """
    Xử lý và vector hóa tài liệu vào ChromaDB.
    Mỗi session có collection riêng biệt.
    """
    embeddings = get_gemini_embeddings()
    if not embeddings:
        return False, "Thiếu cấu hình GEMINI_API_KEY trong file .env."

    documents = []
    for f in uploaded_files:
        text = extract_text(f)
        if text and not text.startswith("Lỗi"):
            doc = Document(
                page_content=text,
                metadata={"source": f.name, "type": f.name.split(".")[-1].upper()}
            )
            documents.append(doc)

    if not documents:
        return False, "Không thể trích xuất văn bản từ các file đã tải lên."

    # Chunking tối ưu cho văn bản hành chính Việt Nam
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
    )
    docs = text_splitter.split_documents(documents)

    try:
        collection_name = _get_session_collection()
        # Chroma v0.4+ tự động persist
        Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=PERSIST_DIRECTORY,
            collection_name=collection_name
        )
        st.session_state.rag_ready = True
        st.session_state.rag_doc_count = len(uploaded_files)
        return True, f"Thành công — Đã xử lý {len(docs)} chunks từ {len(uploaded_files)} tài liệu."
    except Exception as e:
        return False, str(e)


def query_rag(query: str) -> str:
    """
    Truy vấn RAG với ngữ cảnh từ collection của session hiện tại.
    """
    embeddings = get_gemini_embeddings()
    if not embeddings:
        return "Lỗi: Không tìm thấy GEMINI_API_KEY trong file .env."

    collection_name = _get_session_collection()
    persist_path = os.path.join(PERSIST_DIRECTORY, collection_name)

    if not os.path.exists(PERSIST_DIRECTORY):
        return "Cơ sở dữ liệu tri thức chưa được xây dựng. Vui lòng tải tài liệu lên trước (Cột bên trái)."

    try:
        vectordb = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings,
            collection_name=collection_name
        )

        # Kiểm tra collection có dữ liệu không
        if vectordb._collection.count() == 0:
            return "Cơ sở dữ liệu tri thức chưa có dữ liệu. Vui lòng tải tài liệu lên và nhấn 'Vector hóa'."

        retriever = vectordb.as_retriever(search_kwargs={"k": 7})
        docs = retriever.invoke(query)

        context = "\n\n".join([
            f"--- [{d.metadata.get('type', 'Tài liệu')}] Nguồn: {d.metadata.get('source', 'Unknown')} ---\n{d.page_content}"
            for d in docs
        ])

        prompt = f"""
Bạn là một Chuyên gia Quản trị Công và Thẩm tra Chính sách cấp cao của Hội đồng Nhân dân tỉnh Thanh Hóa.

[NGỮ CẢNH TÀI LIỆU ĐƯỢC TRUY XUẤT]:
{context}

[YÊU CẦU PHÂN TÍCH]:
{query}

HƯỚNG DẪN TRẢ LỜI (BẮT BUỘC TUÂN THỦ):
1. Trình bày dưới dạng **báo cáo tham mưu có cấu trúc** (dùng ##, ###, bullet points).
2. **Chỉ trích dẫn thông tin CÓ TRONG ngữ cảnh**. Nếu thiếu, ghi rõ: "Tài liệu hiện tại chưa đề cập đến...".
3. Nếu phát hiện **mâu thuẫn số liệu** giữa các báo cáo, phải in đậm và chỉ rõ nguồn.
4. Cuối báo cáo: Đưa ra **kiến nghị và gợi ý câu hỏi chất vấn** cụ thể cho Đại biểu.
5. Sử dụng ngôn ngữ hành chính nhà nước chuẩn mực.
"""
        response = generate_text(prompt, use_pro=True)
        return response

    except Exception as e:
        return f"Lỗi trong quá trình truy vấn RAG: {str(e)}"
