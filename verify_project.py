import os
import sys
import subprocess
import json
from dotenv import load_dotenv

# Fix encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def log(msg):
    print(f"[VERIFY] {msg}")

def check_requirements_encoding():
    log("Checking requirements.txt encoding...")
    try:
        with open("requirements.txt", "rb") as f:
            content = f.read()
            if b"\x00" in content:
                log("DETECTED: UTF-16 or NULL characters in requirements.txt. Fixing...")
                # Try to decode and re-write as clean UTF-8
                text = content.replace(b"\x00", b"").decode("utf-8", errors="ignore")
                with open("requirements.txt", "w", encoding="utf-8") as f2:
                    f2.write(text)
                log("FIXED: requirements.txt is now clean UTF-8.")
            else:
                log("OK: requirements.txt encoding looks fine.")
    except Exception as e:
        log(f"ERROR checking encoding: {e}")

def check_dependencies():
    log("Checking dependencies...")
    needed = ["streamlit", "google-genai", "python-docx", "pypdf", "groq"]
    for pkg in needed:
        try:
            __import__(pkg.replace("-", "_"))
            log(f"OK: {pkg} is installed.")
        except ImportError:
            log(f"MISSING: {pkg}. Attempting to install...")
            subprocess.run([sys.executable, "-m", "pip", "install", pkg], check=True)
            log(f"FIXED: Installed {pkg}.")

def check_api_keys():
    log("Checking API Keys...")
    load_dotenv(override=True)
    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not gemini_key:
        log("WARNING: GEMINI_API_KEY not found in .env")
    else:
        log(f"OK: GEMINI_API_KEY found ({gemini_key[:5]}...)")

    if not groq_key:
        log("WARNING: GROQ_API_KEY not found in .env")
    else:
        log(f"OK: GROQ_API_KEY found ({groq_key[:5]}...)")

def test_connectivity():
    log("Testing AI Connectivity...")
    try:
        from utils.gemini_client import generate_text
        # Test Gemini
        log("Testing Gemini...")
        res_g = generate_text("Ping", provider="gemini", use_pro=False)
        if "❌" in res_g or "⚠️" in res_g:
            log(f"GEMINI FAILED: {res_g}")
        else:
            log("GEMINI SUCCESS!")
            
        # Test Groq
        log("Testing Groq...")
        res_gr = generate_text("Ping", provider="groq", use_pro=False)
        if "❌" in res_gr:
            log(f"GROQ FAILED: {res_gr}")
        else:
            log("GROQ SUCCESS!")
            

    except Exception as e:
        log(f"ERROR during connectivity test: {e}")

if __name__ == "__main__":
    check_requirements_encoding()
    check_dependencies()
    check_api_keys()
    test_connectivity()
    log("Verification Loop Completed.")
