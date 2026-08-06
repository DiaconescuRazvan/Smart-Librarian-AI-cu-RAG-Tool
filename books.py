import json
from pathlib import Path


BOOKS_FILE = Path(__file__).resolve().parent / "data" / "book_summaries.json"


def load_books() -> list[dict]:
    with BOOKS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_summary_by_title(title: str) -> str:
    normalized_title = title.strip().lower()

    for book in load_books():
        book_title = str(book.get("title", "")).strip().lower()

        if book_title == normalized_title:
            return str(book.get("full_summary", "Rezumat indisponibil."))

    return f'Nu am găsit nicio carte cu titlul "{title}".'