import asyncio

# Set when a job is enqueued so the worker picks it up without waiting out its
# poll interval. Lives here rather than in audio_worker so the service layer
# can signal it without importing the worker (and vice versa).
job_available = asyncio.Event()
