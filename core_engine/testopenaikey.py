from openai import OpenAI
import os

def test_openai_key():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ OPENAI_API_KEY tidak ditemukan di environment variable.")
        return

    try:
        client = OpenAI(api_key=api_key)
        response = client.models.list()

        print("✅ API Key Berfungsi!")
        print(f"Jumlah model terdeteksi: {len(response.data)}")

    except Exception as e:
        print("❌ API Key TIDAK valid atau ada masalah lain.")
        print("Error:", e)

if __name__ == "__main__":
    test_openai_key()
