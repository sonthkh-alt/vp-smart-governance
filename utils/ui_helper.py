import streamlit as st
from .auth_helper import init_auth, check_auth_status, get_user_info, login_google, logout

def set_premium_css():
    """
    Thiết lập giao diện Premium cho toàn bộ ứng dụng.
    Sử dụng font Inter, Glassmorphism và các hiệu ứng mượt mà.
    """
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        /* Root variables */
        :root {
            --primary-blue: #1D3557;
            --secondary-blue: #457B9D;
            --light-blue: #A8DADC;
            --accent-color: #E63946;
            --bg-dark: #0F172A;
            --bg-darker: #020617;
            --glass-bg: rgba(255, 255, 255, 0.03);
            --glass-border: rgba(255, 255, 255, 0.1);
            --card-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            --text-white: #F8FAFC;
        }

        /* Full App Background */
        .stApp {
            background-color: var(--bg-dark);
            color: var(--text-white);
        }

        /* Typography */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Global Text Color Force */
        h1, h2, h3, p, span, label, .stMarkdown {
            color: var(--text-white) !important;
        }

        /* Glassmorphism Cards - Enhanced for Dark Mode */
        .glass-card {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 20px;
            border: 1px solid var(--glass-border);
            padding: 2rem;
            box-shadow: var(--card-shadow);
            margin-bottom: 1.5rem;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .glass-card h3 {
            color: var(--light-blue) !important;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .glass-card p {
            color: #94A3B8 !important; /* Slightly dimmed for hierarchy */
            font-size: 0.95rem;
            line-height: 1.6;
        }

        .glass-card:hover {
            transform: translateY(-8px);
            border: 1px solid var(--secondary-blue);
            background: rgba(30, 41, 59, 0.9);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }

        /* Premium Buttons */
        .stButton button {
            background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
            color: white !important;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .stButton button:hover {
            transform: scale(1.02);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
            opacity: 0.95;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: var(--bg-darker) !important;
            border-right: 1px solid var(--glass-border);
        }

        /* Hero Header */
        .hero-section {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border: 1px solid var(--glass-border);
            padding: 5rem 2rem;
            border-radius: 24px;
            text-align: center;
            color: white !important;
            margin-bottom: 3.5rem;
            box-shadow: var(--card-shadow);
            position: relative;
            overflow: hidden;
        }

        .hero-section::before {
            content: "";
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: rotate 20s linear infinite;
        }

        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .hero-title {
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1rem;
            letter-spacing: -1px;
        }

        .hero-subtitle {
            font-size: 1.2rem;
            font-weight: 300;
            opacity: 0.9;
        }

        /* Metric Styling */
        [data-testid="stMetricValue"] {
            font-size: 2.5rem;
            font-weight: 700;
            color: #60A5FA !important;
        }

        [data-testid="stMetricDelta"] {
            color: #94A3B8 !important;
        }

        [data-testid="stMetricLabel"] {
            color: var(--text-white) !important;
        }
        
        /* Sidebar items styling */
        .sidebar-content {
            padding: 1rem;
        }
        
        /* Input & Widget Styling */
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        .stSelectbox [data-baseweb="select"] {
            color: var(--text-white) !important;
            background-color: rgba(30, 41, 59, 0.5) !important;
            border-color: var(--glass-border) !important;
        }

        /* Progress bar */
        .stProgress > div > div {
            background-color: #2563EB !important;
        }

        /* Expander */
        .streamlit-expanderHeader {
            color: var(--text-white) !important;
        }

        /* Info/Success/Warning/Error boxes */
        .stAlert {
            border-radius: 12px;
        }
        /* Custom Sidebar Branding: Rename 'app' to 'SonHa' */
        [data-testid="stSidebarNav"] > div:first-child > span,
        [data-testid="stSidebarNav"] li:first-child a span {
            visibility: hidden;
            position: relative;
            display: inline-block;
            width: 100%;
        }
        [data-testid="stSidebarNav"] > div:first-child > span::after,
        [data-testid="stSidebarNav"] li:first-child a span::after {
            content: "SonHa";
            visibility: visible;
            position: absolute;
            left: 0;
            top: 0;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-white);
            white-space: nowrap;
        }
        </style>
    """, unsafe_allow_html=True)

def draw_module_header(title, icon, description):
    """
    Vẽ header cao cấp cho mỗi phân hệ.
    """
    st.markdown(f"""
        <div class="hero-section">
            <div style="font-size: 4rem; margin-bottom: 1rem;">{icon}</div>
            <h1 class="hero-title">{title}</h1>
            <p class="hero-subtitle">{description}</p>
        </div>
    """, unsafe_allow_html=True)

def draw_glass_card(title, content, icon=None):
    """
    Vẽ một card kiểu glassmorphism.
    """
    icon_html = f"<div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>{icon}</div>" if icon else ""
    st.markdown(f"""
        <div class="glass-card">
            {icon_html}
            <h3 style="margin-top: 0; color: var(--secondary-blue);">{title}</h3>
            <div>{content}</div>
        </div>
    """, unsafe_allow_html=True)

def draw_sidebar():
    """
    Vẽ sidebar chung cho toàn bộ ứng dụng, bao gồm các link điều hướng ngoài.
    """
    # Khởi tạo trạng thái Auth
    init_auth()
    is_logged_in = check_auth_status()
    user = get_user_info()

    with st.sidebar:
        st.markdown("### 🌐 Kết nối Hệ thống")
        st.page_link("https://hdnd.vercel.app/", label="Cổng thông tin HĐND", icon="🌍")
        st.markdown("---")
        
        st.markdown("### 🛠️ Cài đặt & Hỗ trợ")
        st.info("Phiên bản v2.1 - Python 3.14 Compatible")
        st.markdown("---")

        # ─── PHẦN ĐĂNG NHẬP (BOTTOM) ──────────────────────────────────────────
        if not is_logged_in:
            st.markdown("### 🔐 Tài khoản")
            st.button("🔑 Đăng nhập với Google", on_click=login_google, use_container_width=True)
            st.caption("Sử dụng bất kỳ tài khoản Google nào để truy cập AI.")
        else:
            import database
            db_user = database.get_user(user["email"])
            
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(user["picture"], width=45)
            with col2:
                st.markdown(f"**{user['name']}**")
                st.caption(user["email"])
            
            if db_user:
                if not db_user["is_admin"]:
                    status = "✅ Đã duyệt" if db_user["is_approved"] else "⏳ Chờ duyệt"
                    color = "green" if db_user["credits"] > 0 else "red"
                    st.markdown(f"**Trạng thái:** {status}")
                    st.markdown(f"**Lượt AI:** :{color}[{db_user['credits']} lượt]")
            
            if st.button("🚪 Đăng xuất", use_container_width=True):
                logout()
        
        st.markdown("---")

        # Thông tin tác giả - Đặt ở dưới cùng
        st.markdown(f"""
            <a href="https://sites.google.com/view/sonthkh/home" target="_blank" style="text-decoration: none;">
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease; cursor: pointer;" onmouseover="this.style.background='rgba(255,255,255,0.1)'" onmouseout="this.style.background='rgba(255,255,255,0.05)'">
                    <div style="font-size: 0.7rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Quản trị hệ thống</div>
                    <div style="font-weight: 700; color: #60A5FA; font-size: 1rem;">Hà Ngọc Sơn</div>
                    <div style="font-size: 0.8rem; color: #94A3B8; line-height: 1.2;">Phó Chánh Văn phòng Đoàn ĐBQH và HĐND tỉnh Thanh Hóa</div>
                </div>
            </a>
        """, unsafe_allow_html=True)
