import streamlit as st
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from utils.auth_helper import require_auth, ADMIN_EMAIL
from utils.ui_helper import set_premium_css, draw_module_header, draw_sidebar

# ─── CẤU HÌNH TRANG ──────────────────────────────────────────────────────────
# Áp dụng giao diện Premium
set_premium_css()

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
st.markdown("### 📈 Theo dõi API Gemini Usage")

stats = database.get_api_usage_stats()

c_api1, c_api2, c_api3 = st.columns(3)
with c_api1:
    st.metric("🚀 Tổng số yêu cầu AI", stats["total"])
with c_api2:
    if stats["daily"]:
        st.metric("📅 Lượt dùng hôm nay", stats["daily"][0][1])
    else:
        st.metric("📅 Lượt dùng hôm nay", 0)
with c_api3:
    st.metric("🤖 Số Model đã dùng", len(stats["by_model"]))

# Phân bổ theo Model và User
tab1, tab2, tab3 = st.tabs(["📊 Theo Model", "👤 Theo Người dùng", "📜 Nhật ký hệ thống"])

with tab1:
    if stats["detailed"]:
        import pandas as pd
        df_detailed = pd.DataFrame(stats["detailed"], columns=[
            "Model ID", "Tổng số Request", "Thành công", "Lỗi", "Input Tokens", "Output Tokens"
        ])
        
        # Thêm tỷ lệ thành công
        df_detailed["Tỷ lệ %"] = (df_detailed["Thành công"] / df_detailed["Tổng số Request"] * 100).round(1).astype(str) + "%"
        
        st.markdown("#### 📊 Chi tiết Hiệu năng & Dung lượng (Chuẩn Google AI Studio)")
        st.dataframe(df_detailed, use_container_width=True, hide_index=True)
        
        # Biểu đồ tóm tắt
        st.bar_chart(df_detailed.set_index("Model ID")[["Input Tokens", "Output Tokens"]])
    else:
        st.info("Chưa có dữ liệu chi tiết sử dụng theo Model.")

with tab2:
    if stats["by_user"]:
        import pandas as pd
        df_user = pd.DataFrame(list(stats["by_user"].items()), columns=["Email", "Số lượt"])
        st.table(df_user)
    else:
        st.info("Chưa có dữ liệu sử dụng theo Người dùng.")

with tab3:
    import pandas as pd
    col_log1, col_log2 = st.columns(2)
    
    with col_log1:
        st.markdown("#### 🔑 Lịch sử Đăng nhập (Gần nhất)")
        login_data = database.get_login_logs(50)
        if login_data:
            df_login = pd.DataFrame(login_data)
            st.dataframe(df_login[["timestamp", "email", "ip_address", "user_agent"]], use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có nhật ký đăng nhập.")
            
    with col_log2:
        st.markdown("#### 🛠️ Nhật ký Thao tác")
        action_data = database.get_action_logs(100)
        if action_data:
            df_action = pd.DataFrame(action_data)
            st.dataframe(df_action[["timestamp", "email", "action", "module", "detail"]], use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có nhật ký thao tác.")

# --- MỚI: TÌNH TRẠNG LIVE TỪ GOOGLE ---
st.markdown("---")
st.markdown("### 🌐 Tình trạng Kết nối AI (Live Check)")
if st.button("🔄 Kiểm tra kết nối trực tiếp đến các Provider"):
    from utils.gemini_client import check_api_status
    with st.spinner("Đang ping hệ thống AI..."):
        health_results = check_api_status()
        
        cols = st.columns(len(health_results))
        for i, (model_name, info) in enumerate(health_results.items()):
            with cols[i]:
                st.markdown(f"**{model_name}**")
                status = info.get("status", "")
                if "✅" in status:
                    st.success(status)
                elif "⚠️" in status:
                    st.warning(status)
                else:
                    st.error(status)

st.markdown("---")
st.caption("Giao diện Quản trị viên — Bảo mật 2 lớp. Mọi thay đổi đều được ghi lại nhật ký hệ thống.")
