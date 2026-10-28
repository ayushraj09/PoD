from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    web_origin: str = "http://localhost:3000"  # comma-separated list allowed
    ip_hash_salt: str = "dev-salt"

    stt_provider: str = "sarvam"  # sarvam | openai
    sarvam_api_key: str = ""
    openai_api_key: str = ""
    openai_transcribe_model: str = "gpt-4o-transcribe"
    llm_model: str = "gpt-4o-mini"

    voice_match_threshold: float = 0.6
    notify_webhook_url: str = ""

    tg_host: str = ""
    tg_graph: str = "pod"
    tg_secret: str = ""

    # intake
    max_audio_bytes: int = 3 * 1024 * 1024
    rate_limit_per_hour: int = 10
    check_email_dns: bool = True
    load_models: bool = True

    @property
    def web_origins(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.web_origin.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
