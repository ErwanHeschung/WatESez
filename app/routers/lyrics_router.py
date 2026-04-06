from app.dependencies import AudioServiceDep
from fastapi import APIRouter, UploadFile, HTTPException, status
from app.models.dtos.error_response import ErrorResponse
from app.workers.audio_worker import audio_queue


router = APIRouter(
    prefix="/lyrics",
    tags=["lyrics"]
)

@router.post(
    "/register",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "File must be an audio type"
        },
        500: {
            "description": "Internal Server Error during processing"
        }
    }
)
async def upload_audio(
    file: UploadFile
):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio type")
    
    file_bytes = await file.read()
    filename = file.filename or "unknown file"
    
    await audio_queue.put((file_bytes, filename))
    
    return {
        "status": "queued", 
        "message": f"{filename} has been added to the processing queue. Position: {audio_queue.qsize()}"
    }
    
@router.get(
        "/{fingerprint}", 
        status_code=status.HTTP_200_OK,
        responses={
        404: {
            "model": ErrorResponse,
            "description": "Lyrics not found for the given fingerprint"
        },
        500: {
            "description": "Internal Server Error during retrieval"
        }
    }
)
async def get_lyrics(
    fingerprint: str, 
    audio_service: AudioServiceDep
):
    existing_lyrics = await audio_service.get_lyrics_by_fingerprint(fingerprint)
    
    if not existing_lyrics:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lyrics not found for the given fingerprint")
    return existing_lyrics