import random
import time
from aiohttp_retry import Tuple
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional, List
from app.models.song import Pool_Song
from app.rec_service.recommendation import RecommendationService
from app.utils.file_handlers import save_upload_file, read_file_content
from app.services.service_instances import openai_service
import os
import tempfile

router = APIRouter()
recommendation_service = RecommendationService()

@router.post("/recommend", response_model=List[Tuple[Pool_Song, float]])
async def get_song_recommendations(
    image: UploadFile = File(...),
    audio: Optional[UploadFile] = File(None),
    location: Optional[str] = Form(None),
    session_id: str = Form(...)
):
    """
    Get song recommendations based on an image, optional audio file, and optional location.
    
    Args:
        image: Required image file for analysis
        audio: Optional audio file for analysis
        location: Optional location string in format "latitude,longitude"
        session_id: Required Spotify session ID for user context
    """
    try:
        # Initialize audio-related variables
        time_start = time.time()
        audio_data = None
        image_data = None

        # Create temporary files for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # --- Process Image (Required) ---
            image_path = os.path.join(temp_dir, image.filename)
            await save_upload_file(image, image_path)
            image_data = await read_file_content(image_path)

            # --- Process Audio (Optional) ---
            if audio:
                if not audio.filename:
                    raise HTTPException(status_code=400, detail="Audio file name is missing.")
                audio_path = os.path.join(temp_dir, audio.filename)
                await save_upload_file(audio, audio_path)
                audio_data = await read_file_content(audio_path)

            time_prepare_start = time.time()
            # Prepare the recommendation service with all available data
            await recommendation_service.prepare(
                image_data=image_data,
                audio_data=audio_data,
                location=location,
                session_id=session_id
            )
            print("Finished preparing recommendation service")
            time_prepare_end = time.time()
            print("Prepare Time", time_prepare_end - time_prepare_start)
            time_make_candidate_pool_start = time.time()
            # Create candidate pool based on analyzed features
            candidate_pool = await recommendation_service.make_candidate_pool(
                session_id=session_id
            )

            # MIGHT NEED TO REMOVE THIS
            # MAKES IT SO I DON"T HAVE TOO BIG OF A TOURNAMENT
            #TODO Make this a flag or parameter I can choose on frontend
            max_size = 75
            if len(candidate_pool) > max_size:
                print(f"Shuffling candidate pool from {len(candidate_pool)} to {max_size}")
                random.shuffle(candidate_pool)
                candidate_pool = candidate_pool[:max_size]
            time_make_candidate_pool_end = time.time()
            print("Candidate Pool Time", time_make_candidate_pool_end - time_make_candidate_pool_start)
            time_find_recommendations_start = time.time()
            # Get recommendations using the candidate pool
            recommendations = await recommendation_service.find_recommendations(candidate_pool)
            time_find_recommendations_end = time.time()

            if not recommendations:
                raise HTTPException(
                    status_code=404,
                    detail="No recommendations found based on the provided inputs"
                )

            time_end = time.time()
            print(f"Total time taken: {time_end - time_start} seconds")
            print(f"Time taken to prepare: {time_prepare_end - time_prepare_start} seconds")
            print(f"Time taken to make candidate pool: {time_make_candidate_pool_end - time_make_candidate_pool_start} seconds")
            print(f"Time taken to find recommendations: {time_find_recommendations_end - time_find_recommendations_start} seconds")
            
            return recommendations

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.post("/recommend-genetic", response_model=List[Tuple[Pool_Song, float]])
async def get_song_recommendations_genetic(
    image: UploadFile = File(...),
    audio: Optional[UploadFile] = File(None),
    location: Optional[str] = Form(None),
    session_id: str = Form(...)
):
    """
    Get song recommendations using genetic algorithm based on an image, optional audio file, and optional location.
    
    Args:
        image: Required image file for analysis
        audio: Optional audio file for analysis
        location: Optional location string in format "latitude,longitude"
        session_id: Required Spotify session ID for user context
    """
    try:
        # Initialize audio-related variables
        time_start = time.time()
        audio_data = None
        image_data = None

        # Create temporary files for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # --- Process Image (Required) ---
            image_path = os.path.join(temp_dir, image.filename)
            await save_upload_file(image, image_path)
            image_data = await read_file_content(image_path)

            # --- Process Audio (Optional) ---
            if audio:
                if not audio.filename:
                    raise HTTPException(status_code=400, detail="Audio file name is missing.")
                audio_path = os.path.join(temp_dir, audio.filename)
                await save_upload_file(audio, audio_path)
                audio_data = await read_file_content(audio_path)

            time_prepare_start = time.time()
            # Prepare the recommendation service with all available data
            await recommendation_service.prepare(
                image_data=image_data,
                audio_data=audio_data,
                location=location,
                session_id=session_id
            )
            print("Finished preparing recommendation service")
            time_prepare_end = time.time()
            print("Prepare Time", time_prepare_end - time_prepare_start)
            
            time_make_candidate_pool_start = time.time()
            # Create candidate pool based on analyzed features
            candidate_pool = await recommendation_service.make_candidate_pool(
                session_id=session_id
            )
            time_make_candidate_pool_end = time.time()
            print("Candidate Pool Time", time_make_candidate_pool_end - time_make_candidate_pool_start)
            
            time_find_recommendations_start = time.time()
            # Get recommendations using genetic algorithm
            recommendations = await recommendation_service.find_recommendations_genetic(candidate_pool)
            time_find_recommendations_end = time.time()

            if not recommendations:
                raise HTTPException(
                    status_code=404,
                    detail="No recommendations found based on the provided inputs"
                )

            time_end = time.time()
            print(f"Total time taken: {time_end - time_start} seconds")
            print(f"Time taken to prepare: {time_prepare_end - time_prepare_start} seconds")
            print(f"Time taken to make candidate pool: {time_make_candidate_pool_end - time_make_candidate_pool_start} seconds")
            print(f"Time taken to find recommendations GENETIC: {time_find_recommendations_end - time_find_recommendations_start} seconds")
            
            return recommendations

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )