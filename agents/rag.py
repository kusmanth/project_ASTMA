"""RAG part of Agent 1: store the knowledge file in Pinecone and search it."""
import os
from pathlib import Path

from google.genai import types
from pinecone import Pinecone, ServerlessSpec

from agents.llm import EMBED_MODEL, client

KNOWLEDGE_FILE = Path(__file__).parent / "knowledge.txt"
DIMENSIONS = 768
INDEX_NAME = os.getenv("PINECONE_INDEX", "astma-knowledge")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise SystemExit("PINECONE_API_KEY is missing. Add it to your .env file.")

pc = Pinecone(api_key=PINECONE_API_KEY)


def embed(texts: list[str], task_type: str) -> list[list[float]]:
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(output_dimensionality=DIMENSIONS, task_type=task_type),
    )
    return [e.values for e in result.embeddings]


def load_sections() -> list[tuple[str, str]]:
    """Split the knowledge file into (task_name, content), one per '## ' heading."""
    sections = []
    for block in KNOWLEDGE_FILE.read_text(encoding="utf-8").split("## ")[1:]:
        task_name, _, body = block.partition("\n")
        sections.append((task_name.strip(), body.strip()))
    return sections


def get_index():
    """Create the Pinecone index the first time, then reuse it."""
    if not pc.has_index(INDEX_NAME):
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSIONS,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(INDEX_NAME)


def build_index() -> None:
    """Run once (and again whenever knowledge.txt changes)."""
    sections = load_sections()
    vectors = embed([f"{name}\n{body}" for name, body in sections], "RETRIEVAL_DOCUMENT")
    index = get_index()
    try:
        index.delete(delete_all=True)  # remove old tasks
    except Exception:
        pass  # a brand new index is empty, nothing to delete
    index.upsert(vectors=[
        {"id": f"task-{i}", "values": vector, "metadata": {"task_name": name, "content": body}}
        for i, ((name, body), vector) in enumerate(zip(sections, vectors), start=1)
    ])
    print(f"Stored {len(sections)} tasks in Pinecone index '{INDEX_NAME}': {[n for n, _ in sections]}")


def search_top(question: str, k: int = 2) -> list[tuple[str, str, float]]:
    """Return the k closest tasks as (task_name, content, distance), closest first.
    Pinecone gives a similarity score (1 = same meaning). distance = 1 - score, so smaller = closer."""
    vector = embed([question], "RETRIEVAL_QUERY")[0]
    result = pc.Index(INDEX_NAME).query(vector=vector, top_k=k, include_metadata=True)
    return [(m.metadata["task_name"], m.metadata["content"], 1 - m.score) for m in result.matches]


def search(question: str) -> tuple[str, str, float]:
    """Return only the closest task."""
    return search_top(question, 1)[0]


if __name__ == "__main__":
    build_index()