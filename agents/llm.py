import os 
from dotenv import load_dotenv
from google import genai

load_dotenv()

CHAT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
EMBED_MODEL= "gemini-embedding-001"

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise SystemExit("GEMINI_API_KEY is missing. Add it to you .env file.")

cleint = genai.Client(api_key=API_KEY)