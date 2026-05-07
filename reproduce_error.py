import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

system_instruction = """You are TravelX, an elite AI Travel Assistant...""" # truncated for brevity

prompt = "make a plan from jalandhar to surat for 4 days from tomorrow with 4 friends and budget is 14k"

try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[{"role": "user", "parts": [{"text": prompt}]}],
        config=genai.types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7
        )
    )
    print("Response text:", response.text)
    print("Candidates:", response.candidates)
except Exception as e:
    print("Error:", str(e))
