from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    business_name: str = "O Meu Negócio"
    business_timezone: str = "Europe/Lisbon"
    business_phone: str = ""
    business_whatsapp: str = ""
    business_email: str = ""
    business_address: str = ""

    google_calendar_id: str = "primary"
    google_credentials_file: str = "credentials.json"
    google_token_file: str = "token.json"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5"

    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: str = "*"

    @property
    def origins_list(self) -> list[str]:
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
