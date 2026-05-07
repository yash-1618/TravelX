import os
from google import genai
import dotenv

dotenv.load_dotenv(".env")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

contents = [{"role": "user", "parts": [{"text": "Hello, this is a test"}]}]

try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents
    )
    print("Success:", response.text)
except Exception as e:
    print("Error:", str(e))
