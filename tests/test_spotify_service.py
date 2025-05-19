import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.spotify_service import SpotifyService

def save_to_json(data, filename):
    """Save data to a JSON file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "spotify_test_results"
    output_dir.mkdir(exist_ok=True)
    
    # Convert Pydantic models to dictionaries if needed
    if hasattr(data, '__iter__') and not isinstance(data, (str, bytes, dict)):
        # For lists/iterables of objects
        serializable_data = [item.dict() if hasattr(item, 'dict') else item for item in data]
    else:
        # For single objects
        serializable_data = data.dict() if hasattr(data, 'dict') else data
    
    filepath = output_dir / f"{filename}_{timestamp}.json"
    with open(filepath, 'w') as f:
        json.dump(serializable_data, f, indent=2)
    return filepath

def test_spotify_service():
    # Initialize the service
    spotify_service = SpotifyService()
    
    # Get the authorization URL
    auth_data = spotify_service.get_auth_url()
    print("\nAuthorization URL:", auth_data["auth_url"])
    print("State:", auth_data["state"])
    
    # After getting the authorization URL, you'll need to:
    # 1. Open the URL in your browser
    # 2. Log in to Spotify
    # 3. Authorize the application
    # 4. Copy the code from the redirect URL
    
    # Once you have the code, uncomment and use these lines:
    code = input("\nEnter the authorization code from the redirect URL: ")
    token_data = spotify_service.get_access_token(code, auth_data["state"])
    session_id = token_data["session_id"]
    print("\nSession ID:", session_id)
    
    # Test getting top tracks
    top_tracks = spotify_service.get_user_top_tracks(session_id)
    if top_tracks:
        filepath = save_to_json(top_tracks, "top_tracks")
        print(f"\nSuccessfully saved top tracks to: {filepath}")
    
    # Test getting top artists
    top_artists = spotify_service.get_user_top_artists(session_id)
    if top_artists:
        filepath = save_to_json(top_artists, "top_artists")
        print(f"\nSuccessfully saved top artists to: {filepath}")

if __name__ == "__main__":
    test_spotify_service() 