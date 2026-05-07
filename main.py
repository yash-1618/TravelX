import sqlite3
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from google import genai
import os
from dotenv import load_dotenv
import requests
import datetime
import traceback
import uuid
import json
import concurrent.futures
try:
    from duckduckgo_search import DDGS
except ImportError:
    pass
load_dotenv(override=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
DB_PATH = "chat_history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT,
                  role TEXT,
                  content TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

system_instruction = """You are TravelX, an elite AI Travel Assistant and Full Stack Travel Planner.
You act like a highly empathetic, premium travel concierge (similar to a mix of ChatGPT, Booking.com, and MakeMyTrip).
Your goal is to help users plan trips, check hotels, trains, buses, restaurants, budgets, and travel recommendations.

IMPORTANT: You MUST return your ENTIRE response as a SINGLE, VALID JSON object. Do NOT include any markdown formatting like ```json or anything else. Just the raw JSON.

The JSON MUST follow this exact schema:
{
  "summary": "A friendly conversational summary of what you found. Tell them to check the right sidebar for details.",
  "widgets": [
    {
      "type": "OVERVIEW",
      "data": {
        "title": "City Name",
        "description": "Why it is famous (2-3 sentences)",
        "best_time": "Best Time To Visit",
        "duration": "Ideal Duration",
        "image_query": "City Name famous landmark HD"
      }
    },
    {
      "type": "BUDGET",
      "data": {
        "total": "Total Amount (₹)",
        "hotel": "Hotel Cost (₹)",
        "food": "Food Cost (₹)",
        "transport": "Transport Cost (₹)",
        "misc": "Misc Cost (₹)"
      }
    },
    {
      "type": "HOTEL",
      "data": {
        "name": "Hotel Name",
        "location": "Location",
        "price": "Price Per Night (₹)",
        "rating": "Rating (e.g., 4.5)",
        "amenities": "WiFi, Pool",
        "description": "Short Description",
        "image_query": "Hotel Name Location exterior HD"
      }
    },
    {
      "type": "FOOD",
      "data": {
        "name": "Restaurant Name",
        "cuisine": "Cuisine Type",
        "price": "Price Estimate (₹)",
        "rating": "Rating",
        "location": "Location",
        "description": "Description",
        "image_query": "Restaurant Name Location food HD"
      }
    },
    {
      "type": "TRANSPORT",
      "data": {
        "type": "Flight/Train/Bus",
        "company": "Company Name",
        "route": "Departure-Arrival",
        "duration": "Duration",
        "price": "Price (₹)"
      }
    }
  ]
}

CRITICAL RULES:
1. ALL money MUST be in Indian Rupees (₹) ONLY. Do not use $, €, or £. Example: ₹14,500.
2. The `image_query` field MUST be optimized for Google Image Search (include names, locations, and 'HD' or 'interior'/'exterior' as needed).
3. Do not include `image_query` for BUDGET or TRANSPORT widgets.
4. Your output MUST be 100% valid JSON, without any surrounding markdown or conversational text outside the JSON.
5. **MULTIPLE OPTIONS**: When recommending hotels, restaurants, or transport, you MUST provide **AT LEAST 4 to 5 different options** for each category in the `widgets` array so the user can compare prices and features.
"""

def fetch_images_for_query(query, max_results=3):
    try:
        results = DDGS().images(
            keywords=query,
            region="wt-wt",
            safesearch="moderate",
            size="Wallpaper",
            color="color",
            type_image="photo",
            max_results=max_results
        )
        return [res['image'] for res in results]
    except Exception as e:
        print(f"Error fetching image for {query}: {e}")
        return []

def augment_json_with_images(json_str):
    try:
        # Sometimes models wrap JSON in markdown block even if told not to
        if json_str.startswith("```json"):
            json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
        elif json_str.startswith("```"):
            json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
        
        data = json.loads(json_str.strip())
        
        queries = []
        for w in data.get('widgets', []):
            if 'image_query' in w.get('data', {}):
                queries.append((w, w['data']['image_query']))
        
        def fetch(item):
            widget, query = item
            images = fetch_images_for_query(query)
            # Fallback to LoremFlickr if DDGS fails
            widget['data']['images'] = images if images else [f"https://loremflickr.com/800/600/{query.replace(' ', ',')}/all"]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(fetch, queries)
            
        return json.dumps(data)
    except Exception as e:
        print(f"JSON parsing/augmentation error: {e}")
        return json_str

class ChatRequest(BaseModel):
    contents: List[Dict[str, Any]]
    session_id: str

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
        rows = c.fetchall()
        conn.close()
        
        # Convert to the format expected by the frontend (Gemini style)
        history = []
        for role, content in rows:
            history.append({
                "role": role,
                "parts": [{"text": content}]
            })
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        session_id = request.session_id
        
        # Save the latest user message to DB
        user_message = request.contents[-1]["parts"][0]["text"]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", 
                  (session_id, "user", user_message))
        conn.commit()
        
        config = genai.types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            response_mime_type="application/json"
        )
        
        # Get all available API keys
        from dotenv import dotenv_values
        env_vars = dotenv_values(".env")
        api_keys = [
            env_vars.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY"),
            env_vars.get("GEMINI_API_KEY_ALT") or os.environ.get("GEMINI_API_KEY_ALT"),
            env_vars.get("GEMINI_API_KEY_ALT_2") or os.environ.get("GEMINI_API_KEY_ALT_2")
        ]
        api_keys = [key for key in api_keys if key]
        
        last_error = None
        response = None
        models_to_try = [
            'gemini-2.0-flash', 
            'gemini-2.0-flash-lite', 
            'gemini-1.5-flash', 
            'gemini-2.5-flash',
            'gemini-2.5-flash-lite',
            'gemini-flash-latest'
        ]
        
        for model_name in models_to_try:
            model_success = False
            for i, key in enumerate(api_keys):
                temp_client = genai.Client(api_key=key)
                try:
                    response = temp_client.models.generate_content(
                        model=model_name,
                        contents=request.contents,
                        config=config
                    )
                    model_success = True
                    break
                except Exception as e:
                    last_error = e
                    error_msg = str(e).lower()
                    if "503" in error_msg or "unavailable" in error_msg or "500" in error_msg or "high demand" in error_msg or "not found" in error_msg:
                        break
                    elif "quota" in error_msg or "429" in error_msg or "rate limit" in error_msg or "resource_exhausted" in error_msg:
                        print(f"Key {i+1} exhausted for {model_name}. Trying next key...")
                        continue
                    else:
                        print(f"Unexpected error with key {i+1} for {model_name}: {e}")
                        continue
            if model_success:
                break
                    
        if not response and last_error:
            raise last_error
        
        bot_text = response.text
        
        # Process the JSON to fetch real images
        augmented_bot_text = augment_json_with_images(bot_text)
        
        # Save bot response to DB
        c.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", 
                  (session_id, "model", bot_text))
        conn.commit()
        conn.close()
        
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": augmented_bot_text}]
                    }
                }
            ]
        }
    except Exception as e:
        print(f"Error: {traceback.format_exc()}")
        error_detail = str(e)
        if "503" in error_detail or "unavailable" in error_detail or "high demand" in error_detail:
            friendly_msg = "The AI servers are currently under high demand. I'm trying my best to reconnect. Please try sending your message again in a few seconds."
        elif "quota" in error_detail or "429" in error_detail:
            friendly_msg = "API Quota exceeded. Please wait a moment or try again later."
        else:
            friendly_msg = f"Connection Error: {error_detail}"
            
        return {"error": {"message": friendly_msg, "type": "Server Error", "raw": error_detail}}

@app.get("/debug")
def debug_endpoint():
    from dotenv import dotenv_values
    env_vars = dotenv_values(".env")
    return {
        "keys_loaded_dotenv": len([k for k in [env_vars.get("GEMINI_API_KEY"), env_vars.get("GEMINI_API_KEY_ALT"), env_vars.get("GEMINI_API_KEY_ALT_2")] if k]),
        "keys_loaded_environ": len([k for k in [os.environ.get("GEMINI_API_KEY"), os.environ.get("GEMINI_API_KEY_ALT"), os.environ.get("GEMINI_API_KEY_ALT_2")] if k])
    }

app.mount("/", StaticFiles(directory="public", html=True), name="public")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
