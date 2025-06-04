#!/usr/bin/env python
import random
import sys
from pathlib import Path
import json
import time
from datetime import datetime
from app.services.service_instances import spotify_service
from app.rec_service.recommendation import RecommendationService


# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.rec_service.candidate_pool import CandidatePool
from app.services.spotify_service import SpotifyService
from app.models.song import Pool_Song
from app.rec_service.tourney import Tourney

def save_results_to_json(pool, filename):
    """Save pool results to a JSON file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "test_results"
    output_dir.mkdir(exist_ok=True)
    
    filepath = output_dir / f"{filename}_{timestamp}.json"
    
    # Convert pool objects to dictionaries
    pool_data = [song.dict() for song in pool]
    
    with open(filepath, 'w') as f:
        json.dump(pool_data, f, indent=2)
    
    print(f"Results saved to: {filepath}")
    return filepath

def print_pool_summary(pool, source=None):
    """Print a summary of the songs in the pool"""
    for i, song in enumerate(pool, 1):
        print(f"{i}. {song.title} by {song.artist} ({song.genre})")
    print(f"\n=== Total songs in pool: {len(pool)} ===")



def run_spotify_auth():
    """Run the Spotify authentication flow and return a session ID"""
    
    # Get the authorization URL
    auth_data = spotify_service.get_auth_url()
    print("\nAuthorization URL:", auth_data["auth_url"])
    print("State:", auth_data["state"])
    print("\nPlease open the above URL in your browser, log in to Spotify, and authorize the application.")
    print("After authorizing, you'll be redirected to a URL. Copy the 'code' parameter from that URL.")
    
    # Wait for the user to authenticate
    code = input("\nEnter the authorization code from the redirect URL: ")
    
    # Exchange the code for an access token
    token_data = spotify_service.get_access_token(code, auth_data["state"])
    session_id = token_data["session_id"]
    print("\nAuthentication successful! Session ID:", session_id)
    
    return session_id, spotify_service
def print_tourney_results(tourney_results):
    print("\n=== TOURNEY RESULTS ===")
    for song, score in tourney_results:
        print(f"{song.title} by {song.artist} ({song.genre}) - Score: {score:.2f}")

async def test_candidate_pool_with_real_spotify():
    """Integration test for CandidatePool with real Spotify authentication"""
    print("=== Starting CandidatePool Integration Test ===")
    
    # Step 1: Authenticate with Spotify
    session_id, spotify_service = run_spotify_auth()
    
    # recommendation_service = RecommendationService()
    # image_data = open("tests/test.jpg", "rb").read()
    # await recommendation_service.get_image_analysis(image_data, session_id, spotify_service)

    # Step 2: Create a CandidatePool with some genres
    genres = ["rap"]
    pool = CandidatePool(genres, session_id, spotify_service)
    
    # # Step 3: Add songs from top artists
    # print("\nAdding songs from your top artists...")
    # await pool.add_top_user_artists_tracks()
    # print_pool_summary(pool.get_pool(), "top_artists")
    
    # # Step 4: Add songs from top tracks
    # print("\nAdding songs from your top tracks...")
    # pool.add_top_user_tracks()
    # print_pool_summary(pool.get_pool(), "top_tracks")
    
    # # Step 5: Add recently played tracks
    # print("\nAdding songs from your recently played tracks...")
    # pool.add_recently_played_tracks()
    # print_pool_summary(pool.get_pool(), "recently_played")
    
    # # Step 6: Add saved tracks
    # print("\nAdding songs from your saved tracks...")
    # pool.add_saved_tracks()
    # print_pool_summary(pool.get_pool(), "saved_tracks")
    
    # # Step 7: Add saved album tracks
    # print("\nAdding songs from your saved albums...")
    # pool.add_saved_album_tracks()
    # print_pool_summary(pool.get_pool(), "saved_albums")
    recommendation_service = RecommendationService()

    # Step 8: Add songs in parallel
    start = time.time()
    candidate_pool = await recommendation_service.make_candidate_pool(session_id)
    end = time.time()
    print(f"Time taken Candidate Pool: {end - start} seconds")


    # # Step 9: Save results to a JSON file
    # # save_results_to_json(pool.get_pool(), "candidate_pool_results")

    # max_size = 100
    # if len(candidate_pool) > max_size:
    #     print(f"Shuffling candidate pool from {len(candidate_pool)} to {max_size}")
    #     random.shuffle(candidate_pool)
    #     candidate_pool = candidate_pool[:max_size]
    
    # start = time.time()
    # output = await recommendation_service.find_recommendations(candidate_pool)
    # end = time.time()
    # print(f"Time taken Tourney: {end - start} seconds")
    # print(output)



if __name__ == "__main__":
    import asyncio
    asyncio.run(test_candidate_pool_with_real_spotify()) 