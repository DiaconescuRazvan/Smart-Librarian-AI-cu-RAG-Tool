import base64
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from books import get_summary_by_title 
from vector_store import initialize_vector_store, search_books


BASE_DIR = Path(__file__).resolve().parent


load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL")


def _build_books_context(books: list[dict]) -> str:
    lines = []

    for index, book in enumerate(books, start=1):
        lines.append(
            f"{index}. Titlu: {book['title']}\n"
            f"   Autor: {book['author']}\n"
            f"   Teme: {', '.join(book['themes'])}\n"
            f"   Distanță: {book['distance']}"
        )

    return "\n".join(lines)


def _get_openai_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise ValueError("Lipsește OPENAI_API_KEY în fișierul .env.")

    if not OPENAI_CHAT_MODEL:
        raise ValueError("Lipsește OPENAI_CHAT_MODEL în fișierul .env.")

    return OpenAI(api_key=OPENAI_API_KEY)


def _recommend_book(client: OpenAI, user_question: str, matches: list[dict]) -> tuple[str, str, str]:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_summary_by_title",
                "description": "Returnează rezumatul complet pentru o carte pe baza titlului exact.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Titlul exact al cărții recomandate.",
                        }
                    },
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
                "Ești un bibliotecar AI. Primești cele mai relevante 3 cărți găsite într-o bază vectorială. "
                "Alege o singură carte care răspunde cel mai bine întrebării utilizatorului. "
                "După ce alegi, apelează tool-ul get_summary_by_title cu titlul exact al cărții alese."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Întrebarea utilizatorului: {user_question}\n\n"
                f"Top 3 cărți găsite:\n{_build_books_context(matches)}"
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
        fallback_title = matches[0]["title"]
        recommendation_text = assistant_message.content or f"Îți recomand cartea {fallback_title}."
        summary = get_summary_by_title(fallback_title)
        return recommendation_text, summary, fallback_title

    tool_call = tool_calls[0]
    arguments = json.loads(tool_call.function.arguments)
    selected_title = arguments["title"]
    summary = get_summary_by_title(selected_title)

    messages.append(assistant_message.model_dump(exclude_none=True))
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": summary,
        }
    )

    final_response = client.chat.completions.create(
        model=OPENAI_CHAT_MODEL,
        messages=messages,
    )

    recommendation_text = final_response.choices[0].message.content or f"Îți recomand cartea {selected_title}."
    return recommendation_text, summary, selected_title

BAD_WORDS = {
    "prost",
    "proastă",
    "idiot",
    "idioată",
    "tâmpit",
    "tâmpită",
    "fraier",
    "fraieră",
    "dracu",
    "naiba",
}


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\săâîșț]", " ", text)
    return text


def contains_bad_language(text: str) -> bool:
    normalized_text = normalize_text(text)
    words = normalized_text.split()
    return any(word in BAD_WORDS for word in words)


def generate_audio(
    client: OpenAI,
    recommendation: str,
    summary: str,
) -> Path:
    audio_text = (
        f"Recomandarea Smart Librarian. {recommendation} "
        f"Rezumat complet. {summary}"
    )

    output_path = BASE_DIR / "recommendation.mp3"

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="coral",
        input=audio_text,
    ) as response:
        response.stream_to_file(output_path)

    return output_path


def generate_book_image(
    client: OpenAI,
    title: str,
) -> str:
    prompt = (
        f"Create a beautiful, cinematic illustration inspired by the book "
        f"'{title}'. "
        "Do not include any text, title or logo. "
        "High quality digital painting."
    )

    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
    )

    return result.data[0].b64_json


def save_generated_image(
    image_b64: str,
    title: str,
) -> Path:
    image_folder = BASE_DIR / "generated_images"
    image_folder.mkdir(exist_ok=True)

    filename = (
        title.lower()
        .replace(" ", "_")
        .replace(":", "")
        + ".png"
    )

    output_file = image_folder / filename

    with open(output_file, "wb") as file:
        file.write(base64.b64decode(image_b64))

    return output_file


def main() -> None:
    print("Smart Librarian CLI")
    print("Scrie o întrebare despre ce fel de carte vrei sau tastează 'exit' pentru închidere.\n")

    initialize_vector_store()
    client = _get_openai_client()

    while True:
        user_question = input("Tu: ").strip()

        if user_question.lower() == "exit":
            print("La revedere!")
            break

        if not user_question:
            print("Te rog scrie o întrebare validă.\n")
            continue

        if contains_bad_language(user_question):
            print(
                "\nSmart Librarian: Te rog să folosești un limbaj respectuos. "
                "Mesajul nu a fost trimis către LLM.\n"
            )
            continue

        matches = search_books(user_question, number_of_results=3)

        if not matches:
            print("Nu am găsit cărți relevante pentru această întrebare.\n")
            continue

        recommendation_text, full_summary, selected_title = _recommend_book(
            client,
            user_question,
            matches,
        )

        print("\nRecomandare:")
        print(recommendation_text)
        print("\nRezumat complet:")
        print(full_summary)
        print()

        generate = input(
            "\nVrei să generezi o imagine? (da/nu): "
        ).strip().lower()

        if generate in {"da", "d", "yes", "y"}:
            print("\nSe generează imaginea...\n")

            image = generate_book_image(
                client,
                selected_title,
            )

            file = save_generated_image(
                image,
                selected_title,
            )

            print(f"Imagine salvată în:\n{file}\n")

        create_audio = input(
            "Vrei să generezi varianta audio? (da/nu): "
        ).strip().lower()

        if create_audio in {"da", "d", "yes", "y"}:
            try:
                audio_path = generate_audio(
                    client,
                    recommendation_text,
                    full_summary,
                )
                print(f"Fișier audio generat: {audio_path}\n")
            except Exception as error:
                print(f"Nu am putut genera fișierul audio: {error}\n")


if __name__ == "__main__":
    main()