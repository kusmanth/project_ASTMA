"""One place for the AI model settings."""
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

CHAT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
EMBED_MODEL = "gemini-embedding-001"

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise SystemExit("GEMINI_API_KEY is missing. Add it to your .env file.")

# Stop after 60 seconds and try at most 2 times, so a busy Gemini gives an error instead of hanging.
client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(timeout=60_000, retry_options=types.HttpRetryOptions(attempts=2)),
)