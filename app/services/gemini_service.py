from typing import List, Optional, Dict
import os
from pathlib import Path
import google.generativeai as genai
from app.models.song import Pool_Song
from app.services.ai_service import AIService

class GeminiService(AIService):
    def __init__(self, weather_data: dict):
        super().__init__(weather_data)
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        
    def _load_prompt(self, prompt_file: str) -> str:
        """Load prompt template from file"""
        with open(self.prompts_dir / prompt_file, "r") as f:
            return f.read().strip()

    async def analyze_image(self, image_data: bytes) -> dict:
        """
        Analyze image using Gemini Vision API
        """
        prompt = self._load_prompt("image_analysis.txt")
        
        response = await self.vision_model.generate_content_async([
            prompt,
            {"mime_type": "image/jpeg", "data": image_data}
        ])
        
        analysis = response.text
        # Parse the analysis to extract mood and genre
        # This is a simplified version - you might want to add more sophisticated parsing
        return {
            "mood": "happy" if "happy" in analysis.lower() else "sad",
            "genre": "rock" if "rock" in analysis.lower() else "pop",
            "energy_level": "medium",
            "musical_characteristics": {}
        }

    async def analyze_audio(self, audio_data: bytes) -> dict:
        """
        Analyze audio using Gemini API
        Note: Gemini doesn't have direct audio analysis, so we'll use text analysis
        """
        prompt = self._load_prompt("audio_analysis.txt")
        
        # Since Gemini doesn't have direct audio analysis, we'll need to convert audio to text first
        # This is a placeholder - you'll need to implement audio transcription separately
        transcription = "Placeholder for audio transcription"
        
        response = await self.model.generate_content_async([
            prompt,
            transcription
        ])
        
        analysis = response.text
        # Parse the analysis to extract tempo and genre
        return {
            "tempo": "medium" if "medium" in analysis.lower() else "fast",
            "genre": "rock" if "rock" in analysis.lower() else "pop",
            "energy_level": "medium",
            "technical_details": {}
        }

    async def get_recommendation(
        self,
        song_1: Pool_Song,
        song_2: Pool_Song,
        user_context: str = "",
        image_analysis: Optional[Dict] = None
    ) -> int:
        """
        Get song recommendations based on analyzed features
        
        Args:
            song_1: First song to compare
            song_2: Second song to compare
            user_context: User preferences and context
            image_analysis: Optional image analysis results to consider
        """
        prompt_template = self._load_prompt("song_recommendation.txt")
        
        # Format the prompt with song details
        prompt = prompt_template.format(
            weather_data=str(self.weather_data),
            user_context=user_context,
            image_analysis=str(image_analysis) if image_analysis else "No visual context available",
            song1_title=song_1.title,
            song1_artist=song_1.artist,
            song1_genre=song_1.genre,
            song1_description=song_1.description,
            song1_popularity=song_1.popularity_score,
            song1_release_date=song_1.release_date,
            song2_title=song_2.title,
            song2_artist=song_2.artist,
            song2_genre=song_2.genre,
            song2_description=song_2.description,
            song2_popularity=song_2.popularity_score,
            song2_release_date=song_2.release_date
        )
        
        response = await self.model.generate_content_async([
            "You are a music recommendation expert.",
            prompt
        ])
        
        # Parse the response to get the recommendation (0 or 1)
        recommendation = response.text.strip()
        return 0 if "0" in recommendation else 1 