from typing import Annotated, TypeAlias
from fastapi import Depends

from app.services.audio_service import AudioService, get_audio_service

AudioServiceDep: TypeAlias = Annotated[AudioService, Depends(get_audio_service)]