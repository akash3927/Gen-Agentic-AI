from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, ChatResponse, SpeakRequest
from app.services.llm import generate_response, stream_response
from app.services.stt import transcribe_audio
from app.services.tts import generate_speech


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    response = generate_response(request.message)

    return ChatResponse(
        response=response
    )

@router.post("/chat/stream")
def chat_stream(request: ChatRequest):

    return StreamingResponse(
        stream_response(request.message),
        media_type="text/plain"
    )

@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):

    audio = await file.read()

    text = transcribe_audio(
        (file.filename, audio, file.content_type)
    )

    return {
        "text": text
    }

@router.post("/voice-chat")
async def voice_chat(file: UploadFile = File(...)):

    audio = await file.read()

    text = transcribe_audio(
        (file.filename, audio, file.content_type)
    )

    answer = generate_response(text)

    return {
        "transcript": text,
        "response": answer
    }

from fastapi.responses import FileResponse

@router.post("/speak")
def speak(request: SpeakRequest):
    audio = generate_speech(request.text)
    return StreamingResponse(iter([audio]), media_type="audio/mpeg")
