
"""One place for the AI model settings."""
import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

CHAT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# Fallback models if the main model is busy or unavailable.
FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv(
        "GEMINI_FALLBACK_MODELS",
        "gemini-3.6-flash,gemini-3.5-flash-lite"
    ).split(",")
    if m.strip()
]

CHAT_MODELS = [CHAT_MODEL] + [
    m for m in FALLBACK_MODELS if m != CHAT_MODEL
]

EMBED_MODEL = "gemini-embedding-001"

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise SystemExit("GEMINI_API_KEY is missing. Add it to your .env file.")


# Global client for synchronous Gemini requests.
client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(
        timeout=60_000,
        retry_options=types.HttpRetryOptions(attempts=2),
    ),
)


def _should_try_next(error):
    """Check whether another model should be tried."""
    return (
        isinstance(error, errors.ServerError)
        or error.code in (404, 429)
    )


def generate(**kwargs):
    """Synchronous Gemini generation with model fallback."""
    for i, model in enumerate(CHAT_MODELS):
        try:
            return client.models.generate_content(
                model=model,
                **kwargs
            )

        except errors.APIError as error:
            if not _should_try_next(error) or i == len(CHAT_MODELS) - 1:
                raise

            print(
                f"[llm] {model} failed ({error.code}), "
                f"trying {CHAT_MODELS[i + 1]}"
            )


async def agenerate(**kwargs):
    """Asynchronous Gemini generation with a fresh client."""
    async_client = genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(
            timeout=60_000,
            retry_options=types.HttpRetryOptions(attempts=2),
        ),
    )

    try:
        for i, model in enumerate(CHAT_MODELS):
            try:
                return await async_client.aio.models.generate_content(
                    model=model,
                    **kwargs
                )

            except errors.APIError as error:
                if not _should_try_next(error) or i == len(CHAT_MODELS) - 1:
                    raise

                print(
                    f"[llm] {model} failed ({error.code}), "
                    f"trying {CHAT_MODELS[i + 1]}"
                )

    finally:
        await async_client.aio.aclose()
