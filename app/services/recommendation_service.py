from typing import List
from app.models.song import SongResponse

class RecommendationService:
    # Mock data for demonstration
    MOCK_SONGS = [
        {
            "title": "Bohemian Rhapsody",
            "artist": "Queen",
            "album": "A Night at the Opera",
            "spotify_link": "https://open.spotify.com/track/6l8GvAyoUZwWDgF1e4822w",
            "img_link": "https://i.scdn.co/image/ab67616d0000b273e8b066f70c206551210d902b"
        },
        {
            "title": "Stairway to Heaven",
            "artist": "Led Zeppelin",
            "album": "Led Zeppelin IV",
            "spotify_link": "https://open.spotify.com/track/5CQ30WqJwcep0pYcV4AMNc",
            "img_link": "https://i.scdn.co/image/ab67616d0000b273c6f7af36bcd24e41e925c5e5"
        },
        {
            "title": "Hotel California",
            "artist": "Eagles",
            "album": "Hotel California",
            "spotify_link": "https://open.spotify.com/track/40riOy7x9W7GXjyGp4pjAv",
            "img_link": "https://i.scdn.co/image/ab67616d0000b273d8f4982e8a73c3a2f7b0b5c7"
        }
    ]

    @staticmethod
    def get_mock_recommendations() -> List[SongResponse]:
        """
        Return mock song recommendations
        """
        return [SongResponse(**song) for song in RecommendationService.MOCK_SONGS] 