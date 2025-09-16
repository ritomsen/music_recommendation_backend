from typing import List, Dict, Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from app.core.config import settings
import json
import os
import uuid
import random
import math
import asyncio

from app.models.song import SpotifyArtist, Pool_Song
from urllib.parse import urlparse


MAX_LIMIT = 50
class SpotifyService:
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = settings.SPOTIFY_REDIRECT_URI
        self.scope = "user-read-private user-read-email user-top-read user-read-recently-played user-library-read user-modify-playback-state"
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
            print("Token is invalid, refreshing")
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

    async def get_user_top_tracks(self, session_id: str, time_range: str = "medium_term", limit: int = 50, album_mode: bool = False, num_albums: int = 2) -> List[Dict]:
        """Get a user's top tracks"""
        print("Getting user top tracks")
        spotify = self.get_user_spotify_client(session_id)
        if not spotify:
            print("No spotify client found")
            return []
        print("Got Spotify Client")
        
        # Use asyncio.to_thread for the blocking API call
        track_results = await asyncio.to_thread(
            spotify.current_user_top_tracks,
            time_range=time_range,
            limit=MAX_LIMIT
        )
        if limit < MAX_LIMIT and len(track_results['items']) >= limit:
            sampled_tracks = random.sample(track_results['items'], limit)
        else:
            sampled_tracks = track_results['items']
        
        # print("Got Top Tracks", json.dumps(track_results['items'], indent=4), len(sampled_tracks))
        results = []
        for track in sampled_tracks:
            # Default image if none available
            img_url = "https://via.placeholder.com/300"
            # Get image if available
            if track['album']['images'] and len(track['album']['images']) > 0:
                img_url = track['album']['images'][0]['url']
            artist = ""

            for a in track['artists']:
                artist += a['name'] + ", "
            artist = artist[:-2]

            song = Pool_Song(
                title=track['name'],
                artist=artist,
                album=track['album']['name'],
                img_link=img_url, # 300x300
                popularity_score=track['popularity'],
                duration_ms=track['duration_ms'],
                spotify_link=track['external_urls']['spotify'],
                release_date=track['album']['release_date'],
                genre="",
                lyrics=""
            )
            results.append(song)
        # print("Top Tracks without albums", results)
        if album_mode:
            print("Getting Albums from sampled tracks Album Mode On")
            album_ids = set()
            sampled_album_ids = track_results['items'] #HYPERPARAMETER
            random.shuffle(sampled_album_ids)
            ## GETTING Album of sampled tracks
            ## MAKE SURE I AM NOT ADDING DUPLICATE TRACKS
            print("Getting Albums from sampled tracks")
            for album_id in sampled_album_ids:
                if album_id['album']['album_type'] == "album":
                    album_ids.add(album_id['album']['id'])
                    if len(album_ids) >= num_albums:
                        break
            if len(album_ids) > 0:
                tracks = await self.get_albums(session_id, list(album_ids))
                results.extend(tracks)
            else:
                print("No albums found from sampled tracks of top tracks")
            print("Got Results", results)
        return results

    def _build_track_uri_from_link(self, spotify_link: str) -> str:
        """Convert a Spotify track link to a track URI acceptable by the queue API."""
        try:
            parsed = urlparse(spotify_link)
            path = parsed.path or ""
            # Expecting path like /track/<id>
            segments = [seg for seg in path.split('/') if seg]
            track_id = segments[-1] if segments else ""
            # Defensive split in case of stray query-style suffix
            if "?" in track_id:
                track_id = track_id.split("?")[0]
            return f"spotify:track:{track_id}"
        except Exception:
            # Fall back to original link if parsing fails (Spotipy will error and be caught by caller)
            return spotify_link

    async def add_tracks_to_queue(self, session_id: str, songs: list[Pool_Song]) -> bool:
        """Add a list of songs to the user's queue on their active device.

        Returns True if all adds succeed, False if any fail.
        """
        spotify = self.get_user_spotify_client(session_id)
        if not spotify:
            return False

        all_ok = True
        for song in songs:
            try:
                uri = self._build_track_uri_from_link(song.spotify_link)
                # Use a thread to avoid blocking
                await asyncio.to_thread(spotify.add_to_queue, uri)
            except Exception as e:
                print(f"Failed to queue track {song.spotify_link}: {e}")
                all_ok = False
        return all_ok

    async def get_user_top_artists(self, session_id: str, time_range: str = "medium_term", limit: int = 20) -> List[Dict]:
        """Get a user's top artists"""
        print("Getting user top artists")
        spotify = self.get_user_spotify_client(session_id)
        if not spotify:
            return []
        print("Got Spotify Client")
        
        # Use asyncio.to_thread for the blocking API call
        top_artists = await asyncio.to_thread(
            spotify.current_user_top_artists,
            limit=MAX_LIMIT,
            time_range=time_range
        )
        if limit < MAX_LIMIT and len(top_artists['items']) >= limit:
            sampled_artists = random.sample(top_artists['items'], limit)
        else:
            sampled_artists = top_artists['items']
        
        print("Got Top Artists")
        results = []
        for artist in sampled_artists:
            artist = SpotifyArtist(
                name=artist['name'],
                genres=artist['genres'],
                popularity_score=artist['popularity'],
                artist_id=artist['id']
            )
            results.append(artist)
        print("Got Results", results)
        return results
    
    async def get_artist_top_tracks(self, session_id: str, artist_id: str, limit: int = 10) -> List[Dict]:
        """Get a artist's top tracks"""
        spotify = self.get_user_spotify_client(session_id)
        if not spotify:
            return []
            
        # Use asyncio.to_thread for the blocking API call
        top_tracks = await asyncio.to_thread(
            spotify.artist_top_tracks,
            artist_id
        )
        sampled_tracks = random.sample(top_tracks['tracks'], limit)
        results = []
        for track in sampled_tracks:
            # Default image if none available
            img_url = "https://via.placeholder.com/300"
            # Get image if available
            if track['album']['images'] and len(track['album']['images']) > 0:
                img_url = track['album']['images'][0]['url']
            artist = ""
            for a in track['artists']:
                artist += a['name'] + ", "
            artist = artist[:-2]
                
            song = Pool_Song(
                title=track['name'],
                artist=artist,
                album=track['album']['name'],
                img_link=img_url, # 300x300
                popularity_score=track['popularity'],
                duration_ms=track['duration_ms'],
                spotify_link=track['external_urls']['spotify'],
                release_date=track['album']['release_date'],
                genre="",
                lyrics=""
            )
            results.append(song)
        return results

    async def get_user_recently_played(self, session_id: str, limit: int = 30) -> List[Dict]:
        """Get a user's recently played tracks, but gets the last limit tracks first
        For example takes the last 30 tracks out of 50"""
        spotify = self.get_user_spotify_client(session_id)
        if not spotify:
            return []
        

        # Use asyncio.to_thread for the blocking API call
        recently_played = await asyncio.to_thread(
            spotify.current_user_recently_played,
            limit=MAX_LIMIT
        )
        
        results = []
        if len(recently_played['items']) >(MAX_LIMIT-limit):
            for item in recently_played['items'][MAX_LIMIT-limit:]:
                # Default image if none available
                img_url = "https://via.placeholder.com/300"
                # Get image if available
                if item['track']['album']['images'] and len(item['track']['album']['images']) > 0:
                    img_url = item['track']['album']['images'][0]['url']
                artist = ""
                for a in item['track']['artists']:
                    artist += a['name'] + ", "
                artist = artist[:-2]

                song = Pool_Song(
                    title=item['track']['name'],
                    artist=artist,
                    album=item['track']['album']['name'],
                    img_link=img_url, # 300x300
                    popularity_score=item['track']['popularity'],
                    duration_ms=item['track']['duration_ms'],
                    spotify_link=item['track']['external_urls']['spotify'],
                    release_date=item['track']['album']['release_date'],
                    genre="",
                    lyrics=""
                )
                results.append(song)
        return results
    
    async def get_user_saved_tracks(self, session_id: str, num_sections: int = 3, top_tracks_mode: bool = False, num_top_track_artists: int = 10) -> List[Dict]:
        """Get a user's saved tracks using efficient section-based sampling"""
        spotify = self.get_user_spotify_client(session_id)
        if not spotify:
            return []
            
        # Get initial batch to determine total count
        saved_tracks = await asyncio.to_thread(
            spotify.current_user_saved_tracks,
            limit=1
        )
        
        total_saved_tracks = saved_tracks['total']
        num_sections_to_sample = num_sections
        # Calculate section size (min of 50 or total/10)
        section_size = min(MAX_LIMIT, total_saved_tracks // 10)
        if section_size == 0:
            section_size = 1  # Ensure we have at least 1 track per section
            
        # Calculate total number of sections
        total_sections = math.ceil(total_saved_tracks / section_size)
        
        # Randomly select x sections (or fewer if total_sections < x)
        num_sections_to_sample = min(num_sections_to_sample, total_sections)
        selected_sections = random.sample(range(total_sections), num_sections_to_sample)
        
        # Get tracks from selected sections
        all_sampled_tracks = []
        for section in selected_sections:
            offset = section * section_size
            # Get tracks for this section
            section_tracks = await asyncio.to_thread(
                spotify.current_user_saved_tracks,
                limit=section_size,
                offset=offset
            )
            all_sampled_tracks.extend(section_tracks['items'])
        
        # Convert to Pool_Song objects
        results = []
        for track in all_sampled_tracks:
            # Default image if none available
            img_url = ""
            # Get image if available
            if track['track']['album']['images'] and len(track['track']['album']['images']) > 0:
                img_url = track['track']['album']['images'][0]['url']
            artist = ""
            for a in track['track']['artists']:
                artist += a['name'] + ", "
            artist = artist[:-2]
            song = Pool_Song(
                title=track['track']['name'],
                artist=artist,
                album=track['track']['album']['name'],
                img_link=img_url, # 300x300
                popularity_score=track['track']['popularity'],
                duration_ms=track['track']['duration_ms'],
                spotify_link=track['track']['external_urls']['spotify'],
                release_date=track['track']['album']['release_date'],
                genre="",
                lyrics=""
            )
            results.append(song)
        
        # ADDING TOP TRACKS FROM RANDOM ARTISTS
        # Get artist ids from results
        if top_tracks_mode:
            sampled_artist_ids = random.sample(all_sampled_tracks, num_top_track_artists) #HYPERPARAMETER
            artist_ids = set()
            for track in sampled_artist_ids:
                artist_ids.add(track['track']['artists'][0]['id'])
                
            # Process artist tracks in parallel
            tasks = [self.get_artist_top_tracks(session_id, artist_id, limit=5) for artist_id in artist_ids]
            artist_tracks_results = await asyncio.gather(*tasks)
            
            # Extend results with all valid artist tracks
            for tracks in artist_tracks_results:
                if tracks:
                    results.extend(tracks)
        return results
    
    async def get_albums(self, session_id: str, album_ids: List[str]) -> List[Dict]:
        """Fetch albums from a list of album ids"""
        spotify = self.get_user_spotify_client(session_id)
        if not spotify:
            return []
        
        # Use asyncio.to_thread for the blocking API call
        albums = await asyncio.to_thread(
            spotify.albums,
            album_ids
        )
        results = []
        for album in albums['albums']:
            img_url = ""
            if album['images'] and len(album['images']) > 0:
                img_url = album['images'][0]['url']
            album_name = album['name']
            popularity_score = album['popularity']
            release_date = album['release_date']
            for track in album['tracks']['items']:
                artist = ""
                for a in track['artists']:
                    artist += a['name'] + ", "
                artist = artist[:-2]
                song = Pool_Song(
                    title=track['name'],
                    artist=artist,
                    album=album_name,
                    img_link=img_url, # 300x300
                    popularity_score=popularity_score, # Not available in track data
                    duration_ms=track['duration_ms'],
                    spotify_link=track['external_urls']['spotify'],
                    release_date=release_date,
                    genre="",
                    lyrics=""
                )
                results.append(song)
        return results