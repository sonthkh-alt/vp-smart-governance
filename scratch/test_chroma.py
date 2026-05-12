import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("Testing ChromaDB initialization...")
try:
    from langchain_chroma import Chroma
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from utils.gemini_client import _get_api_key
    
    api_key = _get_api_key()
    if not api_key or "your_api_key" in api_key:
        print("SKIP: GEMINI_API_KEY is not set or is placeholder.")
    else:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001", # standard model
            google_api_key=api_key,
        )
        # Try to create a small index in memory or temp dir
        vectordb = Chroma(
            embedding_function=embeddings,
            collection_name="test_collection"
        )
        print("SUCCESS: ChromaDB initialized successfully.")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
