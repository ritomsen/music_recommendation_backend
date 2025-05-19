from typing import List
from app.models.song import Pool_Song
from app.services.shazam_service import ShazamService
from app.services.spotify_service import SpotifyService
from app.services.ai_service import AIService
import asyncio

class CandidatePool:
    def __init__(self, genres: list[str], location: str, session_id: str, spotify_service: SpotifyService):
        self.pool: List[Pool_Song] = []
        self.set_pool = set()
        self.genres = genres
        self.location = location
        self.shazam = ShazamService()
        self.spotify = spotify_service
        self.ai = AIService()
        self.session_id = session_id
        self.lock = asyncio.Lock()  # Add a lock for thread safety

    def get_pool(self):
        return self.pool 
    
    def print_pool(self): #FOR DEBUGGING
        print("# of Songs in Pool: " + str(len(self.pool)))
        for song in self.pool:
            print(song.title + " " + song.artist + " " + song.genre)

    async def _process_track(self, track, comes_from):
        # Check if song already exists without needing the lock
        track_key = track.title + " " + track.artist
        if track.duration_ms >= 600000 or track_key in self.set_pool:
            return
        
        print(track.title, track.artist)
        shazam_song = await self.shazam.search_and_get_song_details(track.title, track.artist)
        if shazam_song and self.check_genre_match([shazam_song.genre], True):
            description = "description"  # TODO GET DESCRIPTION FROM AI
            lyrics = "lyrics"  # TODO GET LYRICS FROM GENIUS? 
            new_song = Pool_Song(
                title=track.title,
                artist=track.artist,
                album=track.album,
                genre=shazam_song.genre,
                img_link=track.img_link,
                popularity_score=track.popularity_score,
                spotify_link=track.spotify_link,
                release_date=track.release_date,
                description=description,
                lyrics=lyrics,
                comes_from=comes_from
            )
            
            # Use lock when modifying shared data structures
            async with self.lock:
                # Double-check that the song wasn't added by another task
                if track_key not in self.set_pool:
                    self.pool.append(new_song)
                    self.set_pool.add(track_key)

    async def add_top_user_artists_tracks(self):
        top_artists = self.spotify.get_user_top_artists(self.session_id)
        tasks = []
        for artist in top_artists:
            # I KNOW ARTISTS CAN HAVE MULTIPLE GENRES SO THIS MIGHT NOT BE GOOD
            if self.check_genre_match(artist.genres, False): 
                print(artist.name, "genre matched")
                top_tracks = self.spotify.get_artist_top_tracks(self.session_id, artist.artist_id)
                for track in top_tracks:
                    tasks.append(self._process_track(track, "top_artists"))
            else:
                print(artist.name, "genre didn't match", "artist genres: ", artist.genres, "pool genres: ", self.genres)
        # Process tracks in parallel within this function
        if tasks:
            await asyncio.gather(*tasks)

    async def add_top_user_tracks(self):
        top_tracks = self.spotify.get_user_top_tracks(self.session_id)
        tasks = []
        for track in top_tracks:
            tasks.append(self._process_track(track, "top_tracks"))
        
        if tasks:
            await asyncio.gather(*tasks)

    async def add_recently_played_tracks(self):
        recently_played = self.spotify.get_user_recently_played(self.session_id)
        tasks = []
        for track in recently_played:
            tasks.append(self._process_track(track, "recently_played"))
        
        if tasks:
            await asyncio.gather(*tasks)

    async def add_saved_tracks(self):
        saved_tracks = self.spotify.get_user_saved_tracks(self.session_id)
        tasks = []
        for track in saved_tracks:
            tasks.append(self._process_track(track, "saved_tracks"))
        
        if tasks:
            await asyncio.gather(*tasks)

    # Might not need
    async def add_saved_album_tracks(self):
        tracks = self.spotify.get_user_saved_albums(self.session_id)
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
        await asyncio.gather(
            self.add_top_user_artists_tracks(),
            self.add_top_user_tracks(),
            self.add_recently_played_tracks(),
            self.add_saved_tracks(),
            self.add_saved_album_tracks()
        )

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
                    # print(genre, pool_genre)
                    return True
        # print(genres, self.genres)
        return False
    
    #TODO ADD MORE SONGS FROM SHAZAM 
        