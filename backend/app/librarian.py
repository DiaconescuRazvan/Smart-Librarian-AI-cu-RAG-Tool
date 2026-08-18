import base64
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .books import get_summary_by_title
from .vector_store import initialize_vector_store, search_books


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL")

BAD_WORDS = {
    "prost", "proastă", "idiot", "idioată", "tâmpit", "tâmpită",
    "fraier", "fraieră", "dracu", "naiba",
}


def get_openai_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise ValueError("Lipsește OPENAI_API_KEY în fișierul .env.")
    if not OPENAI_CHAT_MODEL:
        raise ValueError("Lipsește OPENAI_CHAT_MODEL în fișierul .env.")
    return OpenAI(api_key=OPENAI_API_KEY)


def normalize_text(text: str) -> str:
    return re.sub(r"[^\w\săâîșț]", " ", text.lower())


def contains_bad_language(text: str) -> bool:
    return any(word in BAD_WORDS for word in normalize_text(text).split())


def _build_history_context(history: list[dict]) -> str:
    if not history:
        return "Nu există mesaje anterioare."

    return "\n".join(
        f"{message['role']}: {message['content']}"
        for message in history[-10:]
    )


def is_book_related(client: OpenAI, user_question: str, history: list[dict]) -> bool:
    response = client.chat.completions.create(
        model=OPENAI_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Clasifică întrebarea ca permisă numai dacă este exclusiv despre cărți. "
                    "Dacă include orice subiect din afara cărților, răspunde cu false. "
                    "Răspunde numai cu JSON valid: {\"book_related\": true} sau "
                    "{\"book_related\": false}. Sunt permise recomandări, rezumate, "
                    "autori, personaje, teme, genuri literare și informații despre o carte."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Istoricul conversației:\n{_build_history_context(history)}\n\n"
                    f"Întrebarea nouă: {user_question}"
                ),
            },
        ],
        response_format={"type": "json_object"},
    )

    try:
        result = json.loads(response.choices[0].message.content or "{}")
    except (json.JSONDecodeError, TypeError):
        return False

    return result.get("book_related") is True


def _build_books_context(books: list[dict]) -> str:
    return "\n".join(
        f"{index}. Titlu: {book['title']}\n"
        f"   Autor: {book['author']}\n"
        f"   Teme: {', '.join(book['themes'])}\n"
        f"   Distanță: {book['distance']}"
        for index, book in enumerate(books, start=1)
    )


def recommend_book(
    client: OpenAI,
    user_question: str,
    matches: list[dict],
    history: list[dict],
) -> tuple[str, str, str]:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_summary_by_title",
                "description": "Returnează rezumatul complet pentru o carte pe baza titlului exact.",
                "parameters": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}},
                    "required": ["title"],
                    "additionalProperties": False,
                },
            },
        }
    ]
    messages = [
        {
            "role": "system",
            "content": (
                "Ești un bibliotecar AI. Răspunde exclusiv despre cărți și nu oferi "
                "informații, instrucțiuni sau sfaturi despre alte subiecte. Alege o singură "
                "carte din topul primit și apelează tool-ul get_summary_by_title."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Istoricul conversației:\n{_build_history_context(history)}\n\n"
                f"Întrebarea utilizatorului: {user_question}\n\n"
                f"Top 3 cărți:\n{_build_books_context(matches)}"
            ),
        },
    ]

    first_response = client.chat.completions.create(
        model=OPENAI_CHAT_MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    assistant_message = first_response.choices[0].message
    tool_calls = assistant_message.tool_calls or []

    if not tool_calls:
        selected_title = matches[0]["title"]
        return (
            assistant_message.content or f"Îți recomand cartea {selected_title}.",
            get_summary_by_title(selected_title),
            selected_title,
        )

    tool_call = tool_calls[0]
    selected_title = json.loads(tool_call.function.arguments)["title"]
    summary = get_summary_by_title(selected_title)
    messages.append(assistant_message.model_dump(exclude_none=True))
    messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": summary})

    final_response = client.chat.completions.create(model=OPENAI_CHAT_MODEL, messages=messages)
    return (
        final_response.choices[0].message.content or f"Îți recomand cartea {selected_title}.",
        summary,
        selected_title,
    )


def recommend(user_question: str, history: list[dict] | None = None) -> dict:
    history = history or []
    client = get_openai_client()
    if contains_bad_language(user_question):
        raise ValueError("Te rog să folosești un limbaj respectuos.")
    if not is_book_related(client, user_question, history):
        raise ValueError("Pot răspunde doar la întrebări despre cărți, autori, personaje și recomandări literare.")

    initialize_vector_store()
    matches = search_books(user_question, number_of_results=3)
    if not matches:
        raise LookupError("Nu am găsit cărți relevante pentru această întrebare.")

    recommendation, summary, title = recommend_book(client, user_question, matches, history)
    selected_book = next((book for book in matches if book["title"] == title), matches[0])
    return {
        "recommendation": recommendation,
        "summary": summary,
        "title": title,
        "author": selected_book["author"],
        "themes": selected_book["themes"],
    }


def _image_filename(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_") + ".png"


def generated_image_path(title: str) -> Path:
    return BASE_DIR / "generated_images" / _image_filename(title)


def generate_book_image(title: str) -> str:
    client = get_openai_client()
    result = client.images.generate(
        model="gpt-image-1",
        prompt=(
            f"Create a beautiful cinematic illustration inspired by the book '{title}'. "
            "Do not include any text, title or logo. High quality digital painting."
        ),
    )
    image_b64 = result.data[0].b64_json
    output_dir = BASE_DIR / "generated_images"
    output_dir.mkdir(exist_ok=True)
    output_file = generated_image_path(title)
    output_file.write_bytes(base64.b64decode(image_b64))
    return image_b64


def generate_audio(recommendation: str, summary: str) -> bytes:
    client = get_openai_client()
    audio_text = f"Recomandarea Smart Librarian. {recommendation} Rezumat complet. {summary}"
    output_path = BASE_DIR / "generated_audio" / "recommendation.mp3"
    output_path.parent.mkdir(exist_ok=True)
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts", voice="coral", input=audio_text
    ) as response:
        response.stream_to_file(output_path)
    return output_path.read_bytes()
