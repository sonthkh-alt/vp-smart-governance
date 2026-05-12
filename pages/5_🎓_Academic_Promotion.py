"""
5_🎓_Academic_Promotion.py — Học thuật & Nâng hạng PGS
Lộ trình 6 năm đạt chức danh Phó Giáo sư theo QĐ 37/2018/QĐ-TTg.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.ui_helper import set_premium_css, draw_module_header, draw_sidebar
from utils.gemini_client import generate_text
from utils.auth_helper import require_auth
import database

st.set_page_config(page_title="Học thuật & Nâng hạng", page_icon="🎓", layout="wide")

# Áp dụng giao diện Premium & Sidebar
set_premium_css()
draw_sidebar()

draw_module_header("Academic Promotion Roadmap", "🎓",
    "Lộ trình cá nhân hóa đạt chức danh Phó Giáo sư — Theo QĐ 37/2018/QĐ-TTg")

# ─── Tiêu chuẩn PGS (QĐ 37/2018) ────────────────────────────────────────────
PGS_REQUIREMENTS = {
    "min_articles": 3,        # Tối thiểu 3 bài báo tác giả chính (sau TS)
    "min_points": 6.0,        # Tối thiểu 6 điểm công trình (ngành KHXH)
    "min_teaching_hours": 600, # Giờ giảng quy chuẩn
    "min_supervised_masters": 2,
    "min_research_projects": 1, # Ít nhất 1 đề tài NCKH cấp cơ sở trở lên
    "min_years_after_phd": 3,
}

# ─── SIDEBAR: Hồ sơ Học thuật ─────────────────────────────────────────────────
profile = database.get_academic_profile()

with st.sidebar:
    st.markdown("### 👤 Hồ sơ Học thuật")
    with st.form("profile_form"):
        full_name = st.text_input("Họ và tên", value=profile.get("full_name", ""))
        current_title = st.selectbox("Học vị hiện tại",
            ["Thạc sĩ", "Tiến sĩ", "Tiến sĩ Khoa học"],
            index=["Thạc sĩ", "Tiến sĩ", "Tiến sĩ Khoa học"].index(profile.get("current_title", "Tiến sĩ")))
        field = st.text_input("Ngành", value=profile.get("field", "Luật học"))
        sub_field = st.text_input("Chuyên ngành", value=profile.get("sub_field", "Luật Hiến pháp & Hành chính"))
        institution = st.text_input("Cơ sở đào tạo", value=profile.get("institution", ""))
        phd_year = st.number_input("Năm nhận bằng TS", min_value=2000, max_value=2030,
                                    value=profile.get("phd_year", 2024))
        target_year = st.number_input("Năm mục tiêu PGS", min_value=2027, max_value=2040,
                                       value=profile.get("target_year", 2032))

        st.markdown("---")
        st.markdown("#### 📊 Thành tích hiện tại")
        teaching_hours = st.number_input("Giờ giảng tích lũy", min_value=0, value=profile.get("teaching_hours", 0))
        supervised_masters = st.number_input("Số ThS đã hướng dẫn", min_value=0, value=profile.get("supervised_masters", 0))
        supervised_phds = st.number_input("Số NCS đang/đã hướng dẫn", min_value=0, value=profile.get("supervised_phds", 0))
        rp_national = st.number_input("Đề tài NCKH cấp Bộ/Tỉnh+", min_value=0, value=profile.get("research_projects_national", 0))
        rp_local = st.number_input("Đề tài NCKH cấp cơ sở", min_value=0, value=profile.get("research_projects_local", 0))
        foreign_lang = st.text_input("Ngoại ngữ (VD: IELTS 6.0)", value=profile.get("foreign_language", ""))

        if st.form_submit_button("💾 Lưu Hồ sơ", use_container_width=True):
            database.save_academic_profile({
                "full_name": full_name, "current_title": current_title,
                "field": field, "sub_field": sub_field, "institution": institution,
                "phd_year": phd_year, "target_year": target_year,
                "teaching_hours": teaching_hours, "supervised_masters": supervised_masters,
                "supervised_phds": supervised_phds, "research_projects_national": rp_national,
                "research_projects_local": rp_local, "foreign_language": foreign_lang,
            })
            st.success("✅ Đã lưu!")
            st.rerun()

    st.markdown("---")
    st.markdown("### 📝 Thêm Công trình Khoa học")
    with st.form("pub_form", clear_on_submit=True):
        pub_title = st.text_input("Tên công trình")
        pub_type = st.selectbox("Loại", ["Bài báo khoa học", "Sách chuyên khảo", "Giáo trình", "Bài hội thảo quốc tế", "Bài hội thảo trong nước", "Đề tài NCKH"])
        journal = st.text_input("Tạp chí / NXB / Hội thảo")
        pub_year = st.number_input("Năm", min_value=2015, max_value=2040, value=2026)
        is_isi = st.checkbox("ISI / Scopus")
        is_first = st.checkbox("Tác giả chính / Tác giả liên hệ")
        points = st.number_input("Điểm quy đổi (theo HĐGSNN)", min_value=0.0, max_value=3.0, value=0.5, step=0.25)
        if st.form_submit_button("➕ Thêm công trình", use_container_width=True):
            if pub_title.strip():
                database.save_publication({
                    "title": pub_title, "pub_type": pub_type, "journal_name": journal,
                    "year": pub_year, "is_isi_scopus": is_isi, "is_first_author": is_first, "points": points,
                })
                st.success("✅ Đã thêm!")
                st.rerun()

# ─── Load data ────────────────────────────────────────────────────────────────
profile = database.get_academic_profile()
pubs_raw = database.get_publications()
pubs_df = pd.DataFrame(pubs_raw, columns=["id","title","pub_type","journal_name","year","is_isi_scopus","is_first_author","points","doi","notes","created_at"]) if pubs_raw else pd.DataFrame()

# ─── KPI DASHBOARD ────────────────────────────────────────────────────────────
total_points = pubs_df["points"].sum() if not pubs_df.empty else 0
total_articles = len(pubs_df[pubs_df["pub_type"] == "Bài báo khoa học"]) if not pubs_df.empty else 0
first_author_articles = len(pubs_df[(pubs_df["pub_type"] == "Bài báo khoa học") & (pubs_df["is_first_author"] == 1)]) if not pubs_df.empty else 0
isi_count = len(pubs_df[pubs_df["is_isi_scopus"] == 1]) if not pubs_df.empty else 0
teaching = profile.get("teaching_hours", 0)
masters = profile.get("supervised_masters", 0)
projects = profile.get("research_projects_national", 0) + profile.get("research_projects_local", 0)
target_yr = profile.get("target_year", 2032)
years_left = max(0, target_yr - 2026)

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("📄 Tổng công trình", len(pubs_df) if not pubs_df.empty else 0)
k2.metric("⭐ Điểm quy đổi", f"{total_points:.1f}", delta=f"/{PGS_REQUIREMENTS['min_points']:.0f} cần")
k3.metric("📰 Bài báo (tác giả chính)", first_author_articles, delta=f"/{PGS_REQUIREMENTS['min_articles']} cần")
k4.metric("🌐 ISI/Scopus", isi_count)
k5.metric("🎤 Giờ giảng", teaching, delta=f"/{PGS_REQUIREMENTS['min_teaching_hours']} cần")
k6.metric("⏰ Còn lại", f"{years_left} năm", delta=f"Mục tiêu: {target_yr}")

# Progress bars
st.markdown("---")
st.markdown("### 📊 Tiến độ đạt Tiêu chuẩn PGS (QĐ 37/2018)")

def safe_progress(current, target, label):
    pct = min(current / target, 1.0) if target > 0 else 0
    color = "✅" if pct >= 1.0 else "⏳"
    st.progress(pct, text=f"{color} **{label}**: {current}/{target} ({int(pct*100)}%)")

col_p1, col_p2 = st.columns(2)
with col_p1:
    safe_progress(total_points, PGS_REQUIREMENTS["min_points"], "Điểm công trình quy đổi")
    safe_progress(first_author_articles, PGS_REQUIREMENTS["min_articles"], "Bài báo tác giả chính")
    safe_progress(teaching, PGS_REQUIREMENTS["min_teaching_hours"], "Giờ giảng quy chuẩn")
with col_p2:
    safe_progress(masters, PGS_REQUIREMENTS["min_supervised_masters"], "Hướng dẫn ThS bảo vệ thành công")
    safe_progress(projects, PGS_REQUIREMENTS["min_research_projects"], "Đề tài NCKH")
    yr_after_phd = 2026 - profile.get("phd_year", 2024)
    safe_progress(yr_after_phd, PGS_REQUIREMENTS["min_years_after_phd"], "Năm sau khi nhận TS")

# ─── RADAR CHART ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🕸️ Biểu đồ Năng lực Tổng hợp")

categories = ["Điểm CT", "Bài báo", "ISI/Scopus", "Giờ giảng", "Hướng dẫn ThS", "Đề tài NCKH"]
actual = [
    min(total_points / PGS_REQUIREMENTS["min_points"], 1.5) * 100,
    min(first_author_articles / PGS_REQUIREMENTS["min_articles"], 1.5) * 100,
    min(isi_count / 2, 1.5) * 100,  # 2 ISI = excellent
    min(teaching / PGS_REQUIREMENTS["min_teaching_hours"], 1.5) * 100,
    min(masters / PGS_REQUIREMENTS["min_supervised_masters"], 1.5) * 100,
    min(projects / PGS_REQUIREMENTS["min_research_projects"], 1.5) * 100,
]
target_vals = [100]*6

fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(r=target_vals, theta=categories, fill='toself', name='Yêu cầu PGS', line_color='#EF4444', opacity=0.3))
fig_radar.add_trace(go.Scatterpolar(r=actual, theta=categories, fill='toself', name='Hiện tại của bạn', line_color='#3B82F6'))
fig_radar.update_layout(
    polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(visible=True, range=[0, 150], gridcolor='rgba(255,255,255,0.1)')),
    paper_bgcolor='rgba(0,0,0,0)', font_color='white', showlegend=True, margin=dict(t=30, b=30)
)
st.plotly_chart(fig_radar, use_container_width=True)

# ─── LỘ TRÌNH 6 NĂM ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🗺️ Lộ trình 6 Năm Chiến lược")

if st.button("🧠 AI TẠO LỘ TRÌNH CÁ NHÂN HÓA", type="primary"):
    if require_auth("Tạo lộ trình cá nhân hóa"):
        with st.spinner("AI đang phân tích hồ sơ và thiết kế lộ trình chiến lược..."):
            profile_summary = f"""
