import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

"""
rag_engine.py — RAG cho Legislative Intelligence
LangChain + ChromaDB + Embedding Fallback:
  Tầng 1: Gemini Embedding (Google)
  Tầng 2: OpenAI text-embedding-3-small qua ShopAIKey proxy (Anthropic key)
Session-isolated collections.
"""
import uuid
import time
import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from dotenv import load_dotenv
from utils.doc_helper import extract_text_from_pdf, extract_text_from_docx

load_dotenv(override=True)

PERSIST_DIRECTORY = "chroma_db"

# ── Cấu hình ShopAIKey proxy ─────────────────────────────────────────────────
_SHOPAIKEY_BASE_URL = "https://api.shopaikey.com/v1"
_SHOPAIKEY_API_KEY  = "sk-s4sEA3IauTs0JA0bHwq4S3C7wDXtj7EHZHpB8IZbmvxSIALz"
_SHOPAIKEY_EMB_MODEL = "text-embedding-3-small"

# ── Cấu hình batch/retry ─────────────────────────────────────────────────────
_BATCH_SIZE    = 25            # Tăng số chunk mỗi lần gửi lên Embedding API để tăng tốc độ
_BATCH_DELAY   = 0.5           # Giảm thời gian chờ giữa các batch
_RETRY_DELAYS  = [10, 30, 60] # backoff khi bị rate-limit


# ═══════════════════════════════════════════════════════════════════════════════
#  EMBEDDING PROVIDERS
# ═══════════════════════════════════════════════════════════════════════════════

class _ShopAIKeyEmbeddings(Embeddings):
    """
    OpenAI Embeddings qua proxy ShopAIKey (https://api.shopaikey.com/v1).
    Dùng cùng API key đã cấu hình cho Claude/Anthropic.
    """
    def __init__(self):
        import openai
        self._client = openai.OpenAI(
            api_key=_SHOPAIKEY_API_KEY,
            base_url=_SHOPAIKEY_BASE_URL,
        )
        self._model = _SHOPAIKEY_EMB_MODEL

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embeddings.create(input=texts, model=self._model)
        return [item.embedding for item in resp.data]

    def embed_query(self, text: str) -> list[float]:
        resp = self._client.embeddings.create(input=[text], model=self._model)
        return resp.data[0].embedding


def _build_gemini_embeddings():
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from utils.gemini_client import _get_api_key
    key = _get_api_key("gemini")
    if not key:
        raise ValueError("Thiếu GEMINI_API_KEY")
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2",
        google_api_key=key,
    )


def _get_embeddings_with_fallback() -> tuple[Embeddings, str]:
    """
    Trả về (embedding_object, provider_name).
    Thứ tự ưu tiên:
      1. Gemini Embedding
      2. OpenAI text-embedding-3-small qua ShopAIKey (Anthropic proxy)
    """
    # ── Tầng 1: Gemini Embedding ─────────────────────────────────────────────
    try:
        emb = _build_gemini_embeddings()
        emb.embed_query("test")          # kiểm tra quota
        return emb, "Gemini Embedding"
    except Exception as e:
        err = str(e)
        is_quota = "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower()
        reason = "đã hết quota" if is_quota else f"lỗi: `{err[:100]}`"
        st.warning(
            f"⚠️ **Gemini Embedding** {reason}. "
            "Hệ thống tự động chuyển sang **Anthropic (ShopAIKey) Embedding**..."
        )
        # Luôn fallthrough sang tầng 2, bất kể loại lỗi

    # ── Tầng 2: OpenAI Embeddings qua ShopAIKey proxy ───────────────────────
    try:
        emb = _ShopAIKeyEmbeddings()
        emb.embed_query("test")          # kiểm tra kết nối
        st.success("✅ Đang dùng **Anthropic (ShopAIKey) Embedding** thay thế.")
        return emb, "Anthropic/ShopAIKey (text-embedding-3-small)"
    except Exception as e:
        raise RuntimeError(
            f"Cả Gemini lẫn ShopAIKey Embedding đều không khả dụng.\n"
            f"Lỗi ShopAIKey: {e}"
        )


@st.cache_resource
def _get_embeddings() -> tuple[Embeddings, str]:
    """Cache kết quả chọn embedding để tránh re-init mỗi lần rerun."""
    return _get_embeddings_with_fallback()


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _get_session_collection() -> str:
    if "rag_session_id" not in st.session_state:
        st.session_state.rag_session_id = str(uuid.uuid4())[:8]
    return f"rag_{st.session_state.rag_session_id}"


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


