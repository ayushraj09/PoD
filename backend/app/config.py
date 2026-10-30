from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # the web app calls it NEXT_PUBLIC_SUPABASE_URL; accept either name
    supabase_url: str = Field("", validation_alias=AliasChoices("SUPABASE_URL",
                                                                "NEXT_PUBLIC_SUPABASE_URL"))
    supabase_service_role_key: str = ""
    web_origin: str = "http://localhost:3000"  # comma-separated list allowed
    ip_hash_salt: str = "dev-salt"

    stt_provider: str = "smallest"  # smallest | sarvam | openai (others are fallbacks)
    smallest_api_key: str = ""
    smallest_stt_model: str = "pulse"
    smallest_stt_language: str = "multi-indic"  # en + hi/gu/mr/bn/or auto-detect
    sarvam_api_key: str = ""
    openai_api_key: str = ""
    openai_transcribe_model: str = "gpt-4o-transcribe"
    llm_model: str = "gpt-5-nano"
    llm_reasoning_effort: str = "low"  # gpt-5 family; "low" scored 20/20 vs 17/20 for "minimal"

    voice_match_threshold: float = 0.6
    notify_webhook_url: str = ""

    tg_host: str = ""
    tg_graph: str = "pod"
    tg_secret: str = ""

    ffmpeg_bin: str = "ffmpeg"

    # intake
    max_audio_bytes: int = 3 * 1024 * 1024
    rate_limit_per_hour: int = 10
    check_email_dns: bool = True
    load_models: bool = True

    @property
    def web_origins(self) -> list[str]:
        # tolerate values pasted into a dashboard with quotes, spaces or a trailing slash
        cleaned = (o.strip().strip("'\"").strip().rstrip("/") for o in self.web_origin.split(","))
        return [o for o in cleaned if o]


@lru_cache
def get_settings() -> Settings:
    return Settings()
