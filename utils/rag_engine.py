"""
rag_engine.py — RAG cho Legislative Intelligence
LangChain + ChromaDB + Gemini Embeddings. Session-isolated collections.
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
    if "rag_session_id" not in st.session_state:
        st.session_state.rag_session_id = str(uuid.uuid4())[:8]
    return f"rag_{st.session_state.rag_session_id}"


@st.cache_resource
def _get_embeddings():
    """Cache embeddings model across reruns to avoid re-initialization."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key,
    )


def _extract_text(file_obj) -> str:
    name = file_obj.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_obj)
    if name.endswith(".docx"):
        return extract_text_from_docx(file_obj)
    return ""


_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1200, chunk_overlap=200,
    separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
)


def process_documents(uploaded_files):
    """Vectorize uploaded documents into ChromaDB (per-session collection)."""
    embeddings = _get_embeddings()
    if not embeddings:
        return False, "Thiếu cấu hình GEMINI_API_KEY trong file .env."

    documents = []
    for f in uploaded_files:
        text = _extract_text(f)
        if text and not text.startswith("Lỗi"):
            documents.append(Document(
                page_content=text,
                metadata={"source": f.name, "type": f.name.rsplit(".", 1)[-1].upper()},
            ))

    if not documents:
        return False, "Không thể trích xuất văn bản từ các file đã tải lên."

    try:
        chunks = _SPLITTER.split_documents(documents)
        collection_name = _get_session_collection()
        Chroma.from_documents(
            documents=chunks, embedding=embeddings,
            persist_directory=PERSIST_DIRECTORY,
            collection_name=collection_name,
        )
        st.session_state.rag_ready = True
        st.session_state.rag_doc_count = len(uploaded_files)
        return True, f"Thành công — Đã xử lý {len(chunks)} chunks từ {len(uploaded_files)} tài liệu."
    except Exception as e:
        return False, str(e)


def query_rag(query: str) -> str:
    """Query RAG with context from the current session's collection."""
    embeddings = _get_embeddings()
    if not embeddings:
        return "Lỗi: Không tìm thấy GEMINI_API_KEY trong file .env."

    if not os.path.exists(PERSIST_DIRECTORY):
        return "Cơ sở dữ liệu tri thức chưa được xây dựng. Vui lòng tải tài liệu lên trước (Cột bên trái)."

    try:
        collection_name = _get_session_collection()
        vectordb = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings,
            collection_name=collection_name,
        )

        if vectordb._collection.count() == 0:
            return "Cơ sở dữ liệu tri thức chưa có dữ liệu. Vui lòng tải tài liệu lên và nhấn 'Vector hóa'."

        docs = vectordb.as_retriever(search_kwargs={"k": 7}).invoke(query)

        context = "\n\n".join(
            f"--- [{d.metadata.get('type', 'Tài liệu')}] Nguồn: {d.metadata.get('source', 'Unknown')} ---\n{d.page_content}"
            for d in docs
        )

        prompt = f"""Bạn là một Chuyên gia Quản trị Công và Thẩm tra Chính sách cấp cao của Hội đồng Nhân dân tỉnh Thanh Hóa.
        
        CĂN CỨ PHÁP LÝ CỐT LÕI: Luật Tổ chức chính quyền địa phương số 72/2025/QH15 (Chính quyền 2 cấp: Tỉnh và Xã; Xóa bỏ cấp Huyện; Phân cấp/Phân quyền mạnh mẽ).

        [NGỮ CẢNH TÀI LIỆU ĐƯỢC TRUY XUẤT]:
        {context}

        [YÊU CẦU PHÂN TÍCH]:
        {query}

        HƯỚNG DẪN TRẢ LỜI (BẮT BUỘC TUÂN THỦ):
        1. Trình bày dưới dạng **báo cáo tham mưu có cấu trúc** (dùng ##, ###, bullet points).
        2. **Luôn đối chiếu với Luật 72/2025/QH15** để đánh giá tính hợp pháp và thẩm quyền.
        3. **Chỉ trích dẫn thông tin CÓ TRONG ngữ cảnh**. Nếu thiếu, ghi rõ: "Tài liệu hiện tại chưa đề cập đến...".
        4. Nếu phát hiện **mâu thuẫn số liệu** hoặc mâu thuẫn với Luật mới, phải in đậm và chỉ rõ.
        5. Cuối báo cáo: Đưa ra **kiến nghị và gợi ý câu hỏi chất vấn** cụ thể cho Đại biểu.
        6. Sử dụng ngôn ngữ hành chính nhà nước chuẩn mực."""

        return generate_text(prompt, use_pro=True)
    except Exception as e:
        return f"Lỗi trong quá trình truy vấn RAG: {e}"
