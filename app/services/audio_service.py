from app.repositories.lyrics_repository import LyricsRepository
from fastapi import UploadFile, Depends
from app.services.noise_remover_service import NoiseRemoverService, get_noise_remover_service
from app.services.stt_service import STTService, get_stt_service
import hashlib
from app.models.entities.lyrics import Lyrics
from app.configs.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

class AudioService:
    def __init__(
            self, 
            noise_remover_service: NoiseRemoverService, 
            stt_service: STTService,
            lyrics_repo: LyricsRepository
    ):
        self.noise_remover_service = noise_remover_service
        self.stt_service = stt_service
        self.lyrics_repo = lyrics_repo
    
    async def register_lyrics(self, file: UploadFile) -> None:
        file_bytes = await file.read()
        await file.seek(0)
        fingerprint = hashlib.sha256(file_bytes).hexdigest()

        existing = await self.lyrics_repo.get_by_fingerprint(fingerprint)
        if existing:
            return 

        cleaned_buffer = await self.noise_remover_service.remove_instrumental(file)

        await self.noise_remover_service.save_to_storage(cleaned_buffer, file.filename)
        
        song_lyrics_dto = await self.stt_service.find_lyrics(cleaned_buffer)
        
        new_record = Lyrics(
            fingerprint=fingerprint,
            language=song_lyrics_dto.language,
            content=[line.model_dump() for line in song_lyrics_dto.lyrics]
        )

        await self.lyrics_repo.save(new_record)
    

def get_audio_service(
    noise_remover: NoiseRemoverService = Depends(get_noise_remover_service),
    stt: STTService = Depends(get_stt_service),
    db: AsyncSession = Depends(get_db)
) -> AudioService:
    repo = LyricsRepository(session=db)
 
    return AudioService(
        noise_remover_service=noise_remover,
        stt_service=stt,
        lyrics_repo=repo
    )