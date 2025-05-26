from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from app.services.spotify_service import SpotifyService
from app.core.config import settings
from typing import Dict, Optional
from app.services.service_instances import spotify_service

router = APIRouter()

@router.get("/login")
async def spotify_login():
    """
    Generate a Spotify login URL and return it to the client
    """
    auth_data = spotify_service.get_auth_url()
    return auth_data

@router.get("/callback")
async def spotify_callback(code: str, state: str, request: Request):
    """
    Handle the Spotify callback and exchange the authorization code for tokens
    """
    try:
        # Exchange code for tokens
        token_data = spotify_service.get_access_token(code, state)
        
        # Redirect to frontend with the session ID as a query parameter
        frontend_url = f"{settings.FRONTEND_URL}?session_id={token_data['session_id']}"
        return RedirectResponse(url=frontend_url)
    except Exception as e:
        # Redirect to frontend with error message
        error_redirect = f"{settings.FRONTEND_URL}?error={str(e)}"
        return RedirectResponse(url=error_redirect)

@router.get("/check-auth")
async def check_auth(session_id: Optional[str] = None):
    """
    Check if a user is authenticated with Spotify
    """
    print(f"[/check-auth] endpoint hit with session_id: {session_id}")
    if not session_id:
        return JSONResponse({"authenticated": False, "message": "No session ID provided"})
    
    is_valid = spotify_service.validate_token(session_id)
    
    return {
        "authenticated": is_valid,
        "message": "Token is valid" if is_valid else "Token is invalid or expired"
    }

@router.post("/logout")
async def logout(session_id: str):
    """
    Log a user out by clearing their tokens
    """
    success = spotify_service.clear_user_token(session_id)
    return {"success": success}

@router.get("/user-profile")
async def get_user_profile(session_id: str):
    """
    Get the user's Spotify profile
    """
    spotify = spotify_service.get_user_spotify_client(session_id)
    if not spotify:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    try:
        user_profile = spotify.current_user()
        return user_profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Spotify profile: {str(e)}")

@router.get("/top-tracks") #FOR TESTING
async def get_top_tracks(session_id: str, time_range: str = "medium_term"):
    """
    Get a user's top tracks
    """
    top_tracks = spotify_service.get_user_top_tracks(session_id, time_range)
    return top_tracks

