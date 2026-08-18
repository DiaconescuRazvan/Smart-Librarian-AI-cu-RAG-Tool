import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4


BASE_DIR = Path(__file__).resolve().parents[1]
STORE_PATH = BASE_DIR / "conversations.json"
STORE_LOCK = Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_store() -> dict[str, dict]:
    if not STORE_PATH.exists():
        return {}

    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_store(conversations: dict[str, dict]) -> None:
    temporary_path = STORE_PATH.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(conversations, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(STORE_PATH)


def create_conversation() -> dict:
    timestamp = _now()
    conversation = {
        "id": uuid4().hex,
        "title": "Conversație nouă",
        "created_at": timestamp,
        "updated_at": timestamp,
        "messages": [],
    }

    with STORE_LOCK:
        conversations = _read_store()
        conversations[conversation["id"]] = conversation
        _write_store(conversations)

    return conversation


def get_conversation(conversation_id: str) -> dict | None:
    with STORE_LOCK:
        return _read_store().get(conversation_id)


def list_conversations() -> list[dict]:
    with STORE_LOCK:
        conversations = list(_read_store().values())

    return [
        {
            "id": conversation["id"],
            "title": conversation["title"],
            "created_at": conversation["created_at"],
            "updated_at": conversation["updated_at"],
            "message_count": len(conversation.get("messages", [])),
        }
        for conversation in sorted(
            conversations,
            key=lambda item: item.get("updated_at", ""),
            reverse=True,
        )
    ]


def append_turn(
    conversation_id: str,
    question: str,
    answer: str,
    result: dict | None = None,
) -> dict:
    with STORE_LOCK:
        conversations = _read_store()
        conversation = conversations.get(conversation_id)

        if conversation is None:
            raise KeyError(f"Conversația {conversation_id} nu există.")

        if not conversation["messages"]:
            conversation["title"] = question[:70].strip()

        conversation["messages"].append({"role": "user", "content": question})
        conversation["messages"].append(
            {"role": "assistant", "content": answer, "result": result}
        )
        conversation["updated_at"] = _now()
        _write_store(conversations)
        return conversation