Họ tên: {profile.get('full_name', 'Chưa cập nhật')}
Học vị: {profile.get('current_title', 'Tiến sĩ')}
Ngành: {profile.get('field', '')} — Chuyên ngành: {profile.get('sub_field', '')}
Cơ sở: {profile.get('institution', '')}
Năm nhận TS: {profile.get('phd_year', 2024)}
Mục tiêu PGS: {target_yr}
Giờ giảng hiện tại: {teaching}/{PGS_REQUIREMENTS['min_teaching_hours']}
Bài báo tác giả chính: {first_author_articles}/{PGS_REQUIREMENTS['min_articles']}
Bài ISI/Scopus: {isi_count}
Điểm công trình: {total_points}/{PGS_REQUIREMENTS['min_points']}
Hướng dẫn ThS: {masters}/{PGS_REQUIREMENTS['min_supervised_masters']}
Đề tài NCKH: {projects}/{PGS_REQUIREMENTS['min_research_projects']}
Ngoại ngữ: {profile.get('foreign_language', 'Chưa cập nhật')}
"""
            prompt = f"""
Bạn là chuyên gia tư vấn học thuật cấp cao, am hiểu sâu sắc quy trình xét PGS tại Việt Nam (QĐ 37/2018/QĐ-TTg).

HỒ SƠ ỨNG VIÊN:
{profile_summary}

