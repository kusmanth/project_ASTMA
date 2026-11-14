"""RAG part of Agent 1: store the knowledge file in pgvector and search it."""
from pathlib import Path

from google.genai import types
from sqlalchemy import text

from agents.llm import EMBED_MODEL, client
from app.database import engine

KNOWLEDGE_FILE = Path(__file__).parent / "knowledge.txt"
DIMENSIONS = 768


def embed(texts: list[str], task_type: str) -> list[list[float]]:
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(output_dimensionality=DIMENSIONS, task_type=task_type),
    )
    return [e.values for e in result.embeddings]


def to_pgvector(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


def load_sections() -> list[tuple[str, str]]:
    """Split the knowledge file into (task_name, content), one per '## ' heading."""
    sections = []
    for block in KNOWLEDGE_FILE.read_text(encoding="utf-8").split("## ")[1:]:
        task_name, _, body = block.partition("\n")
        sections.append((task_name.strip(), body.strip()))
    return sections


def build_index() -> None:
    """Run once (and again whenever knowledge.txt changes)."""
    sections = load_sections()
    vectors = embed([f"{name}\n{body}" for name, body in sections], "RETRIEVAL_DOCUMENT")
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text(
            f"CREATE TABLE IF NOT EXISTS knowledge_chunks ("
            f"id SERIAL PRIMARY KEY, task_name TEXT NOT NULL, content TEXT NOT NULL, "
            f"embedding vector({DIMENSIONS}) NOT NULL)"
        ))
        conn.execute(text("DELETE FROM knowledge_chunks"))
        for (name, body), vector in zip(sections, vectors):
            conn.execute(
                text("INSERT INTO knowledge_chunks (task_name, content, embedding) "
                     "VALUES (:name, :content, CAST(:embedding AS vector))"),
                {"name": name, "content": body, "embedding": to_pgvector(vector)},
            )
    print(f"Stored {len(sections)} tasks in knowledge_chunks: {[n for n, _ in sections]}")


def search(question: str) -> tuple[str, str, float]:
    """Return the closest task: (task_name, content, distance). Smaller distance = closer."""
    vector = embed([question], "RETRIEVAL_QUERY")[0]
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT task_name, content, embedding <=> CAST(:q AS vector) AS distance "
                 "FROM knowledge_chunks ORDER BY distance LIMIT 1"),
            {"q": to_pgvector(vector)},
        ).one()
    return row.task_name, row.content, float(row.distance)


if __name__ == "__main__":
    build_index()