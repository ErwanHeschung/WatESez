import asyncio
import io
from app.configs.settings import settings
from pathlib import Path
from audio_separator.separator import Separator
import aiofiles


class NoiseRemoverService:
    def __init__(self):
        self.storage_dir = Path("./storage")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.separator = None

    def _load_ai_model(self):
        self.separator = Separator()
        self.separator.load_model(settings.separate_model)

    async def remove_instrumental(
        self, audio_bytes: bytes, filename: str
    ) -> io.BytesIO:
        if self.separator is None:
            await asyncio.to_thread(self._load_ai_model)

        safe_name = Path(filename).name or "upload"
        input_path = self.storage_dir / f"input_{safe_name}"

        async with aiofiles.open(input_path, "wb") as f:
            await f.write(audio_bytes)

        output_files = []
        try:
            output_files = await asyncio.to_thread(
                self.separator.separate, str(input_path)
            )

            vocal_filename = next(
                (f for f in output_files if "Vocals" in f), None
            )
            if vocal_filename is None:
                raise RuntimeError(
                    f"No vocal stem in separator output for {safe_name!r}. "
                    f"Got: {output_files}"
                )

            exported_io = io.BytesIO()
            async with aiofiles.open(Path(vocal_filename), "rb") as f:
                exported_io.write(await f.read())

        finally:
            input_path.unlink(missing_ok=True)
            for file in output_files:
                Path(file).unlink(missing_ok=True)

        exported_io.seek(0)
        return exported_io
