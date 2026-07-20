"""Domain exceptions.

Services raise these; the HTTP layer translates them to responses in
app.main. Keeping them framework-agnostic means the worker can catch the same
errors without importing anything from FastAPI.
"""


class WatESezError(Exception):
    """Base class for every error this application raises deliberately."""


class AudioDecodeError(WatESezError):
    """The upload could not be decoded to PCM."""


class FingerprintError(WatESezError):
    """No acoustic fingerprint could be derived from the audio."""


class SeparationError(WatESezError):
    """The separator produced no usable vocal stem."""


class QueueFullError(WatESezError):
    """Too many jobs are already pending."""

    def __init__(self, pending: int):
        self.pending = pending
        super().__init__(f"Processing queue is full ({pending} pending)")


class JobNotFoundError(WatESezError):
    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Job {job_id} not found")


class LyricsNotFoundError(WatESezError):
    def __init__(self, fingerprint: str):
        self.fingerprint = fingerprint
        super().__init__(f"No lyrics for fingerprint {fingerprint}")
