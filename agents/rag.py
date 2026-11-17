"""RAG part of Agent 1: read the knowledge documents (Word / PDF), store them in Pinecone, search them.

Knowledge documents live in agents/knowledge/. One file = one task.
The file name is the task name, for example "Book emergency trip.docx".
"""
import os
import re
from pathlib import Path

from docx import Document
from google.genai import types
from pinecone import Pinecone, ServerlessSpec
from pypdf import PdfReader

from agents.llm import EMBED_MODEL, client

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
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


def read_document(path: Path) -> str:
    """Get the plain text out of a Word, PDF or text file."""
    if path.suffix == ".docx":
        return "\n".join(p.text for p in Document(path).paragraphs if p.text.strip())
    if path.suffix == ".pdf":
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return path.read_text(encoding="utf-8")


def load_sections() -> list[tuple[str, str, str]]:
    """Read every document in the knowledge folder: (task_name, content, file_name)."""
    sections = []
    for path in sorted(KNOWLEDGE_DIR.iterdir()):
        if path.suffix not in (".docx", ".pdf", ".txt") or path.name.startswith("~$"):
            continue  # skip other files and Word's temporary "~$" files
        task_name = path.stem
        lines = [line.strip() for line in read_document(path).splitlines() if line.strip()]
        if lines and lines[0].lower() == task_name.lower():
            lines = lines[1:]  # the title is already the task name
        sections.append((task_name, "\n".join(lines), path.name))
    if not sections:
        raise SystemExit(f"No .docx, .pdf or .txt files found in {KNOWLEDGE_DIR}")
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
    """Run once, and again whenever a knowledge document is added or changed."""
    sections = load_sections()
    vectors = embed([f"{name}\n{body}" for name, body, _ in sections], "RETRIEVAL_DOCUMENT")
    index = get_index()
    try:
        index.delete(delete_all=True)  # remove old tasks
    except Exception:
        pass  # a brand new index is empty, nothing to delete
    index.upsert(vectors=[
        {"id": re.sub(r"[^a-z0-9]+", "-", name.lower()), "values": vector,
         "metadata": {"task_name": name, "content": body, "source": file_name}}
        for (name, body, file_name), vector in zip(sections, vectors)
    ])
    for name, _, file_name in sections:
        print(f"Stored '{name}' from {file_name}")
    print(f"{len(sections)} tasks in Pinecone index '{INDEX_NAME}'")


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