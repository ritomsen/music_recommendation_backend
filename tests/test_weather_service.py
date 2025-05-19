import pytest
from unittest.mock import patch, Mock
import sys
from pathlib import Path
import json
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)
from app.services.weather_service import WeatherService

@pytest.fixture
def weather_service():
    return WeatherService()

@pytest.mark.asyncio
async def test_get_current_weather_success(weather_service):
    # Example coordinates for San Francisco
    latitude = 37.7749
    longitude = -122.4194
    # Mock the requests.get method
    result = await weather_service.get_current_weather(latitude, longitude)
    assert result is not None
    print(json.dumps(result, indent=4))

