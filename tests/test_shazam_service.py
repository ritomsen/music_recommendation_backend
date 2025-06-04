import asyncio
import time

import rapidfuzz
from app.services.shazam_service import ShazamService

async def test_get_song_details():
    # Initialize the service
    shazam_service = ShazamService()
    
    # First, let's search for a popular song to get its key
    # search_result = await shazam_service.search_and_get_song_details("MVP", "Russ")
    
    # if not search_result:
    #     print("Failed to find song in search")
    #     return
        
    
    # print("\nDetailed Song Information:")
    # print("\nSong Details:")
    # print(f"Title: {search_result.title}")
    # print(f"Artist: {search_result.artist}")
    # print(f"Album: {search_result.album}")
    # print(f"Genre: {search_result.genre}")
    # print(f"Release Date: {search_result.release_date}")
    # print(f"Image URL: {search_result.img_link}")
    # print(f"Shazam Key: {search_result.key}")



    print("Getting related tracks")
    related_tracks = await shazam_service.search_and_get_related_tracks("MVP", "Russ")
    for track in related_tracks:
        print(f"Track: {track.title} by {track.artist}, {track.spotify_link}")

    
if __name__ == "__main__":
    asyncio.run(test_get_song_details()) 