from app.services.spotify_service import SpotifyService
from app.services.open_ai_service import OpenAIService
from app.services.weather_service import WeatherService
from app.services.genius_service import GeniusService
from app.services.shazam_service import ShazamService
from app.services.gemini_service import GeminiService
# Create shared instances of services
spotify_service = SpotifyService()
openai_service = OpenAIService()
weather_service = WeatherService()
genius_service = GeniusService() 
shazam_service = ShazamService()
gemini_service = GeminiService()