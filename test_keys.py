import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

keys = [
    os.environ.get("GEMINI_API_KEY"),
    os.environ.get("GEMINI_API_KEY_ALT"),
    os.environ.get("GEMINI_API_KEY_ALT_2")
]

for i, key in enumerate(keys):
    print(f"Testing Key {i+1}: {key[:10]}...")
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Hello'
        )
        print("Success!")
    except Exception as e:
        print(f"Failed with error type: {type(e)}")
        print(f"Error message: {e}")
        print(f"Error message lower: {str(e).lower()}")
