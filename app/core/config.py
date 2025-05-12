from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Music Recommendation API"
    
    # Add your API keys and other configuration here
    # OPENAI_API_KEY: str = ""
    
    class Config:
        case_sensitive = True

settings = Settings() 