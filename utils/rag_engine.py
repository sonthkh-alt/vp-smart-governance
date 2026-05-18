import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

"""
rag_engine.py — RAG cho Legislative Intelligence
LangChain + ChromaDB + Embedding Fallback (Gemini → Voyage/Anthropic → Local).
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
from utils.gemini_client import generate_text, _get_api_key

load_dotenv(override=True)

PERSIST_DIRECTORY = "chroma_db"

# ── Cấu hình batch/retry ──────────────────────────────────────────────────────
_BATCH_SIZE = 5               # số chunk mỗi lần gửi lên Embedding API
_BATCH_DELAY = 2              # giây chờ giữa các batch bình thường
_RETRY_DELAYS = [10, 30, 60]  # giây chờ khi bị rate-limit (backoff)


# ═══════════════════════════════════════════════════════════════════════════════
#  EMBEDDING PROVIDERS — Fallback theo thứ tự: Gemini → Voyage → Local
# ═══════════════════════════════════════════════════════════════════════════════

class _VoyageEmbeddings(Embeddings):
    """Wrapper cho Anthropic Voyage AI Embeddings (voyageai SDK)."""

    def __init__(self, api_key: str, model: str = "voyage-3"):
        import voyageai
        self._client = voyageai.Client(api_key=api_key)
        self._model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        result = self._client.embed(texts, model=self._model, input_type="document")
        return result.embeddings

    def embed_query(self, text: str) -> list[float]:
        result = self._client.embed([text], model=self._model, input_type="query")
        return result.embeddings[0]


class _LocalEmbeddings(Embeddings):
    """Wrapper cho sentence-transformers (chạy local, không cần API)."""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, convert_to_numpy=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode([text], convert_to_numpy=True)[0].tolist()


def _get_embeddings_with_fallback() -> tuple[Embeddings, str]:
    """
    Trả về (embedding_object, provider_name).
    Thứ tự ưu tiên: Gemini Embedding → Voyage AI (Anthropic) → Local sentence-transformers.
    """
    # ── Tầng 1: Gemini Embedding ─────────────────────────────────────────────
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        gemini_key = _get_api_key("gemini")
        if gemini_key:
            emb = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-2",
                google_api_key=gemini_key,
            )
            # Kiểm tra nhanh xem quota còn không
            emb.embed_query("test")
            return emb, "Gemini Embedding"
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
            st.warning("⚠️ **Gemini Embedding** đã hết quota. Hệ thống tự động chuyển sang **Anthropic Voyage AI**...")
        else:
            st.warning(f"⚠️ Gemini Embedding lỗi ({err[:80]}). Chuyển sang Anthropic Voyage AI...")

    # ── Tầng 2: Anthropic Voyage AI Embedding ────────────────────────────────
    try:
        import voyageai
        voyage_key = os.getenv("VOYAGE_API_KEY") or ""
        try:
            voyage_key = st.secrets.get("VOYAGE_API_KEY", voyage_key)
        except Exception:
            pass

        if voyage_key:
            emb = _VoyageEmbeddings(api_key=voyage_key)
            emb.embed_query("test")  # kiểm tra kết nối
            return emb, "Anthropic Voyage-3"
        else:
            st.warning("⚠️ Chưa có **VOYAGE_API_KEY**. Chuyển sang embedding local...")
    except ImportError:
        st.warning("⚠️ Thư viện `voyageai` chưa được cài đặt. Chuyển sang embedding local...")
    except Exception as e:
        st.warning(f"⚠️ Voyage AI lỗi ({str(e)[:80]}). Chuyển sang embedding local...")

    # ── Tầng 3: Local sentence-transformers (hoàn toàn offline/miễn phí) ─────
    try:
        import sentence_transformers  # noqa
        emb = _LocalEmbeddings()
        return emb, "Local (sentence-transformers)"
    except ImportError:
        raise RuntimeError(
            "Không thể khởi tạo bất kỳ embedding provider nào.\n"
            "Vui lòng cài: pip install sentence-transformers"
        )


@st.cache_resource
def _get_embeddings() -> tuple[Embeddings, str]:
    """Cache kết quả lựa chọn embedding để tránh re-init mỗi lần rerun."""
    return _get_embeddings_with_fallback()


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
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


def _embed_with_retry(chunks: list, embeddings: Embeddings, collection_name: str) -> None:
    """Gửi chunks theo từng batch nhỏ với retry + fallback tự động khi bị 429."""
    vectordb = None
    total = len(chunks)
    num_batches = -(-total // _BATCH_SIZE)  # ceiling division

    for batch_idx, start in enumerate(range(0, total, _BATCH_SIZE)):
        batch = chunks[start: start + _BATCH_SIZE]
        attempt = 0
        current_embeddings = embeddings  # có thể bị thay thế khi fallback

        while True:
            try:
                if vectordb is None:
                    vectordb = Chroma.from_documents(
                        documents=batch,
                        embedding=current_embeddings,
                        persist_directory=PERSIST_DIRECTORY,
                        collection_name=collection_name,
                    )
                else:
                    vectordb.add_documents(batch)

                # Delay nhỏ giữa các batch để không vượt rate limit
                if start + _BATCH_SIZE < total:
                    time.sleep(_BATCH_DELAY)
                break  # batch thành công → thoát vòng retry

            except Exception as e:
                err = str(e)
                is_quota_err = "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower()

                if is_quota_err and attempt < len(_RETRY_DELAYS):
                    wait = _RETRY_DELAYS[attempt]
                    st.warning(
                        f"⏳ Đang chờ **{wait}s** do vượt quota "
                        f"(batch {batch_idx + 1}/{num_batches})..."
                    )
                    time.sleep(wait)
                    attempt += 1

                elif is_quota_err and attempt >= len(_RETRY_DELAYS):
                    # Đã thử hết retry → fallback sang provider tiếp theo
                    st.warning(
                        "🔄 Gemini Embedding đã hết quota hoàn toàn. "
                        "**Tự động chuyển sang Anthropic Voyage AI...**"
                    )
                    # Xóa cache để buộc chọn lại provider
                    _get_embeddings.clear()
                    st.session_state["_embedding_fallback"] = True

                    try:
                        voyage_key = os.getenv("VOYAGE_API_KEY") or ""
                        try:
                            voyage_key = st.secrets.get("VOYAGE_API_KEY", voyage_key)
                        except Exception:
                            pass

                        if not voyage_key:
                            raise ValueError("Chưa có VOYAGE_API_KEY")

                        current_embeddings = _VoyageEmbeddings(api_key=voyage_key)
                        st.info("✅ Đã chuyển sang **Anthropic Voyage-3 Embedding**. Tiếp tục vector hóa...")
                        attempt = 0  # reset retry counter cho provider mới
                    except Exception as ve:
                        raise RuntimeError(
                            f"Cả Gemini và Voyage AI đều không khả dụng. "
                            f"Voyage lỗi: {ve}"
                        ) from e
                else:
                    raise


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
        _embed_with_retry(chunks, embeddings, collection_name)
        st.session_state.rag_ready = True
        st.session_state.rag_doc_count = len(uploaded_files)
        provider_used = st.session_state.get("_embedding_fallback") and "Anthropic Voyage-3" or provider
        return True, f"Thành công — Đã xử lý {len(chunks)} chunks từ {len(uploaded_files)} tài liệu. (Provider: {provider_used})"
    except Exception as e:
        return False, str(e)


def query_rag(query: str) -> str:
    """Query RAG with context from the current session's collection."""
    try:
        embeddings, _ = _get_embeddings()
    except Exception as e:
        return f"Lỗi: Không thể khởi tạo embedding engine: {e}"

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

        return generate_text(prompt, use_pro=True)
    except Exception as e:
        return f"Lỗi trong quá trình truy vấn RAG: {e}"
