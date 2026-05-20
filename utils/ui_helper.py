import streamlit as st


def set_premium_css():
    """
    Thiết lập giao diện Premium cho toàn bộ ứng dụng.
    Sử dụng font Inter, Glassmorphism và các hiệu ứng mượt mà.
    """
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

        /* Root variables - Sophisticated iOS Indigo/Violet Palette */
        :root {
            --primary-ios: #6366F1;
            --primary-light: #818CF8;
            --accent-ios: #EC4899;
            --accent-violet: #8B5CF6;
            --bg-dark: #090D1A;
            --bg-card: rgba(17, 24, 39, 0.7);
            --bg-card-hover: rgba(31, 41, 55, 0.85);
            --glass-border: rgba(255, 255, 255, 0.08);
            --glass-border-hover: rgba(99, 102, 241, 0.4);
            --card-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5);
            --text-main: #F9FAFB;
            --text-mute: #9CA3AF;
        }

        /* Safe area inserts for iOS notches */
        body {
            padding-top: env(safe-area-inset-top);
            padding-bottom: env(safe-area-inset-bottom);
            padding-left: env(safe-area-inset-left);
            padding-right: env(safe-area-inset-right);
        }

        /* Full App Background with Animated Mesh Gradient */
        .stApp {
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.15) 0px, transparent 50%),
                radial-gradient(at 50% 100%, rgba(236, 72, 153, 0.08) 0px, transparent 50%);
            background-attachment: fixed;
            color: var(--text-main);
        }

        /* Typography - Native iOS Feel */
        html, body, [class*="css"], .stMarkdown, p, span, label, li {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Plus Jakarta Sans", sans-serif !important;
            -webkit-font-smoothing: antialiased;
        }

        /* Global Header force styling */
        h1, h2, h3, h4, h5, h6 {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Plus Jakarta Sans", sans-serif !important;
            color: var(--text-main) !important;
            font-weight: 700 !important;
            letter-spacing: -0.025em !important;
        }

        /* Responsive Columns Hack for iPhone/Mobile Portrait screen */
        @media (max-width: 768px) {
            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
                padding-left: 0px !important;
                padding-right: 0px !important;
                margin-bottom: 12px !important;
            }
            div[data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
                gap: 0px !important;
            }
            /* Reduce page padding on mobile */
            .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-top: 2rem !important;
                padding-bottom: 2rem !important;
            }
            /* Scale headers for iPhone screens */
            h1 { font-size: 1.8rem !important; }
            h2 { font-size: 1.4rem !important; }
            h3 { font-size: 1.2rem !important; }
            
            /* Compact metrics for mobile */
            div[data-testid="metric-container"] {
                padding: 10px !important;
            }
            div[data-testid="stMetricValue"] {
                font-size: 1.8rem !important;
            }
        }

        /* High-End Glassmorphism Cards */
        .glass-card {
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid var(--glass-border);
            padding: 1.5rem;
            box-shadow: var(--card-shadow);
            margin-bottom: 1.2rem;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            overflow: hidden;
            animation: fadeInUp 0.6s ease-out;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(15px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .glass-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, rgba(255,255,255,0.15), rgba(255,255,255,0.02));
            z-index: 1;
        }
        
        .glass-card h3 {
            color: var(--primary-light) !important;
            font-weight: 700;
            font-size: 1.35rem;
            margin-top: 0;
            margin-bottom: 0.75rem;
        }

        .glass-card p {
            color: var(--text-mute) !important;
            font-size: 0.9rem;
            line-height: 1.5;
            margin-bottom: 0;
        }

        .glass-card:hover {
            transform: translateY(-5px);
            border-color: var(--glass-border-hover);
            background: var(--bg-card-hover);
            box-shadow: 0 20px 40px rgba(99, 102, 241, 0.15);
        }

        /* Premium iOS-Native Touch Buttons */
        .stButton button {
            background: linear-gradient(135deg, var(--primary-ios) 0%, var(--accent-violet) 100%) !important;
            color: white !important;
            border: none !important;
            padding: 0.65rem 1.5rem !important;
            border-radius: 14px !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.3px !important;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
            min-height: 46px !important; /* Touch target Apple HIG */
            width: 100% !important; /* Full width for easy tapping on iPhone */
        }

        .stButton button:hover {
            transform: scale(1.02) translateY(-1px) !important;
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.45) !important;
            opacity: 0.98 !important;
        }

        .stButton button:active {
            transform: scale(0.98) !important;
        }
        
        /* Secondary / Link buttons styling */
        .stDownloadButton button {
            background: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid var(--glass-border) !important;
            color: var(--text-main) !important;
            border-radius: 14px !important;
            min-height: 46px !important;
            width: 100% !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }
        .stDownloadButton button:hover {
            background: rgba(255, 255, 255, 0.15) !important;
            border-color: rgba(255, 255, 255, 0.3) !important;
        }

        /* Sidebar Styling for iOS overlay feel */
        [data-testid="stSidebar"] {
            background-color: #05070F !important;
            border-right: 1px solid var(--glass-border);
        }

        /* Hero Header iOS Design */
        .hero-section {
            background: linear-gradient(135deg, rgba(17, 24, 39, 0.8) 0%, rgba(9, 13, 26, 0.95) 100%);
            border: 1px solid var(--glass-border);
            padding: 2.5rem 1.5rem;
            border-radius: 24px;
            text-align: center;
            color: white !important;
            margin-bottom: 2rem;
            box-shadow: var(--card-shadow);
            position: relative;
            overflow: hidden;
            animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .hero-section::after {
            content: "";
            position: absolute;
            top: -20%;
            left: -20%;
            width: 140%;
            height: 140%;
            background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 60%);
            pointer-events: none;
        }

        .hero-title {
            font-size: 1.8rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            letter-spacing: -0.03em;
            background: linear-gradient(135deg, #FFFFFF 30%, #C7D2FE 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero-subtitle {
            font-size: 0.95rem;
            font-weight: 400;
            color: var(--text-mute);
            line-height: 1.4;
        }

        /* Premium Metric Cards */
        [data-testid="metric-container"] {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid var(--glass-border) !important;
            border-radius: 16px !important;
            padding: 12px 16px !important;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-light) !important;
            letter-spacing: -0.03em;
        }

        [data-testid="stMetricDelta"] {
            color: var(--accent-ios) !important;
            font-size: 0.85rem !important;
        }

        [data-testid="stMetricLabel"] {
            color: var(--text-mute) !important;
            font-size: 0.85rem !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Form Inputs on iOS: Focus colors, rounded corners */
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        .stSelectbox [data-baseweb="select"] {
            color: var(--text-main) !important;
            background-color: rgba(17, 24, 39, 0.6) !important;
            border: 1px solid var(--glass-border) !important;
            border-radius: 12px !important;
            padding: 10px 14px !important;
            font-size: 0.95rem !important;
            transition: all 0.3s ease !important;
        }

        [data-testid="stTextInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: var(--primary-ios) !important;
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25) !important;
        }

        /* Premium Tabs Styling for iOS Segmented Control look */
        .stTabs [data-baseweb="tab-list"] {
            background-color: rgba(17, 24, 39, 0.8) !important;
            padding: 4px !important;
            border-radius: 14px !important;
            border: 1px solid var(--glass-border) !important;
            display: flex !important;
            justify-content: space-around !important;
            margin-bottom: 1.5rem !important;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: transparent !important;
            color: var(--text-mute) !important;
            border: none !important;
            padding: 8px 12px !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            border-radius: 10px !important;
            transition: all 0.2s ease !important;
            flex-grow: 1 !important;
            text-align: center !important;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: rgba(255, 255, 255, 0.08) !important;
            color: var(--primary-light) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
        }

        /* Table Responsive Styling */
        div[data-testid="stTable"] {
            background: rgba(17, 24, 39, 0.5) !important;
            border: 1px solid var(--glass-border) !important;
            border-radius: 12px !important;
            overflow-x: auto !important;
        }

        /* Streamlit info boxes */
        .stAlert {
            border: 1px solid var(--glass-border) !important;
            border-radius: 14px !important;
            background-color: rgba(99, 102, 241, 0.05) !important;
        }
        
        /* Scrollbar styles */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    if st.session_state.get("show_login", False):
        from utils.auth_helper import login_google
        login_google()

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
            <h3 style="margin-top: 0; color: var(--primary-light);">{title}</h3>
            <div>{content}</div>
        </div>
    """, unsafe_allow_html=True)

def draw_sidebar():
    """
    Vẽ sidebar chung cho toàn bộ ứng dụng, bao gồm các link điều hướng ngoài.
    """
    # Khởi tạo trạng thái Auth
    from utils.auth_helper import init_auth, check_auth_status, get_user_info
    init_auth()
    is_logged_in = check_auth_status()
    user = get_user_info()

    with st.sidebar:

        # ─── PHẦN ĐĂNG NHẬP (BOTTOM) ──────────────────────────────────────────
        if not is_logged_in:
            st.markdown("### 🔐 Tài khoản")
            from utils.auth_helper import render_login_button
            render_login_button(sidebar=True)
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
                from utils.auth_helper import logout
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
