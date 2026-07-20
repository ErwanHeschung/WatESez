import asyncio
import io
from app.models.dtos.lyrics import LyricLine, SongLyrics
from faster_whisper import WhisperModel
from faster_whisper.vad import VadOptions
from app.configs.settings import settings
from fastapi.concurrency import run_in_threadpool

VAD_PARAMETERS = VadOptions(
    threshold=0.35,
    min_speech_duration_ms=200,
    min_silence_duration_ms=700,
    speech_pad_ms=300,
)


class STTService:
    def __init__(self):
        self.model = None

    def _load_ai_model(self):
        """Synchronous helper method to load Whisper into memory."""
        self.model = WhisperModel(
            settings.whisper_model,
            device="cpu",
            compute_type=settings.whisper_compute_type,
        )

    async def find_lyrics(self, audio: io.BytesIO) -> SongLyrics:
        if self.model is None:
            await asyncio.to_thread(self._load_ai_model)

        audio.seek(0)

        def sync_process():
            seg_gen, info_obj = self.model.transcribe(
                audio,
                language=settings.whisper_language,
                beam_size=settings.whisper_beam_size,
                condition_on_previous_text=False,
                initial_prompt="Song lyrics.",
                vad_filter=True,
                vad_parameters=VAD_PARAMETERS,
                word_timestamps=settings.whisper_word_timestamps,
                hallucination_silence_threshold=(
                    2.0 if settings.whisper_word_timestamps else None
                ),
                language_detection_segments=4,
            )
            return list(seg_gen), info_obj

        segments, info = await run_in_threadpool(sync_process)

        lyrics_data = [
            LyricLine(start=round(s.start, 2), end=round(s.end, 2), text=s.text.strip())
            for s in segments
            if self._is_plausible(s)
        ]

        return SongLyrics(language=info.language, lyrics=lyrics_data)

    @staticmethod
    def _is_plausible(segment) -> bool:
        """Drop segments Whisper emitted over instrumental or near-silent audio.

        On an isolated vocal stem the model hallucinates confidently in the gaps
        between verses, and those lines were previously written straight to the
        database.
        """
        if not segment.text.strip():
            return False
        if segment.avg_logprob < settings.whisper_min_avg_logprob:
            return False
        if segment.no_speech_prob > settings.whisper_max_no_speech_prob:
            return False
        return True


def get_stt_service() -> STTService:
    return STTService()
