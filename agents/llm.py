"""One place for the AI model settings."""
import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

CHAT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
# If the main model is busy (503/504), try these next, in order.
FALLBACK_MODELS = [m.strip() for m in os.getenv(
    "GEMINI_FALLBACK_MODELS", "gemini-3.6-flash,gemini-3.5-flash-lite").split(",") if m.strip()]
CHAT_MODELS = [CHAT_MODEL] + [m for m in FALLBACK_MODELS if m != CHAT_MODEL]
EMBED_MODEL = "gemini-embedding-001"

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise SystemExit("GEMINI_API_KEY is missing. Add it to your .env file.")

# Stop after 60 seconds and try at most 2 times, so a busy Gemini gives an error instead of hanging.
client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(timeout=60_000, retry_options=types.HttpRetryOptions(attempts=2)),
)


def _should_try_next(error: errors.APIError) -> bool:
    """Busy server (5xx), daily quota used up (429) or unknown model name (404): try the next model."""
    return isinstance(error, errors.ServerError) or error.code in (404, 429)


def generate(**kwargs):
    """Like client.models.generate_content, but falls back to the next model when one is busy."""
    for i, model in enumerate(CHAT_MODELS):
        try:
            return client.models.generate_content(model=model, **kwargs)
        except errors.APIError as error:
            if not _should_try_next(error) or i == len(CHAT_MODELS) - 1:
                raise
            print(f"[llm] {model} failed ({error.code}), trying {CHAT_MODELS[i + 1]}")


async def agenerate(**kwargs):
    """Async version of generate(), used by the MCP executor."""
    for i, model in enumerate(CHAT_MODELS):
        try:
            return await client.aio.models.generate_content(model=model, **kwargs)
        except errors.APIError as error:
            if not _should_try_next(error) or i == len(CHAT_MODELS) - 1:
                raise
            print(f"[llm] {model} failed ({error.code}), trying {CHAT_MODELS[i + 1]}")
