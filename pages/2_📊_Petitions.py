"""
2_📊_Petitions.py — Kiến nghị Cử tri
Dashboard theo dõi, phân tích xu hướng và tham mưu chính sách.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from utils.ui_helper import set_premium_css, draw_module_header, draw_sidebar
from utils.gemini_client import generate_text
from utils.auth_helper import require_auth
import database

st.set_page_config(page_title="Kiến nghị Cử tri", page_icon="📊", layout="wide")

database.init_db()
set_premium_css()
draw_sidebar()

draw_module_header(
    "Constituency Petitions",
    "📊",
    "Phân tích xu hướng, quản lý tiến độ và tham mưu chính sách từ kiến nghị cử tri."
)

# ─── SIDEBAR: Tiếp nhận kiến nghị mới ────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📥 Tiếp nhận Kiến nghị")
    with st.form("petition_form", clear_on_submit=True):
        voter    = st.text_input("Tên cử tri / Đơn vị")
        district = st.selectbox("Huyện / Thị xã / TP", [
            "TP. Thanh Hóa", "TX. Sầm Sơn", "TX. Bỉm Sơn", "KKT Nghi Sơn",
            "Thọ Xuân", "Hoằng Hóa", "Quảng Xương", "Đông Sơn", "Triệu Sơn",
            "Vĩnh Lộc", "Yên Định", "Thiệu Hóa", "Nông Cống"
        ])
        category = st.selectbox("Lĩnh vực", [
            "Giao thông & Hạ tầng", "Môi trường", "Giáo dục & Đào tạo",
            "Y tế", "Đất đai & Nhà ở", "Chính sách xã hội",
            "Kinh tế & Doanh nghiệp", "An ninh trật tự"
        ])
        content  = st.text_area("Nội dung kiến nghị", height=120,
                                placeholder="Mô tả cụ thể nội dung kiến nghị...")
        submitted = st.form_submit_button("💾 Lưu Kiến nghị", use_container_width=True)

        if submitted:
            if content.strip():
                database.save_petition(voter, district, content, category)
                st.success("✅ Đã lưu kiến nghị thành công!")
                st.rerun()
            else:
                st.error("Vui lòng nhập nội dung kiến nghị!")

    st.markdown("---")
    st.markdown("### ⚙️ Cập nhật Trạng thái")
    all_rows = database.get_petitions()
    if all_rows:
        petition_ids = {f"#{r[0]} — {r[4][:40]}...": r[0] for r in all_rows}
        selected_label = st.selectbox("Chọn kiến nghị", list(petition_ids.keys()))
        new_status = st.selectbox("Trạng thái mới", ["Mới", "Đang xử lý", "Đã xong"])
        resolution = st.text_input("Kết quả giải quyết (nếu có)")
        if st.button("✅ Cập nhật", use_container_width=True):
            database.update_petition_status(petition_ids[selected_label], new_status, resolution)
            st.success("Đã cập nhật!")
            st.rerun()

# ─── Load dữ liệu ─────────────────────────────────────────────────────────────
data = database.get_petitions()
df = pd.DataFrame(data, columns=["id", "created_at", "voter_name", "district", "content", "category", "status", "resolution"])

if df.empty:
    sample_data = [
        [1, "2026-05-01", "Nguyễn Văn A", "TP. Thanh Hóa", "Đề nghị sửa chữa đường tránh QL1A bị xuống cấp nghiêm trọng", "Giao thông & Hạ tầng", "Đang xử lý", ""],
        [2, "2026-05-02", "HĐND xã Hải Thượng", "KKT Nghi Sơn", "Ô nhiễm nguồn nước ngầm do chất thải công nghiệp KCN Nghi Sơn", "Môi trường", "Mới", ""],
        [3, "2026-05-03", "Lê Thị C", "TX. Sầm Sơn", "Thiếu quỹ đất xây dựng trường mầm non công lập tại phường Trung Sơn", "Giáo dục & Đào tạo", "Đã xong", "UBND tỉnh đã phê duyệt quy hoạch bổ sung 2ha đất"],
        [4, "2026-05-04", "Hội Nông dân huyện Thọ Xuân", "Thọ Xuân", "Đề nghị hỗ trợ nông dân bị thiệt hại do bão số 3", "Chính sách xã hội", "Đang xử lý", ""],
        [5, "2026-05-05", "Hoàng Văn E", "Quảng Xương", "Nâng cấp, cải tạo Trạm Y tế xã Quảng Thái", "Y tế", "Mới", ""],
        [6, "2026-05-06", "UBMTTQ phường Đông Hương", "TP. Thanh Hóa", "Cải tạo hệ thống thoát nước ngập lụt đường Trường Thi", "Giao thông & Hạ tầng", "Mới", ""],
        [7, "2026-05-07", "Nguyễn Thị G", "Hoằng Hóa", "Giải quyết tranh chấp đất nông nghiệp sau dồn điền đổi thửa", "Đất đai & Nhà ở", "Đang xử lý", ""],
    ]
    df = pd.DataFrame(sample_data, columns=["id", "created_at", "voter_name", "district", "content", "category", "status", "resolution"])

# ─── KPI DASHBOARD ────────────────────────────────────────────────────────────
total    = len(df)
pending  = len(df[df['status'] == 'Mới'])
proc     = len(df[df['status'] == 'Đang xử lý'])
resolved = len(df[df['status'] == 'Đã xong'])
rate     = int(resolved / total * 100) if total > 0 else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("📋 Tổng kiến nghị", total)
k2.metric("🔔 Chưa xử lý",     pending,  delta=f"-{pending}" if pending > 0 else None, delta_color="inverse")
k3.metric("⏳ Đang xử lý",     proc)
k4.metric("✅ Hoàn thành",     resolved)
k5.metric("📈 Tỷ lệ giải quyết", f"{rate}%")

# Progress bar tổng thể
st.progress(rate / 100, text=f"Tiến độ hoàn thành: **{rate}%** ({resolved}/{total} kiến nghị)")

st.markdown("---")

# ─── CHARTS ──────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.markdown("### 📈 Phân loại theo Lĩnh vực")
    color_map = {
        "Giao thông & Hạ tầng": "#3B82F6",
        "Môi trường": "#10B981",
        "Giáo dục & Đào tạo": "#F59E0B",
        "Y tế": "#EF4444",
        "Đất đai & Nhà ở": "#8B5CF6",
        "Chính sách xã hội": "#EC4899",
        "Kinh tế & Doanh nghiệp": "#06B6D4",
        "An ninh trật tự": "#F97316",
    }
    fig_cat = px.pie(
        df, names='category', hole=0.5,
        color='category', color_discrete_map=color_map
    )
    fig_cat.update_traces(textposition='outside', textinfo='percent+label')
    fig_cat.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="white",
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_cat, use_container_width=True)

with c2:
    st.markdown("### 📍 Phân bổ & Trạng thái theo Địa phương")
    cross = df.groupby(['district', 'status']).size().reset_index(name='count')
    fig_dist = px.bar(
        cross, x='district', y='count', color='status',
        barmode='stack',
        color_discrete_map={"Mới": "#EF4444", "Đang xử lý": "#F59E0B", "Đã xong": "#10B981"}
    )
    fig_dist.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="white",
        xaxis_tickangle=-30,
        legend_title="Trạng thái",
        margin=dict(t=20, b=60)
    )
    st.plotly_chart(fig_dist, use_container_width=True)

st.markdown("---")

# ─── AI ANALYSIS ──────────────────────────────────────────────────────────────
st.markdown("### 🧠 Trợ lý AI — Phân tích Xu hướng & Tham mưu Chính sách")
st.caption("AI sẽ phân tích toàn bộ dữ liệu kiến nghị để xác định điểm nóng, đánh giá rủi ro và đề xuất giải pháp vĩ mô.")

if st.button("🔍 CHẠY PHÂN TÍCH AI CHUYÊN SÂU", type="primary"):
    if require_auth("Phân tích AI chuyên sâu"):
        with st.spinner("🧠 AI đang tổng hợp dữ liệu và đánh giá rủi ro xã hội..."):
        data_summary = df[['district', 'category', 'status', 'content']].to_string(index=False)
        prompt = f"""
