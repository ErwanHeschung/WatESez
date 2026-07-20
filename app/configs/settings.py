from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    whisper_model: str = "large-v3-turbo"
    separate_model: str = "UVR-MDX-NET-Voc_FT.onnx"
    whisper_compute_type: str = "int8_float32"
    whisper_beam_size: int = 5
    whisper_language: str | None = None
    whisper_word_timestamps: bool = True
    whisper_min_avg_logprob: float = -1.0
    whisper_max_no_speech_prob: float = 0.6
    service_port: int = 8100
    service_host: str = "0.0.0.0"

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "watesez"
    db_user: str = "postgres"
    db_password: str = "postgres"

    audio_queue_max_size: int = 10

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()
