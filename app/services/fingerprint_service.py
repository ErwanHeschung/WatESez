import asyncio
import hashlib

import chromaprint

from app.exceptions import AudioDecodeError, FingerprintError

SAMPLE_RATE = 44100
CHANNELS = 1


class FingerprintService:
    """Derives a stable identifier for a track from its acoustic content.

    Split out of AudioService: decoding audio and hashing it is a distinct
    concern from orchestrating the transcription pipeline, and it is the only
    part that needs ffmpeg and chromaprint.
    """

    async def generate(self, audio_bytes: bytes) -> str:
        pcm_data = await self._decode_to_pcm(audio_bytes)
        return self._fingerprint_pcm(pcm_data)

    @staticmethod
    async def _decode_to_pcm(audio_bytes: bytes) -> bytes:
        process = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-i",
            "pipe:0",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            str(CHANNELS),
            "-f",
            "s16le",
            "pipe:1",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        pcm_data, stderr = await process.communicate(input=audio_bytes)

        if process.returncode != 0:
            detail = stderr.decode(errors="replace").strip().splitlines()
            raise AudioDecodeError(
                f"ffmpeg could not decode the upload: {detail[-1] if detail else ''}"
            )

        return pcm_data

    @staticmethod
    def _fingerprint_pcm(pcm_data: bytes) -> str:
        fp = chromaprint.Fingerprinter()
        fp.start(SAMPLE_RATE, CHANNELS)
        fp.feed(pcm_data)
        raw_fingerprint = fp.finish()

        if not raw_fingerprint:
            raise FingerprintError("chromaprint produced an empty fingerprint")

        return hashlib.sha256(raw_fingerprint).hexdigest()
