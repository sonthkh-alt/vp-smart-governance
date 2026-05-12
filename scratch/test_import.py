import sys
import os

# Giả lập môi trường Streamlit
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
class MockSessionState(dict):
    def __getattr__(self, name):
        return self.get(name)
    def __setattr__(self, name, value):
        self[name] = value

import streamlit as st
st.session_state = MockSessionState()

try:
    from utils.auth_helper import require_auth
    print("SUCCESS: require_auth imported successfully.")
except ImportError as e:
    print(f"FAILED: ImportError: {e}")
except Exception as e:
    print(f"ERROR: {e}")
