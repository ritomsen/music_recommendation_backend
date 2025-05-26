from typing import Dict, Optional
import os
import aiohttp
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
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    response.raise_for_status()
                    response = await response.json()
                    output = {
                        "isDaytime": response.get('isDaytime'),
                        "currentConditions": str(response.get('weatherCondition').get('description').get("text",'')),
                        "currentTemperature": str(response.get('feelsLikeTemperature').get('degrees','')) + " " + str(response.get('feelsLikeTemperature').get('unit','')) ,
                        "uvIndex": str(response.get('uvIndex', '')),
                        "relativeHumidity": str(response.get('relativeHumidity', '')),
                        "precipitationProbability": str(response.get('precipitation').get('probability').get('percent')) + " of " + str(response.get('precipitation').get('probability').get('type')),
                        "qpf": str(response.get('precipitation').get('qpf').get('quantity')) + " " + str(response.get('precipitation').get('qpf').get('unit')),
                        "thunderstormProbability": str(response.get('thunderstormProbability')),
                        "windGusts": str(response.get("wind").get("gust").get("value")) + " " + str(response.get("wind").get("gust").get("unit")),
                        "visibility": str(response.get("visibility").get("distance")) + " " + str(response.get("visibility").get("unit")),
                        "cloudCover": str(response.get("cloudCover", "")),
                    }
                    return output
            
        except aiohttp.ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch weather data: {str(e)}"
            )
