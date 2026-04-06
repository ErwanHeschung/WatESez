from pydantic import BaseModel
from typing import List

class LyricLine(BaseModel):
    start: float
    end: float
    text: str

class SongLyrics(BaseModel):
    song_metadata: dict = {}
    language: str
    lyrics: List[LyricLine]