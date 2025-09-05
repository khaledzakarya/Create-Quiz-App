from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    QUIZ_GENERATION_MODEL: str
    EMBEDDING_MODEL: str
    model_config = SettingsConfigDict(env_file=".env")


def get_settings():
    return Settings() 