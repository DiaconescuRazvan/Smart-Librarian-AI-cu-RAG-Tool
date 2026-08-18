from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from urllib.parse import quote

from .librarian import generate_audio, generate_book_image, generated_image_path, recommend
from .conversation_store import (
    append_turn,
    create_conversation,
    get_conversation,
    list_conversations,
)
from .models import (
    AudioRequest,
    ConversationResponse,
    ConversationSummary,
    ImageRequest,
    RecommendationRequest,
    RecommendationResponse,
)


app = FastAPI(title="Smart Librarian API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/conversations", response_model=list[ConversationSummary])
def get_conversations():
    return list_conversations()


@app.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation_by_id(conversation_id: str):
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversația nu există.")
    return conversation


@app.post("/api/recommend", response_model=RecommendationResponse)
def create_recommendation(request: RecommendationRequest):
    conversation = (
        get_conversation(request.conversation_id)
        if request.conversation_id
        else create_conversation()
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversația nu există.")

    try:
        result = recommend(request.question.strip(), conversation.get("messages", []))
        append_turn(
            conversation["id"],
            request.question.strip(),
            result["recommendation"],
            result,
        )
        return {**result, "conversation_id": conversation["id"]}
    except ValueError as error:
        append_turn(conversation["id"], request.question.strip(), str(error))
        raise HTTPException(status_code=400, detail=str(error)) from error
    except LookupError as error:
        append_turn(conversation["id"], request.question.strip(), str(error))
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        append_turn(
            conversation["id"],
            request.question.strip(),
            f"Nu am putut procesa cererea: {error}",
        )
        raise HTTPException(status_code=500, detail=f"Nu am putut procesa cererea: {error}") from error


@app.post("/api/image")
def create_image(request: ImageRequest, http_request: Request) -> dict[str, str]:
    try:
        title = request.title.strip()
        generate_book_image(title)
        image_url = f"{str(http_request.base_url).rstrip('/')}/api/image?title={quote(title)}"
        return {"image": image_url}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Nu am putut genera imaginea: {error}") from error


@app.get("/api/image")
def serve_image(title: str):
    image_path = generated_image_path(title.strip())
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Imaginea nu există.")
    return FileResponse(image_path, media_type="image/png")


@app.post("/api/audio")
def create_audio(request: AudioRequest):
    try:
        audio = generate_audio(request.recommendation, request.summary)
        return Response(content=audio, media_type="audio/mpeg")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Nu am putut genera audio: {error}") from error
