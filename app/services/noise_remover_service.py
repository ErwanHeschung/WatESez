import io
from app.configs.settings import settings
from fastapi import UploadFile
from pathlib import Path
from audio_separator.separator import Separator

class NoiseRemoverService:
    def __init__(self):
        self.storage_dir = Path("./storage")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.separator = Separator()
        self.separator.load_model(settings.separate_model)

    async def remove_instrumental(self, file: UploadFile) -> io.BytesIO:
        input_path = self.storage_dir / f"input_{file.filename}"
        with open(input_path, "wb") as f:
            f.write(await file.read())

        output_files = self.separator.separate(str(input_path))

        vocal_filename = next(f for f in output_files if "Vocals" in f)
        vocal_path = Path(vocal_filename)

        exported_io = io.BytesIO()
        with open(vocal_path, "rb") as f:
            exported_io.write(f.read())

        input_path.unlink(missing_ok=True)
        for f in output_files:
            Path(f).unlink(missing_ok=True)

        exported_io.seek(0)
        await file.seek(0)
        return exported_io
    
    async def save_to_storage(self, buffer: io.BytesIO, original_name: str) -> str:
        safe_name = f"vocals_{original_name}"
        file_path = self.storage_dir / safe_name
        
        buffer.seek(0)
        with open(file_path, "wb") as f:
            f.write(buffer.getbuffer())

        return str(file_path)

def get_noise_remover_service() -> NoiseRemoverService:
    return NoiseRemoverService()