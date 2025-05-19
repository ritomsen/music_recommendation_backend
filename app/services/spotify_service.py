from typing import List, Dict, Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from app.core.config import settings
import json
import os
import uuid
import random
import math

from app.models.song import SpotifyArtist, SpotifySong

class SpotifyService:
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = settings.SPOTIFY_REDIRECT_URI
        self.scope = "user-read-private user-read-email user-top-read user-read-recently-played user-library-read"
        self.cache_path = "spotify_cache"
        self.user_tokens = {}  # Store tokens for multiple users

    def _get_auth_manager(self, state=None):
        """Create a SpotifyOAuth auth manager with the given state"""
        return SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            state=state,
            cache_path=None  # We'll manage our own token storage
        )

    def get_auth_url(self) -> Dict[str, str]:
        """Generate a Spotify authorization URL with state parameter"""
        state = str(uuid.uuid4())
        auth_manager = self._get_auth_manager(state)
        auth_url = auth_manager.get_authorize_url(state=state)
        return {"auth_url": auth_url, "state": state}

    def get_access_token(self, code: str, state: str) -> Dict:
        """Exchange authorization code for access token"""
        auth_manager = self._get_auth_manager(state)
        token_info = auth_manager.get_access_token(code)
        
        # Generate a session id for this user
        session_id = str(uuid.uuid4())
        
        # Store token info with session id
        self.user_tokens[session_id] = {
            "token_info": token_info,
        }
        
        return {"session_id": session_id}

    def get_user_spotify_client(self, session_id: str) -> Optional[spotipy.Spotify]:
        """Get a spotipy client for the user with the given session_id"""
        if session_id not in self.user_tokens:
            return None
            
        token_info = self.user_tokens[session_id]["token_info"]
        auth_manager = self._get_auth_manager()
        
        # Let spotipy handle token validation and refresh
        if not self.validate_token(session_id):
            if "refresh_token" in token_info:
                token_info = auth_manager.refresh_access_token(token_info["refresh_token"])
                self.user_tokens[session_id]["token_info"] = token_info
            else:
                print("ERROR: No refresh token found")
                return None
        # Create a client with the user's access token
        return spotipy.Spotify(auth=token_info["access_token"])

    def clear_user_token(self, session_id: str) -> bool:
        """Remove a user's token from storage"""
        if session_id in self.user_tokens:
            del self.user_tokens[session_id]
            return True
        return False
        
    def validate_token(self, session_id: str) -> bool:
        """Validate if a user's token is still valid"""
        if session_id not in self.user_tokens:
            return False
            
        token_info = self.user_tokens[session_id]["token_info"]
        auth_manager = self._get_auth_manager()
        
        # Use spotipy's built-in token validation
        return auth_manager.validate_token(token_info)
   

    def get_user_top_tracks(self, session_id: str, time_range: str = "medium_term") -> List[Dict]:
        """Get a user's top tracks"""
        spotify = self.get_user_spotify_client(session_id)
        if not spotify:
            return []
        
        track_results = spotify.current_user_top_tracks(time_range=time_range, limit=50)
        results = []
        for track in track_results['items']:
            # Default image if none available
            img_url = "https://via.placeholder.com/300"
            # Get image if available
            if track['album']['images'] and len(track['album']['images']) > 0:
                img_url = track['album']['images'][0]['url']

            song = SpotifySong(
                title=track['name'],
                artist=track['artists'][0]['name'],
                album=track['album']['name'],
                img_link=img_url, # 300x300
                popularity_score=track['popularity'],
                duration_ms=track['duration_ms'],
                spotify_id=track['id'],
                spotify_link=track['external_urls']['spotify'],
                release_date=track['album']['release_date']
            )
            results.append(song)
        return results

    def get_user_top_artists(self, session_id: str, time_range: str = "medium_term") -> List[Dict]:
        """Get a user's top artists"""
        spotify = self.get_user_spotify_client(session_id)
        if not spotify:
            return []
        
        top_artists = spotify.current_user_top_artists(limit=20, time_range=time_range)
        results = []
        for artist in top_artists['items']:
            artist = SpotifyArtist(
                name=artist['name'],
                genres=artist['genres'],
                popularity_score=artist['popularity'],
                artist_id=artist['id']
            )
            results.append(artist)
        return results
    
    def get_artist_top_tracks(self, session_id: str, artist_id: str) -> List[Dict]:
        """Get a user's top tracks"""
        spotify = self.get_user_spotify_client(session_id)
        if not spotify:
            return []
        
        top_tracks = spotify.artist_top_tracks(artist_id)
        results = []
        for track in top_tracks['tracks']:
            # Default image if none available
            img_url = "https://via.placeholder.com/300"
            # Get image if available
            if track['album']['images'] and len(track['album']['images']) > 0:
                img_url = track['album']['images'][0]['url']
                
            song = SpotifySong(
                title=track['name'],
                artist=track['artists'][0]['name'],
                album=track['album']['name'],
                img_link=img_url, # 300x300
                popularity_score=track['popularity'],
                duration_ms=track['duration_ms'],
                spotify_id=track['id'],
                spotify_link=track['external_urls']['spotify'],
                release_date=track['album']['release_date']
            )
            results.append(song)
        return results

    def get_user_recently_played(self, session_id: str) -> List[Dict]:
        """Get a user's recently played tracks"""
        spotify = self.get_user_spotify_client(session_id)
        if not spotify:
            return []
        recently_played = spotify.current_user_recently_played(limit=30)
        results = []
        for item in recently_played['items']:
            # Default image if none available
            img_url = "https://via.placeholder.com/300"
            # Get image if available
            if item['track']['album']['images'] and len(item['track']['album']['images']) > 0:
                img_url = item['track']['album']['images'][0]['url']
                
            song = SpotifySong(
                title=item['track']['name'],
                artist=item['track']['artists'][0]['name'],
                album=item['track']['album']['name'],
                img_link=img_url, # 300x300
                popularity_score=item['track']['popularity'],
                duration_ms=item['track']['duration_ms'],
                spotify_id=item['track']['id'],
                spotify_link=item['track']['external_urls']['spotify'],
                release_date=item['track']['album']['release_date']
            )
            results.append(song)
        return results
    
    def get_user_saved_tracks(self, session_id: str) -> List[Dict]:
        """Get a user's saved tracks with stratified random sampling"""
        spotify = self.get_user_spotify_client(session_id)
        if not spotify:
            return []
            
        # Get initial batch to determine total count
        saved_tracks = spotify.current_user_saved_tracks(limit=50)
        total_saved_tracks = saved_tracks['total']
        
        # Calculate the size of each third
        third_size = total_saved_tracks // 3
        first_third_end = third_size
        second_third_end = third_size * 2
        
        # Calculate how many tracks to fetch from each third
        first_third_sample_size = min(int(third_size * 0.2), 100)  # 20% of first third, max 100
        second_third_sample_size = min(int(third_size * (1/3)), 165)  # 1/3 of second third, max 165
        last_third_sample_size = min(int(third_size * (1/3)), 165)  # 1/3 of last third, max 165
        
        # Get all saved tracks (with pagination)
        all_tracks = []
        offset = 0
        limit = 50  # Spotify API limit
        
        while offset < total_saved_tracks:
            batch = spotify.current_user_saved_tracks(limit=limit, offset=offset)
            all_tracks.extend(batch['items'])
            offset += limit
            # Break if we've fetched all tracks or if this is just for testing
            if len(batch['items']) < limit:
                break
        
        # Split tracks into three parts
        first_third = all_tracks[:first_third_end] 
        second_third = all_tracks[first_third_end:second_third_end] 
        last_third = all_tracks[second_third_end:]
        
        # Sample from each third
        sampled_first_third = random.sample(first_third, min(first_third_sample_size, len(first_third))) 
        sampled_second_third = random.sample(second_third, min(second_third_sample_size, len(second_third))) 
        sampled_last_third = random.sample(last_third, min(last_third_sample_size, len(last_third)))
        
        # Combine samples
        sampled_tracks = sampled_first_third + sampled_second_third + sampled_last_third
        
        # Convert to SpotifySong objects
        results = []
        for track in sampled_tracks:
            # Default image if none available
            img_url = "https://via.placeholder.com/300"
            # Get image if available
            if track['track']['album']['images'] and len(track['track']['album']['images']) > 0:
                img_url = track['track']['album']['images'][0]['url']
                
            song = SpotifySong(
                title=track['track']['name'],
                artist=track['track']['artists'][0]['name'],
                album=track['track']['album']['name'],
                img_link=img_url, # 300x300
                popularity_score=track['track']['popularity'],
                duration_ms=track['track']['duration_ms'],
                spotify_id=track['track']['id'],
                spotify_link=track['track']['external_urls']['spotify'],
                release_date=track['track']['album']['release_date']
            )
            results.append(song)
            
        return results
    
    def get_user_saved_albums(self, session_id: str) -> List[Dict]:
        """Get a user's saved albums"""
        spotify = self.get_user_spotify_client(session_id)
        if not spotify:
            return []
        
        saved_albums = spotify.current_user_saved_albums(limit=5)
        results = []
        for album in saved_albums['items']:
            for track in album['album']['tracks']['items']:
                # Default image if none available
                img_url = "https://via.placeholder.com/300"
                # Get image if available
                if album['album']['images'] and len(album['album']['images']) > 0:
                    img_url = album['album']['images'][0]['url']
                    
                song = SpotifySong(
                    title=track['name'],
                    artist=track['artists'][0]['name'],
                    album=album['album']['name'],
                    img_link=img_url, # 300x300
                    popularity_score=album['album']['popularity'],
                    duration_ms=track['duration_ms'],
                    spotify_id=track['id'],
                    spotify_link=track['external_urls']['spotify'],
                    release_date=album['album']['release_date']
                )
                results.append(song)
        return results
