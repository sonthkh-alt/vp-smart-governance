import streamlit as st
from supabase import create_client, Client
import database
import os
from datetime import datetime

# Khởi tạo Supabase Client an toàn
supabase = None
try:
    if "supabase" in st.secrets:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        supabase: Client = create_client(url, key)
    else:
        st.warning("⚠️ Thiếu cấu hình [supabase] trong Secrets. Vui lòng cấu hình để sử dụng tính năng lưu trữ.")
except Exception as e:
    st.error(f"Không thể khởi tạo kết nối Supabase: {e}")

BUCKET_NAME = "reference-docs"

# Tự động tạo Bucket nếu chưa có (Chỉ chạy được nếu dùng Service Role Key)
if supabase:
    try:
        # Kiểm tra xem bucket đã tồn tại chưa
        buckets = supabase.storage.list_buckets()
        exists = any(b.name == BUCKET_NAME for b in buckets)
        if not exists:
            supabase.storage.create_bucket(BUCKET_NAME, options={"public": True})
            print(f"Đã tạo Bucket {BUCKET_NAME} thành công.")
    except Exception as be:
        print(f"Lưu ý: Không thể tự tạo bucket (có thể do quyền): {be}")

def upload_file(uploaded_file, module="Chưa xác định"):
    """
    Upload file lên Supabase Storage và lưu metadata vào Database.
    """
    if uploaded_file is None or supabase is None:
        if supabase is None: st.error("Lỗi: Chưa kết nối được tới hệ thống lưu trữ Supabase.")
        return None

    try:
        # 1. Tạo tên file duy nhất để tránh trùng lặp trên Storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = uploaded_file.name.replace(" ", "_")
        storage_path = f"{module}/{timestamp}_{safe_filename}"

        # 2. Upload lên Supabase Storage
        file_content = uploaded_file.getvalue()
        supabase.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": uploaded_file.type}
        )

        # 3. Lưu Metadata vào Database
        user_email = st.session_state.user_info.get("email") if st.session_state.get("is_logged_in") else "Khách"
        database.save_document(
            file_name=uploaded_file.name,
            file_type=uploaded_file.type,
            file_size=uploaded_file.size,
            storage_path=storage_path,
            uploader_email=user_email,
            module=module
        )
        
        return storage_path
    except Exception as e:
        st.error(f"Lỗi khi upload file: {str(e)}")
        return None

def get_file_url(storage_path):
    """
    Lấy URL công khai của file.
    """
    if supabase is None: return None
    try:
        res = supabase.storage.from_(BUCKET_NAME).get_public_url(storage_path)
        return res
    except Exception as e:
        print(f"Lỗi khi lấy URL: {e}")
        return None

def delete_file(doc_id, storage_path):
    """
    Xóa file khỏi Storage và Database.
    """
    if supabase is None: return False
    try:
        # 1. Xóa khỏi Storage
        supabase.storage.from_(BUCKET_NAME).remove([storage_path])
        # 2. Xóa khỏi Database
        database.delete_document(doc_id)
        return True
    except Exception as e:
        st.error(f"Lỗi khi xóa file: {str(e)}")
        return False
