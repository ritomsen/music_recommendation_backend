from typing import List
from app.models.song import Pool_Song
from app.services.service_instances import (
    genius_service,
    shazam_service,
    # spotify_service,
)
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
            print(f"Song {index} in pool: {song.title} {song.artist} {filtered_genre} {song.comes_from}")

    async def _process_track(self, track, comes_from):
        # Check if song already exists without needing the lock
        track_key = track.title + " " + track.artist
        if track.duration_ms >= 600000 or track_key in self.set_pool:
            print(f"Skipping track {track.title} - Duration too long or already in pool")
            return
        
        print(f"Processing track: {track.title} by {track.artist}")
        
        # Fetch lyrics and song details in parallel
        shazam_task = self.shazam.search_and_get_song_details(track.title, track.artist)
        genius_task = self.genius.search_song(track.title, track.artist)
        
        shazam_song, genius_result = await asyncio.gather(shazam_task, genius_task)
        
        lyrics = genius_result.get("lyrics", "") if genius_result else ""
        
        if shazam_song and self.check_genre_match([shazam_song.genre], True):
            new_song = Pool_Song(
                title=track.title,
                artist=track.artist,
                album=track.album,
                genre=shazam_song.genre,
                img_link=track.img_link,
                popularity_score=track.popularity_score,
                spotify_link=track.spotify_link,
                release_date=track.release_date,
                duration_ms=track.duration_ms,
                lyrics=lyrics,
                comes_from=comes_from
            )
            
            # Use lock when modifying shared data structures
            async with self.lock:
                # Double-check that the song wasn't added by another task
                if track_key not in self.set_pool:
                    self.pool.append(new_song)
                    self.set_pool.add(track_key)
                    print(f"Added new song to pool: {track.title} by {track.artist}")
        else:
            print(f"Track {track.title} did not match genre criteria")

    async def add_top_user_artists_tracks(self):
        print("Fetching top user artists tracks")
        top_artists = await asyncio.to_thread(self.spotify.get_user_top_artists, self.session_id)
        tasks = []
        for artist in top_artists:
            # I KNOW ARTISTS CAN HAVE MULTIPLE GENRES SO THIS MIGHT NOT BE GOOD
            if self.check_genre_match(artist.genres, False): 
                print(f"Processing artist: {artist.name} - genre matched")
                top_tracks = await asyncio.to_thread(self.spotify.get_artist_top_tracks, self.session_id, artist.artist_id)
                for track in top_tracks:
                    tasks.append(self._process_track(track, "top_artists"))
            else:
                print(f"Artist {artist.name} genre didn't match. Artist genres: {artist.genres}, Pool genres: {self.genres}")
        if tasks:
            await asyncio.gather(*tasks)

    async def add_top_user_tracks(self):
        print("Fetching top user tracks")
        top_tracks = await asyncio.to_thread(self.spotify.get_user_top_tracks, self.session_id)
        tasks = []
        for track in top_tracks:
            tasks.append(self._process_track(track, "top_tracks"))
        
        if tasks:
            await asyncio.gather(*tasks)

    async def add_recently_played_tracks(self):
        print("Fetching recently played tracks")
        recently_played = await asyncio.to_thread(self.spotify.get_user_recently_played, self.session_id)
        tasks = []
        for track in recently_played:
            tasks.append(self._process_track(track, "recently_played"))
        
        if tasks:
            await asyncio.gather(*tasks)

    async def add_saved_tracks(self):
        print("Fetching saved tracks")
        saved_tracks = await asyncio.to_thread(self.spotify.get_user_saved_tracks, self.session_id)
        tasks = []
        for track in saved_tracks:
            tasks.append(self._process_track(track, "saved_tracks"))
        
        if tasks:
            await asyncio.gather(*tasks)

    async def add_saved_album_tracks(self):
        print("Fetching saved album tracks")
        tracks = await asyncio.to_thread(self.spotify.get_user_saved_albums, self.session_id)
        tasks = []
        for track in tracks:
            tasks.append(self._process_track(track, "saved_albums"))
        
        if tasks:
            await asyncio.gather(*tasks)

    async def add_songs_parallel(self):
        """
        Calls all song-adding functions in parallel and joins their results.
        This is more efficient than calling them sequentially.
        """
        print("Starting parallel song addition process")
        await asyncio.gather(
            self.add_top_user_artists_tracks(),
            self.add_top_user_tracks(),
            self.add_recently_played_tracks(),
            self.add_saved_tracks(),
            self.add_saved_album_tracks()
        )
        print("Completed parallel song addition process")

    def check_genre_match(self, genres: list[str], isSong: bool):
        #TODO NEED TO FIX THIS
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
        