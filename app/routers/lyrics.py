from fileinput import filename

from fastapi import APIRouter, UploadFile, HTTPException
from app.models.dtos.error_response import ErrorResponse
from app.workers.audio_worker import audio_queue

router = APIRouter(
    prefix="/lyrics",
    tags=["lyrics"]
)

@router.post(
    "/register",
    status_code=202,
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