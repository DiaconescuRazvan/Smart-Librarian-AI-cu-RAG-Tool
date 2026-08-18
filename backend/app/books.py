import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
BOOKS_FILE = BASE_DIR / "data" / "book_summaries.json"


def load_books() -> list[dict]:
    with BOOKS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_book_by_title(title: str) -> dict | None:
    normalized_title = title.strip().lower()

    for book in load_books():
        if str(book.get("title", "")).strip().lower() == normalized_title:
            return book

    return None


def get_summary_by_title(title: str) -> str:
    book = get_book_by_title(title)
    if book is None:
        return f'Nu am găsit nicio carte cu titlul "{title}".'

    return str(book.get("full_summary", "Rezumat indisponibil."))
