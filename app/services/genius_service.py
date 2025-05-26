import asyncio
import lyricsgenius
from typing import Optional, Dict, Any
from ..core.config import settings

class GeniusService:
    def __init__(self):
        self.genius = lyricsgenius.Genius(settings.GENIUS_ACCESS_TOKEN)
        # Configure genius to skip non-songs and remove section headers
        self.genius.verbose = False
        self.genius.remove_section_headers = False
        self.genius.skip_non_songs = True
        self.genius.timeout = 0.5

    async def search_song(self, title: str, artist: str) -> Optional[Dict[str, Any]]:
        """
        Search for a song by title and artist.
        
        Args:
            title (str): The title of the song
            artist (str): The name of the artist
            
        Returns:
            Optional[Dict[str, Any]]: Song information if found, None otherwise
        """
        return {
                "lyrics": ""
            }
        #TODO FIGURE THIS OUT
        # try:
        #     song = await asyncio.to_thread(self.genius.search_song, title, artist, get_full_info=False)
        #     if song:
        #         return {
        #             "lyrics": song.lyrics
        #         }
        #     return None
        # except Exception as e:
        #     # print(f"GENIUS Error searching for song: {str(e)}")
        #     return {
        #         "lyrics": ""
        #     }


