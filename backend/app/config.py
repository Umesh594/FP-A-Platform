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

    # MySQL operational finance source
    MYSQL_HOST: str = "mysql"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "fpa_source"
    MYSQL_USERNAME: str = "fpa_reader"
    MYSQL_PASSWORD: str = ""
    MYSQL_MOCK_MODE: bool = True
    MYSQL_TIMEOUT_SECONDS: int = 10

    # Splunk HTTP Event Collector. Disabled until both values are configured.
    SPLUNK_HEC_URL: str = ""
    SPLUNK_HEC_TOKEN: str = ""
    SPLUNK_HEC_INDEX: str = "fpa-platform"

    # Network protocol diagnostics
    SMTP_HOST: str = "smtp.sendgrid.net"
    SMTP_PORT: int = 587
    SMTP_TLS_REQUIRED: bool = True
    NETWORK_DIAGNOSTICS_MOCK_MODE: bool = True

    # Emails
    CFO_EMAIL_TEMPLATE: str = ""
    WEEKLY_UPDATE_EMAIL: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
