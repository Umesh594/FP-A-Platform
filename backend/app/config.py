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

    # Salesforce enterprise integration
    SALESFORCE_BASE_URL: str = ""
    SALESFORCE_CLIENT_ID: str = ""
    SALESFORCE_CLIENT_SECRET: str = ""
    SALESFORCE_USERNAME: str = ""
    SALESFORCE_PASSWORD: str = ""
    SALESFORCE_SECURITY_TOKEN: str = ""
    SALESFORCE_API_VERSION: str = "v60.0"
    SALESFORCE_TIMEOUT_SECONDS: int = 15
    SALESFORCE_MOCK_MODE: bool = True

    # Oracle finance integration
    ORACLE_DSN: str = ""
    ORACLE_USERNAME: str = ""
    ORACLE_PASSWORD: str = ""
    ORACLE_SCHEMA: str = "FPNA"
    ORACLE_MOCK_MODE: bool = True
    ORACLE_TIMEOUT_SECONDS: int = 10

    # Emails
    CFO_EMAIL_TEMPLATE: str = ""
    WEEKLY_UPDATE_EMAIL: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
