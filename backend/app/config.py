from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Autonomous FP&A Platform"
    DATABASE_URL: str
    REDIS_URL: str
    GROQ_API_KEY: str | None = None
    SENDGRID_API_KEY: str | None = None
    DEFAULT_EMAIL_SENDER: str = ""
    FORECAST_MONTHS: int = 12
    KPI_ALERT_THRESHOLD: float = 0.10
    API_KEY: str | None = None
    ENABLE_API_SCHEDULER: bool = False

    # Emails
    CFO_EMAIL_TEMPLATE: str = ""
    WEEKLY_UPDATE_EMAIL: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
