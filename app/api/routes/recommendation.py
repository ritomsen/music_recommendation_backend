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
    audio: UploadFile = File(...),
    location: Optional[str] = Form(None)
):
    """
    Get song recommendations based on an image, audio file, and optional location.
    """
    try:
        # Create temporary files for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded files
            image_path = os.path.join(temp_dir, image.filename)
            audio_path = os.path.join(temp_dir, audio.filename)
            
            await save_upload_file(image, image_path)
            await save_upload_file(audio, audio_path)
            
            # Read file contents
            image_data = await read_file_content(image_path)
            audio_data = await read_file_content(audio_path)
            
            # Analyze files using AI service
            image_features = await ai_service.analyze_image(image_data)
            audio_features = await ai_service.analyze_audio(audio_data)
            
            # Get recommendations
            recommendations = await ai_service.get_recommendations(
                image_features,
                audio_features,
                location
            )
            
            # If no recommendations from AI service, return mock data
            if not recommendations:
                return RecommendationService.get_mock_recommendations()
            
            return recommendations
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 