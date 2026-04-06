import asyncio
import io
from app.models.dtos.lyrics import LyricLine, SongLyrics
from faster_whisper import WhisperModel
from app.configs.settings import settings
from fastapi.concurrency import run_in_threadpool

class STTService:
    def __init__(self):
        self.model = None
    
    def _load_ai_model(self):
        """Synchronous helper method to load Whisper into memory."""
        self.model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")

    async def find_lyrics(self, audio: io.BytesIO) -> SongLyrics:
        if self.model is None:
            await asyncio.to_thread(self._load_ai_model)
            
        audio.seek(0)

        def sync_process():
            seg_gen, info_obj = self.model.transcribe(audio, beam_size=1, vad_filter=True)
            return list(seg_gen), info_obj

        segments, info = await run_in_threadpool(sync_process)

        lyrics_data = [
            LyricLine(
                start=round(s.start, 2),
                end=round(s.end, 2),
                text=s.text.strip()
            ) for s in segments
        ]

        return SongLyrics(
            language=info.language,
            lyrics=lyrics_data
        )
        
def get_stt_service() -> STTService:
    return STTService()