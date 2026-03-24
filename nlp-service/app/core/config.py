from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "Meeting Transcript NLP Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8001
    WHISPER_MODEL: str = "base"          # tiny | base | small | medium
    SUMMARIZER_MODEL: str = "facebook/bart-large-cnn"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    SUMMARY_MAX_LENGTH: int = 300
    SUMMARY_MIN_LENGTH: int = 80

    class Config:
        env_file = ".env"


settings = Settings()
