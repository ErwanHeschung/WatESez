import asyncio
import hashlib
import chromaprint
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

    async def register_lyrics(self, file_bytes: bytes, filename: str) -> str:
        """Transcribe and store lyrics, returning the track's fingerprint.

        The fingerprint is returned even when the track was already known, so
        the caller can always point at the resulting lyrics.
        """
        fingerprint = await self.generate_acoustic_fingerprint(file_bytes)

        existing = await self.lyrics_repo.get_by_fingerprint(fingerprint)
        if existing:
            return fingerprint

        cleaned_buffer = await self.noise_remover_service.remove_instrumental(
            file_bytes, filename
        )

        song_lyrics_dto = await self.stt_service.find_lyrics(cleaned_buffer)

        new_record = Lyrics(
            fingerprint=fingerprint,
            language=song_lyrics_dto.language,
            content=[line.model_dump() for line in song_lyrics_dto.lyrics],
        )

        await self.lyrics_repo.save(new_record)

        return fingerprint

    @staticmethod
    async def generate_acoustic_fingerprint(audio_bytes: bytes) -> str:
        async def _fingerprint():
            pcm_process = await asyncio.create_subprocess_exec(
                "ffmpeg",
                "-i",
                "pipe:0",
                "-ar",
                "44100",
                "-ac",
                "1",
                "-f",
                "s16le",
                "pipe:1",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            pcm_data, _ = await pcm_process.communicate(input=audio_bytes)

            if pcm_process.returncode != 0:
                raise RuntimeError("ffmpeg decode failed")

            fp = chromaprint.Fingerprinter()
            fp.start(44100, 1)
            fp.feed(pcm_data)
            raw_fingerprint = fp.finish()
            if not raw_fingerprint:
                raise RuntimeError("chromaprint produced an empty fingerprint")
            return hashlib.sha256(raw_fingerprint).hexdigest()

        return await _fingerprint()

    async def get_lyrics_by_fingerprint(self, fingerprint: str) -> Lyrics | None:
        return await self.lyrics_repo.get_by_fingerprint(fingerprint)


def get_audio_service(
    noise_remover: NoiseRemoverService = Depends(get_noise_remover_service),
    stt: STTService = Depends(get_stt_service),
    db: AsyncSession = Depends(get_db),
) -> AudioService:
    repo = LyricsRepository(session=db)

    return AudioService(
        noise_remover_service=noise_remover, stt_service=stt, lyrics_repo=repo
    )
