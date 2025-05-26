import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.models.song import Pool_Song
from app.services.open_ai_service import OpenAIService

# Sample Pool_Song objects for testing
song1 = Pool_Song(
    id="1",
    title="Song One",
    artist="Artist A",
    album="Album X",
    genre="Pop",
    year=2020,
    duration_ms=180000,
    image_url="http://example.com/image1.jpg",
    preview_url="http://example.com/preview1.mp3",
    spotify_id="spotify1",
    lyrics="Lyrics for song one",
    description="Description for song one",
    reason_for_addition="Reason one",
    track_number=1,
    disc_number=1,
    explicit=False,
    popularity_score=80,
    release_date="2020-01-01"
)

song2 = Pool_Song(
    id="2",
    title="Song Two",
    artist="Artist B",
    album="Album Y",
    genre="Rock",
    year=2021,
    duration_ms=200000,
    image_url="http://example.com/image2.jpg",
    preview_url="http://example.com/preview2.mp3",
    spotify_id="spotify2",
    lyrics="Lyrics for song two",
    description="Description for song two",
    reason_for_addition="Reason two",
    track_number=1,
    disc_number=1,
    explicit=True,
    popularity_score=70,
    release_date="2021-01-01"
)

# Sample prompt template
PROMPT_TEMPLATE = """
Weather: {{ "temp": "20C" }}
User: {{ "preference": "upbeat" }}
Image: {{ "mood": "happy" }}
Audio: {{ "tempo": "fast" }}
Compare:
Song 1: {song1_title} by {song1_artist} ({song1_genre}) - Popularity: {song1_popularity}, Released: {song1_release_date}, Desc: {song1_description}
Song 2: {song2_title} by {song2_artist} ({song2_genre}) - Popularity: {song2_popularity}, Released: {song2_release_date}, Desc: {song2_description}
Which is better?
"""

@pytest.fixture
def open_ai_service_mock():
    service = OpenAIService()
    service.client = AsyncMock()  # Mock the AsyncOpenAI client
    return service

@pytest.mark.asyncio
async def test_get_recommendation_song1_wins(open_ai_service_mock):
    # Mock the API response for song1 winning
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = '''{
        "comparison": {
            "song1_analysis": "Great beat",
            "song2_analysis": "A bit slow",
            "overall_winner": "song1",
            "key_differentiators": ["tempo"],
            "recommendation_reason": "Song 1 is more upbeat and fits the happy mood."
        }
    }'''
    open_ai_service_mock.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await open_ai_service_mock.get_recommendation(song1, song2, PROMPT_TEMPLATE)
    assert result == 0
    open_ai_service_mock.client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_get_recommendation_song2_wins(open_ai_service_mock):
    # Mock the API response for song2 winning
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = '''{
        "comparison": {
            "song1_analysis": "Okay",
            "song2_analysis": "Excellent vocals",
            "overall_winner": "song2",
            "key_differentiators": ["vocals"],
            "recommendation_reason": "Song 2 has superior vocal performance."
        }
    }'''
    open_ai_service_mock.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await open_ai_service_mock.get_recommendation(song1, song2, PROMPT_TEMPLATE)
    assert result == 1
    open_ai_service_mock.client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_get_recommendation_fallback_parsing_song1_in_reason(open_ai_service_mock):
    # Mock API response where winner is not explicitly "song1" or "song2", but "song1" is in the reason
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    # Malformed JSON to trigger fallback
    mock_response.choices[0].message.content = '''{
        "comparison": {
            "overall_winner": "unknown", 
            "recommendation_reason": "We think song1 is better due to its rhythm."
        }
    }''' # Note: missing closing brace for "comparison" to make it invalid JSON for this test case
    open_ai_service_mock.client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # To make the JSON truly invalid for testing the fallback, let's ensure it *will* cause a JSONDecodeError
    # by providing something that is not valid JSON at all for the content,
    # but still contains the keyword for the fallback logic.
    # The above structure might still be parsable up to a point or by lenient parsers.

    # Simulate a real JSONDecodeError by providing truly malformed JSON
    mock_response_invalid_json = MagicMock()
    mock_response_invalid_json.choices = [MagicMock()]
    mock_response_invalid_json.choices[0].message = MagicMock()
    mock_response_invalid_json.choices[0].message.content = "This is not JSON, but song1 is preferred." # Fallback will catch "song1"
    
    open_ai_service_mock.client.chat.completions.create = AsyncMock(return_value=mock_response_invalid_json)


    result = await open_ai_service_mock.get_recommendation(song1, song2, PROMPT_TEMPLATE)
    assert result == 0 # Fallback should pick song1 based on "song1" in reason

@pytest.mark.asyncio
async def test_get_recommendation_fallback_parsing_json_decode_error(open_ai_service_mock):
    # Mock API response that causes JSONDecodeError
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "This is not valid JSON. Prefer song2." # Fallback will pick song2
    open_ai_service_mock.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await open_ai_service_mock.get_recommendation(song1, song2, PROMPT_TEMPLATE)
    assert result == 1 # Fallback should pick song2
    open_ai_service_mock.client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_get_recommendation_no_explicit_winner_song1_in_reason(open_ai_service_mock):
    # Mock the API response where "overall_winner" is not "song1" or "song2"
    # but the reason implies song1
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = '''{
        "comparison": {
            "song1_analysis": "Good",
            "song2_analysis": "Also good",
            "overall_winner": "neither", 
            "recommendation_reason": "Leaning towards song1 for its unique style."
        }
    }'''
    open_ai_service_mock.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await open_ai_service_mock.get_recommendation(song1, song2, PROMPT_TEMPLATE)
    assert result == 0 # Should choose song1 based on reason
    open_ai_service_mock.client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_get_recommendation_no_explicit_winner_song2_in_reason(open_ai_service_mock):
    # Mock the API response where "overall_winner" is not "song1" or "song2"
    # but the reason implies song2
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = '''{
        "comparison": {
            "song1_analysis": "Good",
            "song2_analysis": "Also good",
            "overall_winner": "tie", 
            "recommendation_reason": "song2 is a slightly better fit for the current mood."
        }
    }'''
    open_ai_service_mock.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await open_ai_service_mock.get_recommendation(song1, song2, PROMPT_TEMPLATE)
    assert result == 1 # Should choose song2 based on reason
    open_ai_service_mock.client.chat.completions.create.assert_called_once()

# To run these tests, navigate to your project's root directory and run:
# PYTHONPATH=. pytest music_recommendation_backend/tests/test_open_ai_service.py 