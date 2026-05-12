import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
print("Testing imports for app.py...")
try:
    import streamlit as st
    import app
    print("SUCCESS: app.py imported successfully.")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