Hãy thiết kế LỘ TRÌNH CHIẾN LƯỢC {years_left} NĂM (từ 2026 đến {target_yr}) để ứng viên đạt đủ tiêu chuẩn PGS. Chia theo từng năm:

Với MỖI NĂM, hãy đề xuất:
## Năm [X] (20XX) — [Chủ đề chiến lược]
### Nghiên cứu & Công bố
- Số bài báo cần viết, tạp chí mục tiêu (gợi ý tạp chí cụ thể trong ngành {profile.get('field', '')})
- Hội thảo quốc tế nên tham gia
### Giảng dạy
- Số giờ cần tích lũy thêm, cách mở rộng (thỉnh giảng, sau đại học)
### Đề tài & Hướng dẫn
- Đề tài NCKH nên đăng ký (cấp nào, chủ đề gợi ý)
- Chiến lược nhận hướng dẫn ThS/NCS
### Sách & Giáo trình
- Kế hoạch viết sách chuyên khảo hoặc giáo trình
### Ngoại ngữ & Kỹ năng bổ trợ
- Mục tiêu ngoại ngữ, kỹ năng mềm

Cuối cùng: Đưa ra **3 RỦI RO LỚN NHẤT** và cách phòng tránh.

Trình bày chuyên nghiệp, chi tiết, thực tế.
"""
            result = generate_text(prompt, use_pro=True)
            st.session_state.roadmap_result = result

if "roadmap_result" in st.session_state:
    st.markdown(st.session_state.roadmap_result)

# ─── DANH MỤC CÔNG TRÌNH ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📚 Danh mục Công trình Khoa học")

if not pubs_df.empty:
    display_df = pubs_df[["id", "year", "title", "pub_type", "journal_name", "is_isi_scopus", "is_first_author", "points"]].copy()
    display_df["is_isi_scopus"] = display_df["is_isi_scopus"].map({1: "✅", 0: ""})
    display_df["is_first_author"] = display_df["is_first_author"].map({1: "✅", 0: ""})
    st.dataframe(
        display_df, hide_index=True, use_container_width=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "year": st.column_config.NumberColumn("Năm", format="%d"),
            "title": st.column_config.TextColumn("Tên công trình", width="large"),
            "pub_type": st.column_config.TextColumn("Loại"),
            "journal_name": st.column_config.TextColumn("Tạp chí / NXB"),
            "is_isi_scopus": st.column_config.TextColumn("ISI/Scopus", width="small"),
            "is_first_author": st.column_config.TextColumn("Tác giả chính", width="small"),
            "points": st.column_config.NumberColumn("Điểm", format="%.2f"),
        }
    )
    st.caption(f"Tổng: {len(display_df)} công trình · {total_points:.1f} điểm quy đổi · {isi_count} ISI/Scopus")
else:
    st.info("Chưa có công trình nào. Hãy thêm công trình từ thanh bên trái.")

# ─── AI GỢI Ý ĐỀ TÀI ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 💡 Trợ lý AI — Gợi ý Đề tài & Chiến lược Công bố")

topic_prompt = st.text_input("Nhập lĩnh vực quan tâm (hoặc để trống để AI tự gợi ý):",
    placeholder="VD: Quản trị công, Pháp luật về quyền con người, Kinh tế biển...")

if st.button("🔍 GỢI Ý ĐỀ TÀI NGHIÊN CỨU", type="primary"):
    if require_auth("Gợi ý đề tài nghiên cứu"):
        with st.spinner("AI đang phân tích xu hướng nghiên cứu..."):
            field_info = profile.get("field", "Luật học") if profile else "Khoa học xã hội"
            sub_info = profile.get("sub_field", "") if profile else ""
            user_topic = topic_prompt if topic_prompt.strip() else f"{field_info} - {sub_info}"
            prompt = f"""
Bạn là cố vấn học thuật cấp cao. Ứng viên PGS ngành {field_info}, chuyên ngành {sub_info}.

Hãy đề xuất 5 ĐỀ TÀI NGHIÊN CỨU tiềm năng trong lĩnh vực: {user_topic}

Với mỗi đề tài:
1. **Tên đề tài** (tiếng Việt + tiếng Anh)
2. **Tính cấp thiết**: Vì sao đề tài này đang "nóng" trong học thuật
3. **Khả năng công bố**: Gợi ý 2-3 tạp chí phù hợp (ưu tiên ISI/Scopus nếu có)
4. **Phương pháp nghiên cứu** gợi ý
5. **Ước tính thời gian** hoàn thành

Ưu tiên đề tài có tính liên ngành, có thể gắn với thực tiễn quản trị nhà nước tại Việt Nam.
"""
            result = generate_text(prompt, use_pro=True)
            st.session_state.topic_suggestions = result

if "topic_suggestions" in st.session_state:
    st.markdown(st.session_state.topic_suggestions)
