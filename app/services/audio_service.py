from fastapi import UploadFile, Depends
from app.services.noise_remover_service import NoiseRemoverService, get_noise_remover_service
from app.services.stt_service import STTService, get_stt_service

class AudioService:
    def __init__(self, noise_remover_service: NoiseRemoverService, stt_service: STTService):
        self.noise_remover_service = noise_remover_service
        self.stt_service = stt_service
    
    async def register_lyrics(self, file: UploadFile) -> str:
        cleaned_buffer = await self.noise_remover_service.remove_instrumental(file)
        await self.noise_remover_service.save_to_storage(cleaned_buffer, file.filename)
        lyrics = await self.stt_service.find_lyrics(cleaned_buffer)
        return lyrics
    

def get_audio_service(
    noise_remover: NoiseRemoverService = Depends(get_noise_remover_service),
    stt: STTService = Depends(get_stt_service)
) -> AudioService:
    return AudioService(noise_remover_service=noise_remover,stt_service=stt)