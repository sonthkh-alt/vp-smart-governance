import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.gemini_client import generate_text
import unittest
from unittest.mock import patch

class TestFallback(unittest.TestCase):
    @patch('utils.gemini_client._call_groq')
    @patch('utils.gemini_client._call_gemini_with_fallback')
    def test_groq_fallback_to_gemini(self, mock_gemini, mock_groq):
        # Giả lập Groq bị giới hạn (Rate Limit)
        mock_groq.return_value = "❌ Lỗi Groq API: Rate limit reached (429)"
        mock_gemini.return_value = "Đây là câu trả lời từ Gemini (Fallback)"
        
        # Gọi hàm với provider mặc định là groq
        result = generate_text("Ping")
        
        # Kiểm tra xem có gọi Gemini không
        mock_gemini.assert_called_once()
        self.assertEqual(result, "Đây là câu trả lời từ Gemini (Fallback)")
        print("✅ Test Fallback thành công!")

if __name__ == "__main__":
    unittest.main()
