from fastapi import APIRouter, UploadFile, HTTPException
from app.dependencies import AudioServiceDep
from app.models.error_response import ErrorResponse


router = APIRouter(
    prefix="/lyrics",
    tags=["lyrics"]
)

@router.post(
    "/register",
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
    service: AudioServiceDep    
):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio type")

    result = await service.register_lyrics(file)
    return result