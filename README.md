TravelX – AI Powered Travel Planning Assistant
Overview

TravelX is an AI-powered travel planning web application that generates complete travel itineraries using natural language prompts. Users can simply describe their trip requirements, and the system intelligently creates structured travel recommendations including hotels, restaurants, transportation, and budget planning.

The project combines FastAPI, Gemini AI, SQLite, and a modern frontend interface to deliver a smart interactive travel planning experience.

Features
AI-generated travel itineraries
Smart hotel recommendations
Restaurant and food suggestions
Transport planning
Budget estimation with visual charts
Real-time travel card widgets
Multi-model Gemini AI fallback system
Multi-API key rotation handling
Persistent chat history using SQLite
Dynamic travel images using DuckDuckGo image search
Session-based conversations
Dark mode UI
Interactive sidebar and smart result panels
Tech Stack
Backend
Python
FastAPI
SQLite
Google Gemini API
DuckDuckGo Search API
Frontend
HTML
CSS
JavaScript
Database
SQLite (chat_history.db)
Project Structure
TravelX/
│
├── public/                 # Frontend files
│   ├── index.html
│   ├── style.css
│   ├── script.js
│
├── main.py                 # Main FastAPI backend
├── .env                    # Gemini API keys
├── chat_history.db         # SQLite database
│
├── check_models.py         # Lists available Gemini models
├── test_keys.py            # Tests all API keys
├── test_models.py          # Benchmarks Gemini models
├── reproduce_error.py      # Error debugging script
├── test_gemini.py          # Basic Gemini API test
│
└── README.md
How the System Works
1. User Input

The user enters a travel request in natural language.

Example:

Plan a 3-day trip from Jalandhar to Delhi for 4 friends
2. Gemini AI Processing

The backend sends the request to Gemini AI with a strict system instruction that forces the response into structured JSON format.

The AI generates:

Overview
Hotels
Food Recommendations
Transportation
Budget Breakdown
3. Image Augmentation

The backend automatically:

Searches travel-related images
Fetches real hotel and restaurant photos
Injects image URLs into widgets
4. Frontend Rendering

The frontend converts JSON widgets into:

Hotel cards
Food cards
Budget charts
Transport panels
Smart travel widgets
Backend Deep Dive
main.py
init_db()

Creates the SQLite database and message storage table.

Stores:

Session ID
User messages
AI responses
Timestamps
system_instruction

Defines strict JSON schema rules for Gemini AI responses.

Widget Types:

OVERVIEW
HOTEL
FOOD
TRANSPORT
BUDGET
fetch_images_for_query()

Uses DuckDuckGo image search to fetch travel images dynamically.

augment_json_with_images()

Processes AI JSON responses and injects image URLs into travel widgets.

Features:

Removes markdown formatting
Parses JSON
Uses multithreading
Adds fallback images if needed
POST /chat

Main API endpoint.

Responsibilities:

Stores user messages
Rotates across multiple Gemini models
Rotates across multiple API keys
Handles quota/rate-limit errors
Returns structured AI response
GET /history/{session_id}

Restores previous chat sessions from SQLite database.

GET /debug

Debug endpoint for checking loaded API keys.

Gemini Model Fallback System

TravelX uses:

3 API Keys
6 Gemini Models

This creates a robust fallback architecture that avoids:

Rate limits
Quota exhaustion
Temporary model failures

Supported Models:

gemini-2.0-flash
gemini-2.0-flash-lite
gemini-1.5-flash
gemini-2.5-flash
gemini-2.5-flash-lite
gemini-flash-latest
Database
SQLite Database: chat_history.db
Table: messages
Column	Description
id	Unique message ID
session_id	User session identifier
role	user/model
content	Message text
timestamp	Time of message
Frontend UI

The frontend contains:

Left Sidebar
New Chat
Saved Trips
Settings
Dark Mode Toggle
Center Chat Section

Displays:

User prompts
AI-generated responses
Smart Results Panel

Contains:

Overview Tab
Hotels Tab
Food Tab
Transport Tab
Budget Tab
Utility Scripts
check_models.py

Lists available Gemini models.

test_keys.py

Checks whether API keys are working.

test_models.py

Benchmarks Gemini model response speed.

reproduce_error.py

Used for debugging Gemini API issues.

test_gemini.py

Simple Gemini API connectivity test.

Installation
Clone Repository
git clone <repository-url>
cd TravelX
Install Dependencies
pip install -r requirements.txt
Configure Environment Variables

Create a .env file:

GEMINI_API_KEY=your_key_here
GEMINI_API_KEY_ALT=your_key_here
GEMINI_API_KEY_ALT_2=your_key_here
Run the Server
python main.py

Server runs on:

http://localhost:8001
Known Issue

Currently, the system stores the original AI response in SQLite instead of the image-augmented version.

Result:

Images disappear after page refresh.

Recommended Fix:
Store augmented_bot_text instead of bot_text in the database.

Future Improvements
Real hotel booking APIs
Flight ticket integration
Google Maps integration
AI trip optimization
User authentication
Cloud deployment
PDF itinerary export
Voice assistant integration
Author

Saksham Rawat
B.Tech CSE Student – Lovely Professional University

License

This project is for educational and learning purposes.
