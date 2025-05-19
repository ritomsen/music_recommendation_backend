from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional, List
from app.models.song import SongResponse
from app.services.ai_service import AIService
from app.services.recommendation_service import RecommendationService
from app.utils.file_handlers import save_upload_file, read_file_content
import os
import tempfile

router = APIRouter()
ai_service = AIService()

@router.post("/recommend", response_model=List[SongResponse])
async def get_song_recommendations(
    image: UploadFile = File(...),
    audio: Optional[UploadFile] = File(None), # Make audio optional
    location: Optional[str] = Form(None)
):
    """
    Get song recommendations based on an image, optional audio file, and optional location.
    """
    try:
        # Initialize audio-related variables
        audio_path = None
        audio_data = None
        audio_features = None

        # Create temporary files for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # --- Process Image (Required) ---
            image_path = os.path.join(temp_dir, image.filename)
            await save_upload_file(image, image_path)
            image_data = await read_file_content(image_path)
            image_features = await ai_service.analyze_image(image_data)

            # --- Process Audio (Optional) ---
            if audio:
                # Ensure audio has a filename before proceeding
                if not audio.filename:
                     raise HTTPException(status_code=400, detail="Audio file name is missing.")
                audio_path = os.path.join(temp_dir, audio.filename)
                await save_upload_file(audio, audio_path)
                audio_data = await read_file_content(audio_path)
                audio_features = await ai_service.analyze_audio(audio_data)

            # Get recommendations using potentially None audio features
            recommendations = await ai_service.get_recommendations(
                image_features=image_features,
                audio_features=audio_features, # Can be None if audio was not provided
                location=location
            )

            # If no recommendations from AI service, return mock data
            # Note: Consider if mock data logic needs adjustment based on inputs
            if not recommendations:
                return RecommendationService.get_mock_recommendations()

            return recommendations

    except HTTPException as http_exc:
        # Re-raise HTTPException to let FastAPI handle it
        raise http_exc
    except Exception as e:
        # Log the exception for debugging purposes (optional but recommended)
        # logger.error(f"Error processing recommendation request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")