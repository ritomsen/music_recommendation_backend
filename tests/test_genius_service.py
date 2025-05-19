import pytest
import os
from dotenv import load_dotenv
import sys
from pathlib import Path
import logging
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from app.services.genius_service import GeniusService

# Load environment variables
load_dotenv()
# Add the project root to Python path


@pytest.fixture
def genius_service():
    """Fixture to create a GeniusService instance for testing."""
    return GeniusService()

@pytest.mark.asyncio
async def test_search_song_success(genius_service):
    """Test successful song search with known song."""
    # Test with a well-known song that's likely to exist
    result = await genius_service.search_song("Egypt - Remix", "Westside Gunn")
    assert result is not None
    assert "lyrics" in result
    assert len(result["lyrics"]) > 0
    
    # Print the search results for inspection
    print("\nSearch Results:")
    print(f"Lyrics found: {len(result['lyrics'])} characters")
    print("\nFirst 500 characters of lyrics:")
    print(result['lyrics'][:500])

# @pytest.mark.asyncio
# async def test_search_song_not_found(genius_service):
#     """Test song search with non-existent song."""
#     # Test with a made-up song that shouldn't exist
#     result = await genius_service.search_song("ThisIsNotARealSong123", "FakeArtist123")
    
#     assert result is None

# @pytest.mark.asyncio
# async def test_get_lyrics_success(genius_service):
#     """Test successful lyrics retrieval for a known song."""
#     # First search for a song to get its ID
#     lyrics = await genius_service.search_song("Bohemian Rhapsody", "Queen")
#     assert lyrics is not None
#     print(lyrics)
#     # Then get lyrics using the song's ID
#     lyrics = lyrics['lyrics']
#     assert len(lyrics) > 0
#     assert "Is this the real life?" in lyrics or "Is this just fantasy?" in lyrics

# @pytest.mark.asyncio
# async def test_search_song_empty_input(genius_service):
#     """Test song search with empty input."""
#     result = await genius_service.search_song("", "")
    
#     assert result is None

# @pytest.mark.asyncio
# async def test_search_song_special_characters(genius_service):
#     """Test song search with special characters."""
#     result = await genius_service.search_song("Hey Jude!", "The Beatles")
    
#     assert result is not None
#     assert "lyrics" in result
#     assert len(result["lyrics"]) > 0 