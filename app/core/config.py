from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://crm_user:crm_password@localhost:5432/crm_db"

    secret_key: str = "change-this-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    gemini_api_key: str = ""
    gemini_timeout_seconds: int = 25

    app_env: str = "development"

    admin_full_name: str = "Administrador"
    admin_email: str = "admin@crm.local"
    admin_password: str = "change-this-admin-password"


settings = Settings()
