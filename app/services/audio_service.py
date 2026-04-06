from app.repositories.lyrics_repository import LyricsRepository
from fastapi import Depends
from app.services.noise_remover_service import (
    NoiseRemoverService,
    get_noise_remover_service,
)
from app.services.stt_service import STTService, get_stt_service
from app.models.entities.lyrics import Lyrics
from app.configs.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import subprocess
import json
import hashlib


class AudioService:
    def __init__(
        self,
        noise_remover_service: NoiseRemoverService,
        stt_service: STTService,
        lyrics_repo: LyricsRepository,
    ):
        self.noise_remover_service = noise_remover_service
        self.stt_service = stt_service
        self.lyrics_repo = lyrics_repo

    async def register_lyrics(self, file_bytes: bytes, filename: str) -> None:
        fingerprint = self.generate_acoustic_fingerprint(file_bytes)

        existing = await self.lyrics_repo.get_by_fingerprint(fingerprint)
        if existing:
            return

        cleaned_buffer = await self.noise_remover_service.remove_instrumental(
            file_bytes, filename
        )

        await self.noise_remover_service.save_to_storage(cleaned_buffer, filename)

        song_lyrics_dto = await self.stt_service.find_lyrics(cleaned_buffer)

        new_record = Lyrics(
            fingerprint=fingerprint,
            language=song_lyrics_dto.language,
            content=[line.model_dump() for line in song_lyrics_dto.lyrics],
        )

        await self.lyrics_repo.save(new_record)

    @staticmethod
    def generate_acoustic_fingerprint(audio_bytes: bytes) -> str:
        command = ["fpcalc", "-json", "-length", "0", "-"]

        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout, stderr = process.communicate(input=audio_bytes)

        if process.returncode != 0:
            raise RuntimeError(f"fpcalc failed: {stderr.decode()}")

        result = json.loads(stdout.decode())
        fingerprint_list = result.get("fingerprint", [])

        raw_acoustic_string = ",".join(map(str, fingerprint_list))

        hashed_fingerprint = hashlib.sha256(
            raw_acoustic_string.encode("utf-8")
        ).hexdigest()

        return hashed_fingerprint

    def get_lyrics_by_fingerprint(self, fingerprint: str) -> Lyrics | None:
        return self.lyrics_repo.get_by_fingerprint(fingerprint)


def get_audio_service(
    noise_remover: NoiseRemoverService = Depends(get_noise_remover_service),
    stt: STTService = Depends(get_stt_service),
    db: AsyncSession = Depends(get_db),
) -> AudioService:
    repo = LyricsRepository(session=db)

    return AudioService(
        noise_remover_service=noise_remover, stt_service=stt, lyrics_repo=repo
    )
