import io
from faster_whisper import WhisperModel

class STTService:
    def __init__(self):
        self.model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")

    async def find_lyrics(self, audio: io.BytesIO) -> str:
        audio.seek(0)
        segments, _ = self.model.transcribe(audio, beam_size=1, vad_filter=True)

        lyrics_list = [segment.text.strip() for segment in segments]
        full_lyrics = "\n".join(lyrics_list)

        return full_lyrics

def get_stt_service() -> STTService:
    return STTService()