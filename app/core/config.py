from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables.
    
    Manages database connections, API keys, and application behavior settings.
    """
    # Database
    database_url: str
    
    # Admin API Key
    admin_api_key: Optional[str] = None
    
    # External APIs
    sendgrid_api_key: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # App Settings
    app_name: str = "Kourts"
    debug: bool = False
    environment: str = "development"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )

settings = Settings()