def _embed_with_retry(chunks: list, embeddings: Embeddings, collection_name: str) -> Embeddings:
    """
    Gửi chunks theo từng batch nhỏ.
    - Nếu bị 429: retry theo backoff.
    - Nếu hết retry: tự động chuyển sang ShopAIKey embedding và tiếp tục.
    Trả về embedding object thực sự đã được dùng (có thể đã đổi provider).
    """
    vectordb = None
    total = len(chunks)
    num_batches = -(-total // _BATCH_SIZE)
    current_emb = embeddings

    for batch_idx, start in enumerate(range(0, total, _BATCH_SIZE)):
        batch = chunks[start: start + _BATCH_SIZE]
        attempt = 0

        while True:
            try:
                if vectordb is None:
                    vectordb = Chroma.from_documents(
                        documents=batch,
                        embedding=current_emb,
                        persist_directory=PERSIST_DIRECTORY,
                        collection_name=collection_name,
                    )
                else:
                    vectordb.add_documents(batch)

                if start + _BATCH_SIZE < total:
                    time.sleep(_BATCH_DELAY)
                break  # thành công

            except Exception as e:
                err = str(e)
                is_gemini = isinstance(current_emb, type(_build_gemini_embeddings()))
                is_quota  = "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower()
                # Coi mọi lỗi từ Gemini (kể cả IndexError, empty list...) như lỗi quota
                is_gemini_err = is_quota or isinstance(e, (IndexError, ValueError))

                if is_gemini_err and attempt < len(_RETRY_DELAYS) and is_quota:
                    # Chỉ retry nếu là lỗi quota rõ ràng
                    wait = _RETRY_DELAYS[attempt]
                    st.warning(
                        f"⏳ Đang chờ **{wait}s** do vượt quota Gemini "
                        f"(batch {batch_idx + 1}/{num_batches})..."
                    )
                    time.sleep(wait)
                    attempt += 1

                elif is_gemini_err or is_quota:
                    # Lỗi Gemini không phục hồi được → chuyển sang ShopAIKey
                    reason = "hết quota" if is_quota else f"lỗi không xác định (`{err[:80]}`)"
                    st.warning(
                        f"🔄 Gemini Embedding {reason}. "
                        "**Tự động chuyển sang Anthropic (ShopAIKey) Embedding...**"
                    )
                    _get_embeddings.clear()   # xoá cache để provider mới được chọn
                    try:
                        current_emb = _ShopAIKeyEmbeddings()
                        current_emb.embed_query("test")
                        st.success("✅ Đã chuyển sang **Anthropic/ShopAIKey Embedding**. Tiếp tục...")
                        attempt = 0  # reset retry cho provider mới
                    except Exception as fe:
                        raise RuntimeError(
                            f"Cả Gemini và ShopAIKey đều lỗi. ShopAIKey: {fe}"
                        ) from e
                else:
                    # Lỗi không liên quan đến embedding provider → bắn thẳng
                    raise

    return current_emb


# ═══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def process_documents(uploaded_files):
    """Vectorize uploaded documents into ChromaDB (per-session collection)."""
    try:
        embeddings, provider = _get_embeddings()
        st.info(f"🔧 Đang dùng **{provider}** để vector hóa tài liệu...")
    except Exception as e:
        return False, f"Không thể khởi tạo embedding engine: {e}"

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
        final_emb = _embed_with_retry(chunks, embeddings, collection_name)
        # Lưu provider thực sự đã dùng
        final_provider = provider
        if isinstance(final_emb, _ShopAIKeyEmbeddings):
            final_provider = "Anthropic/ShopAIKey (text-embedding-3-small)"
        st.session_state.rag_ready = True
        st.session_state.rag_doc_count = len(uploaded_files)
        return True, (
            f"Thành công — Đã xử lý {len(chunks)} chunks "
            f"từ {len(uploaded_files)} tài liệu. (Provider: {final_provider})"
        )
    except Exception as e:
        return False, str(e)


def query_rag(query: str) -> str:
    """Query RAG with context from the current session's collection."""
    try:
        embeddings, _ = _get_embeddings()
    except Exception as e:
        return f"Lỗi: Không thể khởi tạo embedding engine: {e}"

    if not os.path.exists(PERSIST_DIRECTORY):
        return "Cơ sở dữ liệu tri thức chưa được xây dựng. Vui lòng tải tài liệu lên trước."

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
            f"--- [{d.metadata.get('type', 'Tài liệu')}] "
            f"Nguồn: {d.metadata.get('source', 'Unknown')} ---\n{d.page_content}"
            for d in docs
        )

        prompt = f"""Bạn là một Chuyên gia Quản trị Công và Thẩm tra Chính sách cấp cao của Hội đồng Nhân dân tỉnh Thanh Hóa.
        
        QUAN ĐIỂM PHÁP LÝ: Bạn BẮT BUỘC sử dụng Google Search để kiểm tra, đối chiếu và cập nhật các Luật, Nghị định, quy định mới nhất đang có hiệu lực liên quan đến vấn đề đang phân tích. Tuyệt đối không sử dụng các văn bản luật cũ đã hết hiệu lực. 
        
        Ưu tiên áp dụng các văn bản quy phạm pháp luật chuyên ngành mới nhất. Chỉ nhắc đến các luật cụ thể (như Luật Tổ chức chính quyền địa phương năm 2025) khi nội dung phân tích trực tiếp liên quan đến tổ chức bộ máy và thẩm quyền của chính quyền địa phương.

        [NGỮ CẢNH TÀI LIỆU ĐƯỢC TRUY XUẤT]:
        {context}

        [YÊU CẦU PHÂN TÍCH]:
        {query}

        HƯỚNG DẪN TRẢ LỜI (BẮT BUỘC TUÂN THỦ):
        1. Trình bày dưới dạng **báo cáo tham mưu có cấu trúc** (dùng ##, ###, bullet points).
        2. **Luôn đối chiếu với các quy định pháp luật mới nhất** để đánh giá tính hợp pháp và thẩm quyền.
        3. **Chỉ trích dẫn thông tin CÓ TRONG ngữ cảnh**. Nếu thiếu, ghi rõ: "Tài liệu hiện tại chưa đề cập đến...".
        4. Nếu phát hiện **mâu thuẫn số liệu** hoặc mâu thuẫn với quy định pháp luật hiện hành, phải in đậm và chỉ rõ.
        5. Cuối báo cáo: Đưa ra **kiến nghị và gợi ý câu hỏi chất vấn** cụ thể cho Đại biểu.
        6. Sử dụng ngôn ngữ hành chính nhà nước chuẩn mực."""

        from utils.gemini_client import generate_text
        return generate_text(prompt, use_pro=True)
    except Exception as e:
        return f"Lỗi trong quá trình truy vấn RAG: {e}"
