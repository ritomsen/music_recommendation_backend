import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path
import json

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.rec_service.candidate_pool import CandidatePool
from app.models.song import Pool_Song, SpotifySong, ShazamSong, SpotifyArtist

class TestCandidatePool(unittest.TestCase):
    def setUp(self):
        # Create mock instances for services
        self.mock_shazam = Mock()
        self.mock_spotify = Mock()
        self.mock_ai = Mock()
        
        # Patch the service classes to return our mocks
        self.shazam_patcher = patch('app.rec_service.candidate_pool.ShazamService')
        self.spotify_patcher = patch('app.rec_service.candidate_pool.SpotifyService')
        self.ai_patcher = patch('app.rec_service.candidate_pool.AIService')
        
        self.mock_shazam_service = self.shazam_patcher.start()
        self.mock_spotify_service = self.spotify_patcher.start()
        self.mock_ai_service = self.ai_patcher.start()
        
        # Set the mock instances to be returned when the classes are instantiated
        self.mock_shazam_service.return_value = self.mock_shazam
        self.mock_spotify_service.return_value = self.mock_spotify
        self.mock_ai_service.return_value = self.mock_ai
        
        # Initialize CandidatePool with test data
        self.genres = ["pop", "rock"]
        self.location = "US"
        self.session_id = "test_session_123"
        self.candidate_pool = CandidatePool(self.genres, self.location, self.session_id)
        
    def tearDown(self):
        # Stop the patchers
        self.shazam_patcher.stop()
        self.spotify_patcher.stop()
        self.ai_patcher.stop()
    
    def _create_mock_spotify_song(self, title="Test Song", artist="Test Artist"):
        """Helper method to create a mock Spotify song"""
        return SpotifySong(
            title=title,
            artist=artist,
            album="Test Album",
            img_link="https://example.com/image.jpg",
            popularity_score=80,
            duration_ms=240000,  # 4 minutes
            spotify_id="test123",
            spotify_link="https://open.spotify.com/track/test123",
            release_date="2023-01-01"
        )
    
    def _create_mock_shazam_song(self, genre="pop"):
        """Helper method to create a mock Shazam song"""
        return ShazamSong(
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            genre=genre,
            key="12345",
            img_link="https://example.com/image.jpg",
            release_date="2023-01-01"
        )
    
    def _setup_mock_shazam_search(self, genre="pop"):
        """Setup mock Shazam search response"""
        mock_shazam_song = self._create_mock_shazam_song(genre)
        self.mock_shazam.search_and_get_song_details.return_value = mock_shazam_song
        return mock_shazam_song
        
    def test_add_top_user_artists_tracks(self):
        # Setup mock data
        mock_artist1 = SpotifyArtist(
            name="Artist 1",
            genres=["pop"],
            popularity_score=90,
            id="artist1"  # Add ID for artist
        )
        mock_artist2 = SpotifyArtist(
            name="Artist 2",
            genres=["metal"],  # This genre should not match
            popularity_score=85,
            id="artist2"  # Add ID for artist
        )
        
        # Setup mock top tracks for artists
        mock_track1 = self._create_mock_spotify_song("Song 1", "Artist 1")
        mock_track2 = self._create_mock_spotify_song("Song 2", "Artist 1")
        
        # Setup mock responses
        self.mock_spotify.get_user_top_artists.return_value = [mock_artist1, mock_artist2]
        self.mock_spotify.get_artist_top_tracks.return_value = [mock_track1, mock_track2]
        
        # Setup Shazam response
        self._setup_mock_shazam_search("pop")
        
        # Call the method
        self.candidate_pool.add_top_user_artists_tracks()
        
        # Verify the results
        self.assertEqual(len(self.candidate_pool.pool), 2)
        self.assertEqual(self.candidate_pool.pool[0].title, "Song 1")
        self.assertEqual(self.candidate_pool.pool[0].comes_from, "top_artists")
        self.assertEqual(self.candidate_pool.pool[1].title, "Song 2")
        
        # Verify that only the artist with matching genre was used
        self.mock_spotify.get_artist_top_tracks.assert_called_once_with(self.session_id, "artist1")
    
    def test_add_top_user_tracks(self):
        # Setup mock data
        mock_track1 = self._create_mock_spotify_song("Top Track 1", "Top Artist 1")
        mock_track2 = self._create_mock_spotify_song("Top Track 2", "Top Artist 2")
        
        # Setup mock responses
        self.mock_spotify.get_user_top_tracks.return_value = [mock_track1, mock_track2]
        
        # Setup Shazam response
        self._setup_mock_shazam_search("pop")
        
        # Call the method
        self.candidate_pool.add_top_user_tracks()
        
        # Verify the results
        self.assertEqual(len(self.candidate_pool.pool), 2)
        self.assertEqual(self.candidate_pool.pool[0].title, "Top Track 1")
        self.assertEqual(self.candidate_pool.pool[0].comes_from, "top_tracks")
        self.assertEqual(self.candidate_pool.pool[1].title, "Top Track 2")
        
        # Verify session_id was passed
        self.mock_spotify.get_user_top_tracks.assert_called_once_with(self.session_id)
    
    def test_add_recently_played_tracks(self):
        # Setup mock data
        mock_track1 = self._create_mock_spotify_song("Recent Track 1", "Recent Artist 1")
        mock_track2 = self._create_mock_spotify_song("Recent Track 2", "Recent Artist 2")
        
        # Setup mock responses
        self.mock_spotify.get_user_recently_played.return_value = [mock_track1, mock_track2]
        
        # Setup Shazam response
        self._setup_mock_shazam_search("rock")
        
        # Call the method
        self.candidate_pool.add_recently_played_tracks()
        
        # Verify the results
        self.assertEqual(len(self.candidate_pool.pool), 2)
        self.assertEqual(self.candidate_pool.pool[0].title, "Recent Track 1")
        self.assertEqual(self.candidate_pool.pool[0].comes_from, "recently_played")
        self.assertEqual(self.candidate_pool.pool[1].title, "Recent Track 2")
        
        # Verify that session_id was passed
        self.mock_spotify.get_user_recently_played.assert_called_once_with(self.session_id)
    
    def test_add_saved_tracks(self):
        # Setup mock data
        mock_track1 = self._create_mock_spotify_song("Saved Track 1", "Saved Artist 1")
        mock_track2 = self._create_mock_spotify_song("Saved Track 2", "Saved Artist 2")
        
        # Setup mock responses
        self.mock_spotify.get_user_saved_tracks.return_value = [mock_track1, mock_track2]
        
        # Setup Shazam response
        self._setup_mock_shazam_search()
        
        # Call the method
        self.candidate_pool.add_saved_tracks()
        
        # Verify the results
        self.assertEqual(len(self.candidate_pool.pool), 2)
        self.assertEqual(self.candidate_pool.pool[0].title, "Saved Track 1")
        self.assertEqual(self.candidate_pool.pool[0].comes_from, "saved_tracks")
        self.assertEqual(self.candidate_pool.pool[1].title, "Saved Track 2")
        
        # Verify that session_id was passed
        self.mock_spotify.get_user_saved_tracks.assert_called_once_with(self.session_id)
    
    def test_add_saved_album_tracks(self):
        # Setup mock data
        mock_track1 = self._create_mock_spotify_song("Album Track 1", "Album Artist 1")
        mock_track2 = self._create_mock_spotify_song("Album Track 2", "Album Artist 2")
        
        # Setup mock responses
        self.mock_spotify.get_user_saved_albums.return_value = [mock_track1, mock_track2]
        
        # Setup Shazam response
        self._setup_mock_shazam_search()
        
        # Call the method
        self.candidate_pool.add_saved_album_tracks()
        
        # Verify the results
        self.assertEqual(len(self.candidate_pool.pool), 2)
        self.assertEqual(self.candidate_pool.pool[0].title, "Album Track 1")
        self.assertEqual(self.candidate_pool.pool[0].comes_from, "saved_albums")
        self.assertEqual(self.candidate_pool.pool[1].title, "Album Track 2")
        
        # Verify that session_id was passed
        self.mock_spotify.get_user_saved_albums.assert_called_once_with(self.session_id)
    
    def test_check_genre_match(self):
        # Test exact match
        self.assertTrue(self.candidate_pool.check_genre_match(["pop"]))
        
        # Test substring match
        self.assertTrue(self.candidate_pool.check_genre_match(["pop rock"]))
        self.assertTrue(self.candidate_pool.check_genre_match(["indie rock"]))
        
        # Test no match
        self.assertFalse(self.candidate_pool.check_genre_match(["metal"]))
        self.assertFalse(self.candidate_pool.check_genre_match(["jazz"]))
    
    def test_all_methods_together(self):
        # Setup mock data for different sources
        # Top artists
        mock_artist = SpotifyArtist(
            name="Artist", 
            genres=["pop"], 
            popularity_score=90,
            id="artist1"
        )
        artist_track = self._create_mock_spotify_song("Artist Top Track", "Artist")
        
        # Top tracks
        top_track = self._create_mock_spotify_song("User Top Track", "Top Artist")
        
        # Recent tracks
        recent_track = self._create_mock_spotify_song("Recent Track", "Recent Artist")
        
        # Saved tracks
        saved_track = self._create_mock_spotify_song("Saved Track", "Saved Artist")
        
        # Saved albums
        album_track = self._create_mock_spotify_song("Album Track", "Album Artist")
        
        # Setup mock responses
        self.mock_spotify.get_user_top_artists.return_value = [mock_artist]
        self.mock_spotify.get_artist_top_tracks.return_value = [artist_track]
        self.mock_spotify.get_user_top_tracks.return_value = [top_track]
        self.mock_spotify.get_user_recently_played.return_value = [recent_track]
        self.mock_spotify.get_user_saved_tracks.return_value = [saved_track]
        self.mock_spotify.get_user_saved_albums.return_value = [album_track]
        
        # Setup Shazam response
        self._setup_mock_shazam_search()
        
        # Call all methods
        self.candidate_pool.add_top_user_artists_tracks()
        self.candidate_pool.add_top_user_tracks()
        self.candidate_pool.add_recently_played_tracks()
        self.candidate_pool.add_saved_tracks()
        self.candidate_pool.add_saved_album_tracks()
        
        # Verify the results
        self.assertEqual(len(self.candidate_pool.pool), 5)
        
        # Verify we have songs from each source
        sources = set(song.comes_from for song in self.candidate_pool.pool)
        expected_sources = {"top_artists", "top_tracks", "recently_played", "saved_tracks", "saved_albums"}
        self.assertEqual(sources, expected_sources)

if __name__ == "__main__":
    unittest.main() 