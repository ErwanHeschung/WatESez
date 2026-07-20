from fastapi import APIRouter, status

from app.dependencies import LyricsRepositoryDep
from app.exceptions import LyricsNotFoundError
from app.models.dtos.error_response import ErrorResponse

router = APIRouter(prefix="/lyrics", tags=["lyrics"])


@router.get(
    "/{fingerprint}",
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Lyrics not found for the given fingerprint",
        },
    },
)
async def get_lyrics(fingerprint: str, lyrics_repo: LyricsRepositoryDep):
    lyrics = await lyrics_repo.get_by_fingerprint(fingerprint)

    if not lyrics:
        raise LyricsNotFoundError(fingerprint)

    return lyrics
