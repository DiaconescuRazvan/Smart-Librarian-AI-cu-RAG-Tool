from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
import os

from books import load_books


BASE_DIR = Path(__file__).resolve().parent
CHROMA_DB_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "book_summaries"


load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


def _get_collection():
    if not OPENAI_API_KEY:
        raise ValueError("Lipsește OPENAI_API_KEY în fișierul .env.")

    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    embedding_function = OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name=OPENAI_EMBEDDING_MODEL,
    )

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
    )


def initialize_vector_store():
    books = load_books()
    collection = _get_collection()

    ids = []
    documents = []
    metadatas = []

    for book in books:
        title = str(book.get("title", "")).strip()
        author = str(book.get("author", "")).strip()
        themes = book.get("themes", [])
        short_summary = str(book.get("short_summary", "")).strip()

        document = (
            f"Title: {title}\n"
            f"Author: {author}\n"
            f"Themes: {', '.join(themes)}\n"
            f"Short summary: {short_summary}"
        )

        ids.append(title.lower())
        documents.append(document)
        metadatas.append(
            {
                "title": title,
                "author": author,
                "themes": ", ".join(themes),
            }
        )

    if ids:
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

    return collection


def search_books(query: str, number_of_results: int = 3):
    collection = _get_collection()

    results = collection.query(
        query_texts=[query],
        n_results=number_of_results,
    )

    matches = []
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for metadata, distance in zip(metadatas, distances):
        themes_text = metadata.get("themes", "")
        themes = [theme.strip() for theme in themes_text.split(",") if theme.strip()]

        matches.append(
            {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "themes": themes,
                "distance": distance,
            }
        )

    return matches