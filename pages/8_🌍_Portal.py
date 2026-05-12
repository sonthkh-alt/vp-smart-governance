import streamlit as st
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.ui_helper import set_premium_css

# Áp dụng giao diện
set_premium_css()

# Hiển thị iframe full màn hình
# Lưu ý: Một số trang web chặn hiển thị trong iframe (X-Frame-Options: SAMEORIGIN).
# Nếu trang vercel này cho phép, nó sẽ hiển thị bình thường.
st.components.v1.iframe("https://hdnd.vercel.app/", height=800, scrolling=True)
