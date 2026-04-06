import uuid
from pydantic import BaseModel, Field
from typing import List

class LyricLine(BaseModel):
    start: float
    end: float
    text: str

class SongLyrics(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    song_metadata: dict = {}
    language: str
    lyrics: List[LyricLine]