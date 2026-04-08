import asyncio
from app.configs.database import async_session_maker
from app.services.noise_remover_service import NoiseRemoverService
from app.services.stt_service import STTService
from app.repositories.lyrics_repository import LyricsRepository
from app.services.audio_service import AudioService
from app.configs.settings import settings

audio_queue = asyncio.Queue(maxsize=settings.audio_queue_max_size)


async def process_audio_queue():
    noise_remover = NoiseRemoverService()
    stt = STTService()

    while True:
        file_bytes, filename = await audio_queue.get()

        try:
            async with async_session_maker() as db_session:
                repo = LyricsRepository(session=db_session)
                audio_service = AudioService(
                    noise_remover_service=noise_remover,
                    stt_service=stt,
                    lyrics_repo=repo,
                )
                await audio_service.register_lyrics(file_bytes, filename)

        except Exception as e:
            print(f"Error processing {filename}: {e}", flush=True)

        finally:
            audio_queue.task_done()
