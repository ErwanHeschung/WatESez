from app.models.entities.lyrics import Lyrics
from app.repositories.lyrics_repository import LyricsRepository
from app.services.fingerprint_service import FingerprintService
from app.services.noise_remover_service import NoiseRemoverService
from app.services.stt_service import STTService


class AudioService:
    """Orchestrates the transcription pipeline.

    Owns the ordering of the steps and nothing else; fingerprinting,
    separation, transcription and persistence each live behind their own
    collaborator.
    """

    def __init__(
        self,
        fingerprint_service: FingerprintService,
        noise_remover_service: NoiseRemoverService,
        stt_service: STTService,
        lyrics_repo: LyricsRepository,
    ):
        self.fingerprint_service = fingerprint_service
        self.noise_remover_service = noise_remover_service
        self.stt_service = stt_service
        self.lyrics_repo = lyrics_repo

    async def register_lyrics(self, file_bytes: bytes, filename: str) -> str:
        """Transcribe and store lyrics, returning the track's fingerprint.

        The fingerprint is returned even when the track was already known, so
        the caller can always point at the resulting lyrics.
        """
        fingerprint = await self.fingerprint_service.generate(file_bytes)

        if await self.lyrics_repo.get_by_fingerprint(fingerprint):
            return fingerprint

        vocals = await self.noise_remover_service.remove_instrumental(
            file_bytes, filename
        )
        song_lyrics = await self.stt_service.find_lyrics(vocals)

        await self.lyrics_repo.save(
            Lyrics(
                fingerprint=fingerprint,
                language=song_lyrics.language,
                content=[line.model_dump() for line in song_lyrics.lyrics],
            )
        )

        return fingerprint
