import random
from typing import List
from app.models.song import Pool_Song
from app.services.service_instances import (
    genius_service,
    shazam_service,
    # spotify_service,
)
from app.models.song import ShazamSong
from app.services.spotify_service import SpotifyService
import asyncio

class CandidatePool:
    def __init__(self, genres: list[str], session_id: str, spotify_service: SpotifyService):
        self.pool: List[Pool_Song] = []
        self.set_pool = set()
        self.genres = genres
        self.shazam = shazam_service
        self.spotify = spotify_service
        self.genius = genius_service
        self.session_id = session_id
        self.lock = asyncio.Lock()  # Add a lock for thread safety
        print(f"Initialized CandidatePool for session {session_id} with genres: {genres}")

    def get_pool(self):
        return self.pool 
    
    def print_pool(self): #FOR DEBUGGING
        print(f"Number of Songs in Pool: {len(self.pool)}")
        for index, song in enumerate(self.pool):
            filtered_genre = "0 Genre Found" if song.genre == "" else song.genre
            print(f"Song {index} in pool: {song.title} {song.artist} {filtered_genre}")

    async def _add_tracks_to_pool(self, tracks: List[Pool_Song], comes_from: str):
        """
        Add a batch of tracks to the pool with thread safety.
        Filters out tracks that are too long or already in the pool.
        """
        # # Filter tracks before acquiring the lock
        # valid_tracks = []
        # for track in tracks:
        #     track_key = track.title + " " + track.artist
        #     if track.duration_ms < 600000 and track_key not in self.set_pool:
        #         valid_tracks.append(track)
        
        # if not valid_tracks:
        #     return
        
        # Use lock when modifying shared data structures
        async with self.lock:
            for track in tracks:
                track_key = track.title + " " + track.artist
                # Double-check that the song wasn't added by another task
                if track.duration_ms < 600000 and track_key not in self.set_pool: # Maybe add popularity > 20
                    self.pool.append(track)
                    self.set_pool.add(track_key)
                    print(f"Added new song to pool: {track.title} by {track.artist} from {comes_from}")

    async def _process_artist_tracks(self, artist):
        """Process tracks for a single artist in parallel"""
        if self.check_genre_match(artist.genres, False):
            print(f"Processing artist: {artist.name} - genre matched")
            top_tracks = await self.spotify.get_artist_top_tracks(self.session_id, artist.artist_id, limit=5)
            if top_tracks:
                await self._add_tracks_to_pool(top_tracks, "top_artists")
        else:
            print(f"Artist {artist.name} genre didn't match. Artist genres: {artist.genres}, Pool genres: {self.genres}")

    async def add_top_user_artists_tracks(self, time_range: str = "medium_term", limit: int = 20):
        print("Fetching top user artists tracks")
        top_artists = await self.spotify.get_user_top_artists(self.session_id, time_range, limit)
        
        # Process all artists in parallel
        tasks = [self._process_artist_tracks(artist) for artist in top_artists]
        await asyncio.gather(*tasks)

    async def add_top_user_tracks(self, time_range: str = "medium_term", album_mode: bool = False, limit: int = 50, num_albums: int = 2):
        print("Fetching top user tracks")
        top_tracks = await self.spotify.get_user_top_tracks(self.session_id, time_range=time_range, album_mode=album_mode, limit=limit, num_albums=num_albums)
        if top_tracks:
            await self._add_tracks_to_pool(top_tracks, "top_tracks")
            
            
    async def add_saved_tracks(self, num_sections: int = 3, top_tracks_mode: bool = False, num_top_track_artists: int = 10):
        print("Fetching saved tracks")
        saved_tracks = await self.spotify.get_user_saved_tracks(self.session_id, num_sections, top_tracks_mode, num_top_track_artists)
        if saved_tracks:
            await self._add_tracks_to_pool(saved_tracks, "saved_tracks")

    async def add_songs_parallel(self):
        """
        Calls all song-adding functions in parallel and joins their results.
        This is more efficient than calling them sequentially.
        """
        print("Starting parallel song addition process")
        tasks = [
            self.add_top_user_artists_tracks(time_range="medium_term", limit=20), # 20 * 5 = 100
            self.add_top_user_tracks(time_range="medium_term", album_mode=True, limit=50, num_albums=2), # 50 + ~25 = ~75 
            self.add_saved_tracks(num_sections=3, top_tracks_mode=True, num_top_track_artists=5),  # 150 + 25 = ~175
            #Total 325ish
        ]
        
        # Use asyncio.gather with return_exceptions=True to handle errors gracefully
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any errors that occurred
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error in task {i}: {str(result)}")
                
        print("Completed parallel song addition process")

    def check_genre_match(self, genres: list[str], isSong: bool):
        #TODO NEED TO FIX THIS
        if len(self.genres) == 0:
            return True
        if not isSong and (len(genres) == 0 or genres[0]==""):
            print("No genres found for Artist")
            return True
        elif len(genres) == 0 or genres[0]=="":
            print("No genres found for Song")
            return True
        for genre in genres:
            for pool_genre in self.genres:
                if genre.lower() in pool_genre.lower() or pool_genre.lower() in genre.lower():
                    print(f"Genre match found: {genre} matches {pool_genre}")
                    return True
        print(f"No genre match found for genres: {genres}")
        return False
    
    #TODO ADD MORE SONGS FROM SHAZAM 
        