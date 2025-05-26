from abc import ABC, abstractmethod
from typing import Dict, Optional
from app.models.song import Pool_Song

class AIService(ABC):
    """Abstract base class for AI services"""
    
    def __init__(self, weather_data: Dict):
        self.weather_data = weather_data
    
    @abstractmethod
    async def analyze_image(self, image_data: bytes) -> Dict:
        """
        Analyze image and return musical aspects
        
        Returns:
            Dict containing:
            - mood: str
            - genre: str
            - energy_level: str
            - musical_characteristics: Dict
        """
        pass
    
    @abstractmethod
    async def analyze_audio(self, audio_data: bytes) -> Dict:
        """
        Analyze audio and return musical aspects
        
        Returns:
            Dict containing:
            - tempo: str
            - genre: str
            - energy_level: str
            - technical_details: Dict
        """
        pass
    
    @abstractmethod
    async def get_recommendation(
        self,
        song_1: Pool_Song,
        song_2: Pool_Song,
        user_context: str = "",
        image_analysis: Optional[Dict] = None
    ) -> int:
        """
        Get recommendation between two songs
        
        Args:
            song_1: First song to compare
            song_2: Second song to compare
            user_context: User preferences and context
            image_analysis: Optional image analysis results to consider in the comparison
            
        Returns:
            int: 0 for song_1 or 1 for song_2
        """
        pass 