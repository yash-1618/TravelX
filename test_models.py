from google import genai
from dotenv import dotenv_values
import time

env_vars = dotenv_values(".env")
client = genai.Client(api_key=env_vars.get("GEMINI_API_KEY"))

models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.5-flash-lite']

for m in models:
    print(f"Testing {m}...")
    start = time.time()
    try:
        response = client.models.generate_content(
            model=m,
            contents="hello"
        )
        print(f"  Success in {time.time() - start:.2f}s: {response.text[:20]}")
    except Exception as e:
        print(f"  Error in {time.time() - start:.2f}s: {e}")
