from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    whisper_model: str
    separate_model: str
    service_port: int
    service_host: str
    
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    
    audio_queue_max_size: int
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    model_config = SettingsConfigDict(env_file=".env",extra="ignore")

settings = Settings()