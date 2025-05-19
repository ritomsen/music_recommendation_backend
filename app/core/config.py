from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Music Recommendation API"
    
    # Spotify credentials
    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str
    SPOTIFY_REDIRECT_URI: str
    FRONTEND_URL: str = "http://localhost:3000"
    
    # OpenAI credentials
    OPENAI_API_KEY: str | None = None
    
    # Add your API keys and other configuration here
    GENIUS_ACCESS_TOKEN: str
    GOOGLE_MAPS_KEY: str
    
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow"  # Allow extra fields in environment variables
    )

settings = Settings() 