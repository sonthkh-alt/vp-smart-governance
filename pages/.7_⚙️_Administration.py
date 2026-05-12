import streamlit as st
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from utils.auth_helper import require_auth, ADMIN_EMAIL
from utils.ui_helper import set_premium_css, draw_module_header, draw_sidebar

# ─── CẤU HÌNH TRANG ──────────────────────────────────────────────────────────
st.set_page_config(page_title="Quản trị Hệ thống", page_icon="⚙️", layout="wide")

# Áp dụng giao diện & Sidebar
set_premium_css()
draw_sidebar()

# Kiểm tra quyền Admin
if "user_info" not in st.session_state or st.session_state.user_info.get("email") != ADMIN_EMAIL:
    st.error("### 🚫 Truy cập bị từ chối\nTrang này chỉ dành cho Quản trị viên hệ thống.")
    st.stop()

draw_module_header(
    "System Administration",
    "⚙️",
    "Quản lý người dùng, phê duyệt thành viên và cấp hạn mức truy vấn AI."
)

# ─── THỐNG KÊ TỔNG QUAN ──────────────────────────────────────────────────────
users = database.get_all_users()
total_users = len(users)
pending_users = len([u for u in users if not u["is_approved"] and not u["is_admin"]])
total_credits = sum([u["credits"] for u in users if not u["is_admin"]])

k1, k2, k3 = st.columns(3)
k1.metric("👥 Tổng người dùng", total_users)
k2.metric("⏳ Đang chờ duyệt", pending_users, delta=pending_users, delta_color="inverse" if pending_users > 0 else "normal")
k3.metric("🪙 Tổng Credit cấp", total_credits)

st.markdown("---")

# ─── DANH SÁCH NGƯỜI DÙNG ─────────────────────────────────────────────────────
st.markdown("### 📋 Quản lý Thành viên")

# Bộ lọc
col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    search = st.text_input("🔍 Tìm kiếm email hoặc tên...", placeholder="Nhập từ khóa...")
with col_f2:
    filter_status = st.selectbox("Trạng thái", ["Tất cả", "Chờ phê duyệt", "Đã phê duyệt", "Admin"])

filtered_users = users.copy()
if search:
    filtered_users = [u for u in filtered_users if search.lower() in u["email"].lower() or search.lower() in u["full_name"].lower()]
if filter_status == "Chờ phê duyệt":
    filtered_users = [u for u in filtered_users if not u["is_approved"] and not u["is_admin"]]
elif filter_status == "Đã phê duyệt":
    filtered_users = [u for u in filtered_users if u["is_approved"] and not u["is_admin"]]
elif filter_status == "Admin":
    filtered_users = [u for u in filtered_users if u["is_admin"]]

# Hiển thị bảng và form cập nhật
for u in filtered_users:
    with st.expander(f"{'👑' if u['is_admin'] else '👤'} {u['full_name']} ({u['email']}) — {u['created_at']}"):
        c1, c2, c3 = st.columns([1, 1, 1])
        
        with c1:
            st.markdown(f"**Trạng thái:** {'✅ Đã phê duyệt' if u['is_approved'] or u['is_admin'] else '⏳ Chờ duyệt'}")
            st.markdown(f"**Lượt truy vấn còn lại:** {u['credits']}")
            
        with c2:
            if not u["is_admin"]:
                new_approved = st.checkbox("Đã phê duyệt", value=bool(u["is_approved"]), key=f"app_{u['email']}")
                new_credits = st.number_input("Số lượt truy vấn AI", min_value=0, max_value=9999, value=u["credits"], key=f"cred_{u['email']}")
            else:
                st.info("Tài khoản Quản trị viên (Full Access)")
                
        with c3:
            if not u["is_admin"]:
                if st.button("💾 Cập nhật thay đổi", key=f"btn_{u['email']}", use_container_width=True, type="primary"):
                    database.update_user_status(u["email"], 1 if new_approved else 0, new_credits)
                    st.success(f"Đã cập nhật cho {u['email']}")
                    st.rerun()
            else:
                st.button("⚙️ Cài đặt hệ thống", disabled=True, use_container_width=True)

st.markdown("---")
st.caption("Giao diện Quản trị viên — Bảo mật 2 lớp. Mọi thay đổi đều được ghi lại nhật ký hệ thống.")
