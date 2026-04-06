from fileinput import filename

from fastapi import APIRouter, UploadFile, HTTPException, BackgroundTasks
from app.dependencies import AudioServiceDep
from app.models.dtos.error_response import ErrorResponse



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
    file: UploadFile, 
    background_tasks: BackgroundTasks,
    service: AudioServiceDep    
):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio type")
    
    file_bytes = await file.read()
    filename = file.filename or "unknown file"

    background_tasks.add_task(service.register_lyrics, file_bytes, filename)
    return {
        "status": "processing", 
        "message": f"{filename} is being processed in the background."
    }