from typing import Dict, Optional
import os
import requests
from fastapi import HTTPException
from app.core.config import settings
class WeatherService:
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_KEY

        self.base_url = "https://weather.googleapis.com/v1/currentConditions:lookup"

    async def get_current_weather(self, latitude: float, longitude: float) -> Dict:
        """
        Fetch current weather conditions for a given location.
        
        Args:
            latitude (float): The latitude of the location
            longitude (float): The longitude of the location
            
        Returns:
            Dict: Current weather conditions
            
        Raises:
            HTTPException: If the API request fails
        """
        try:
            params = {
                "key": self.api_key,
                "location.latitude": latitude,
                "location.longitude": longitude
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch weather data: {str(e)}"
            )
