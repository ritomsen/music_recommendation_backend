import rapidfuzz
from shazamio import Shazam
from typing import Optional, Dict, Any
from app.models.song import ShazamSong, Pool_Song
import asyncio
import json
import re




class ShazamService:
    def __init__(self):
        self.shazam = Shazam()

    
    async def search_song(self, track_name: str, artist_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for a song using Shazam's search functionality.
        
        Args:
            track_name (str): The name of the track
            artist_name (str): The name of the artist
            
        Returns:
            Optional[Dict[str, Any]]: Song details if found, None otherwise
        """
        try:
            cleaned_artist_name = artist_name.lower()
            cleaned_track_name = re.sub(r'\([^)]*\)', '', track_name).strip().lower()

            # Search for the song
            search_results = await self.shazam.search_track(track_name + " " + artist_name)
            # print(json.dumps(search_results, indent=2))
            if not search_results or not search_results.get('tracks', {}).get('hits'):
                print("Shazam Search: No Search Results", track_name, artist_name)
                return None
            
            hits = search_results['tracks']['hits']
            titles_and_subtitles = []
            for hit in hits:
                titles_and_subtitles.append(hit.get('heading', {}).get('title', '').lower() + " " + hit.get('heading', {}).get('subtitle', '').lower())
            # Iterate through results until we find a close match
            result = None
            max_score = 0
            max_ind = -1
            for ind, query in enumerate(titles_and_subtitles):
                score = rapidfuzz.fuzz.ratio(cleaned_track_name + " " + cleaned_artist_name, query)
                if score > 20 and score > max_score:
                    max_score = score
                    max_ind = ind

            if max_ind == -1:
                print("Shazam Search: No Search Results Above Threshold", track_name, artist_name, titles_and_subtitles)
                print(json.dumps(search_results, indent=2))
                return None
            result = hits[max_ind]
            
            print("Shazam Search Result:", track_name + " " + artist_name, "Result ->",titles_and_subtitles[max_ind], max_score, "list", titles_and_subtitles)

            # Extract relevant information
            song_details = {
                'key': result.get('key'),
            }
            
            return song_details
            
        except Exception as e:
            print(f"Error searching for song: {str(e)}")
            print(f"Searched for {track_name} by {artist_name}")
            # print(json.dumps(search_results, indent=2))
            return None

    async def get_song_details(self, song_key: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific song using its Shazam key.
        
        Args:
            song_key (str): The Shazam key of the song
            
        Returns:
            Optional[Dict[str, Any]]: Detailed song information if found, None otherwise
        """
        try:
            # Get detailed song information
            song_info = await self.shazam.track_about(song_key)
            
            if not song_info:
                return None
                
        
            # Extract relevant information
            # Album
            album = ""
            if 'sections' in song_info:
                for section in song_info['sections']:
                    if section.get('type') == 'SONG':
                        for meta in section.get('metadata', []):
                            if meta.get('title', '').lower() == 'album':
                                album = meta.get('text')
                                break
            # Artwork
            images = song_info.get('images', {})
            artwork_url = images.get('coverart', "")

            # Genre
            genre = song_info.get('genres', {}).get('primary') if song_info.get('genres', {}).get('primary') else ""
            # print("Shazam Song Info:", song_info.get('title'), song_info.get('subtitle'), genre)

            # Build details dict
            shazam_song = ShazamSong(
                title=song_info.get('title'),
                artist=song_info.get('subtitle'),
                album=album,
                key=song_info.get('key'),
                img_link=artwork_url,
                genre=genre,
                release_date=song_info.get('releasedate')
            )
    
            
            return shazam_song
            
        except Exception as e:
            print(f"Error getting song details: {str(e)} {json.dumps(song_info, indent=2)}")
            return ShazamSong(
                title="",
                artist="",
                album="",
                key="",
                img_link="",
                genre="",
                release_date=""
            )
    async def search_and_get_song_details(self, track_name: str, artist_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for a song and return its details.
        
        Args:
            track_name (str): The name of the track
            artist_name (str): The name of the artist
        """
        try:
            # Search for the song
            search_results = await self.search_song(track_name, artist_name)
            if search_results == None:
                print("Shazam Search: (Search and get) No Search Results", track_name, artist_name)
                return ShazamSong(
                    title = track_name,
                    artist = artist_name,
                    genre = "",
                    album = "",
                    img_link = "",
                    key = "",
                    release_date = ""
                )
            song_data = await self.get_song_details(search_results['key'])
            return song_data
        except Exception as e:
            print(f"Error searching and getting song details: {str(e)}")
            return None

    async def get_related_tracks(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            related_tracks = await self.shazam.related_tracks(key)
            print(f"Related Tracks: {json.dumps(related_tracks, indent=2)}")
            songs = []
            for track in related_tracks['tracks']:
                album = ""
                if 'sections' in track:
                    for section in track['sections']:
                        if section.get('type') == 'SONG':
                            for meta in section.get('metadata', []):
                                if meta.get('title', '').lower() == 'album':
                                    album = meta.get('text')
                
                cover_art = track.get('images', {}).get('coverart')
                genre = track.get('genres', {}).get('primary', "")
                shazam_song = Pool_Song(
                    spotify_link=track.get('url'),
                    title=track.get('title'),
                    artist=track.get('subtitle'),
                    album=album,
                    img_link=cover_art,
                    release_date="",
                    popularity_score=None,
                    duration_ms=None,
                    lyrics="",
                    genre=genre
                )
                songs.append(shazam_song)
            return songs
        except Exception as e:
            print(f"Error getting related tracks: {str(e)}")
            return None
    
    async def search_and_get_related_tracks(self, track_name: str, artist_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for a song and return its related tracks.
        
        Args:
            track_name (str): The name of the track
            artist_name (str): The name of the artist
        """
        try:
            search_results = await self.search_song(track_name, artist_name)
            if search_results == None:
                print("Shazam Search: (Search and get related) No Search Results", track_name, artist_name)
                return []
            related_tracks = await self.get_related_tracks(search_results['key'])
            return related_tracks
        except Exception as e:
            print(f"Error searching and getting related tracks: {str(e)}")
            return []