Bạn là chuyên gia phân tích xã hội học và chính sách công của tỉnh Thanh Hóa.
Dưới đây là danh sách kiến nghị của cử tri:

{data_summary}

Thực hiện phân tích CHUYÊN SÂU theo 4 phần:

## I. ĐIỂM NÓNG (Hotspots)
Xác định địa phương và lĩnh vực nào đang có nhiều bức xúc nhất. Phân tích tương quan.

## II. ĐÁNH GIÁ RỦI RO
Những kiến nghị nào nếu không giải quyết kịp thời sẽ có nguy cơ: khiếu kiện đông người, bất ổn xã hội, ảnh hưởng đến uy tín chính quyền? Xếp hạng theo mức độ nguy hiểm.

## III. THAM MƯU CHÍNH SÁCH VĨ MÔ
Đề xuất cụ thể cho Thường trực HĐND tỉnh: điều chỉnh quy hoạch, phân bổ ngân sách, chính sách ưu tiên cần ban hành trong kỳ họp tiếp theo.

## IV. KIẾN NGHỊ GIÁM SÁT
Đề xuất đoàn giám sát chuyên đề hoặc chất vấn nào cần được ưu tiên trong kỳ họp tới.

Trả lời sắc bén, chuyên nghiệp, bằng ngôn ngữ hành chính nhà nước.
"""
        result = generate_text(prompt, use_pro=True)
        st.session_state.petition_ai_result = result

if "petition_ai_result" in st.session_state:
    st.markdown(st.session_state.petition_ai_result)

st.markdown("---")

# ─── DATA TABLE ───────────────────────────────────────────────────────────────
st.markdown("### 🔍 Danh sách Kiến nghị Chi tiết")

col_search, col_filter_cat, col_filter_status = st.columns([2, 1, 1])
with col_search:
    search = st.text_input("🔍 Tìm kiếm...", placeholder="Nhập tên, nội dung hoặc địa phương")
with col_filter_cat:
    cat_filter = st.selectbox("Lĩnh vực", ["Tất cả"] + sorted(df['category'].unique().tolist()))
with col_filter_status:
    status_filter = st.selectbox("Trạng thái", ["Tất cả", "Mới", "Đang xử lý", "Đã xong"])

filtered = df.copy()
if search:
    filtered = filtered[filtered.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
if cat_filter != "Tất cả":
    filtered = filtered[filtered['category'] == cat_filter]
if status_filter != "Tất cả":
    filtered = filtered[filtered['status'] == status_filter]

st.dataframe(
    filtered[["id", "created_at", "voter_name", "district", "category", "content", "status", "resolution"]],
    column_config={
        "id":          st.column_config.NumberColumn("ID", width="small"),
        "created_at":  st.column_config.TextColumn("Ngày tiếp nhận", width="small"),
        "voter_name":  st.column_config.TextColumn("Cử tri / Đơn vị"),
        "district":    st.column_config.TextColumn("Địa phương"),
        "category":    st.column_config.TextColumn("Lĩnh vực"),
        "content":     st.column_config.TextColumn("Nội dung kiến nghị", width="large"),
        "status":      st.column_config.TextColumn("Trạng thái"),
        "resolution":  st.column_config.TextColumn("Kết quả xử lý"),
    },
    use_container_width=True,
    hide_index=True
)

st.caption(f"Hiển thị {len(filtered)}/{total} kiến nghị")
