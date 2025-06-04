from app.rec_service.candidate_pool import CandidatePool
from app.rec_service.tourney import Tourney
from app.services.service_instances import (
    spotify_service,
    openai_service,
    weather_service,
)
import json
import asyncio
from typing import Tuple
from app.models.song import Pool_Song
from app.services.spotify_service import SpotifyService

class RecommendationService:
    def __init__(self):
        print("Initializing RecommendationService")
        self.user_context = {}
        self.image_analysis = {}
        self.audio_analysis = {}
        self.location_weather_analysis = {}
        self.prompt_template = None

        self.open_ai_service = openai_service
        self.weather_service = weather_service

    def prepare_prompt_template(self) -> str:
        """
        Prepares the prompt template with all contextual data
        """
        try:
            if self.prompt_template is not None:
                print("Using cached prompt template")
                return self.prompt_template

            print("Preparing prompt template")
            # Load the base prompt template
            with open("app/prompts/song_recommendation.txt", "r") as f:
                base_template = f.read()

            # Format the contextual data
            weather_data = json.dumps(self.location_weather_analysis, indent=2)
            user_context = json.dumps(self.user_context, indent=2)
            image_analysis = json.dumps(self.image_analysis, indent=2)
            audio_analysis = json.dumps(self.audio_analysis, indent=2)

            print(f"Context data prepared - Weather: {weather_data[:100]}...")
            print(f"Image analysis: {image_analysis[:100]}...")

            # Create the template with contextual data but leave song data blank
            self.prompt_template = base_template.format(
                weather_data=weather_data.replace("{", "{{").replace("}", "}}"),
                user_context=user_context.replace("{", "{{").replace("}", "}}"),
                image_analysis=image_analysis.replace("{", "{{").replace("}", "}}"),
                audio_analysis=audio_analysis.replace("{", "{{").replace("}", "}}"),
                song1_title="{song1_title}",
                song1_artist="{song1_artist}",
                song1_popularity="{song1_popularity}",
                song1_release_date="{song1_release_date}",
                song1_duration="{song1_duration}",
                song2_title="{song2_title}",
                song2_artist="{song2_artist}",
                song2_popularity="{song2_popularity}",
                song2_release_date="{song2_release_date}",
                song2_duration="{song2_duration}",
            )
            print("Prompt template prepared and cached", self.prompt_template)
            return self.prompt_template
        except Exception as e:
            print("RITOM SEN ERROR")
            print(f"Error preparing prompt template: {e}")
            return None

    async def get_image_analysis(self, image_data: bytes, session_id: str):
        print("Getting image analysis")
        top_20_songs, top_20_artists = await asyncio.gather(
            spotify_service.get_user_top_tracks(session_id, time_range="long_term", limit=20, album_mode=False),
            spotify_service.get_user_top_artists(session_id, time_range="long_term", limit=20)
        )
        print("Got Top 20 Songs and Artists")
        track_titles_and_artists = [f"{song.title} - {song.artist}" for song in top_20_songs]
        artist_names = [artist.name for artist in top_20_artists]
        print("Got Track Titles and Artists")
        self.image_analysis = await self.open_ai_service.analyze_image(image_data, track_titles_and_artists, artist_names)
        print(f"Image analysis received: {self.image_analysis}")

    async def get_audio_analysis(self, audio_data: bytes):
        if not audio_data:
            return
        print("Getting audio analysis")
        self.audio_analysis = await self.open_ai_service.analyze_audio(audio_data)
        print(f"Audio analysis received: {self.audio_analysis}")

    async def get_location_weather_analysis(self, location: str):
        print(f"Getting weather analysis for location: {location}")
        # Assuming location is in format "latitude,longitude"
        lat, lon = map(float, location.split(','))
        self.location_weather_analysis = await self.weather_service.get_current_weather(lat, lon)
        print(f"Weather analysis received: {self.location_weather_analysis}")

    async def get_user_context(self, session_id: str):
        print("Getting user context")
        # Fetch all user data in parallel
        (
            top_songs_short,
            top_songs_medium,
            top_songs_long,
            top_artists_short,
            top_artists_medium,
            top_artists_long,
            recently_played
        ) = await asyncio.gather(
            spotify_service.get_user_top_tracks(session_id, time_range="short_term", limit=10, album_mode=False),
            spotify_service.get_user_top_tracks(session_id, time_range="medium_term", limit=10, album_mode=False),
            spotify_service.get_user_top_tracks(session_id, time_range="long_term", limit=10, album_mode=False),
            spotify_service.get_user_top_artists(session_id, time_range="short_term", limit=10),
            spotify_service.get_user_top_artists(session_id, time_range="medium_term", limit=10),
            spotify_service.get_user_top_artists(session_id, time_range="long_term", limit=10),
            spotify_service.get_user_recently_played(session_id, limit=10)
        )

        # Prepare data for the LLM (convert objects to strings or dicts as needed)
        def song_list_to_str(song_list):
            return [f"{song.title} - {song.artist}" for song in song_list]
        def artist_list_to_str(artist_list):
            return [artist.name for artist in artist_list]

        user_name = "User"  # Replace with actual user name if available
        user_context = await self.open_ai_service.generate_user_context(
            name=user_name,
            top_songs_short=song_list_to_str(top_songs_short),
            top_songs_medium=song_list_to_str(top_songs_medium),
            top_songs_long=song_list_to_str(top_songs_long),
            top_artists_short=artist_list_to_str(top_artists_short),
            top_artists_medium=artist_list_to_str(top_artists_medium),
            top_artists_long=artist_list_to_str(top_artists_long),
            recently_played=song_list_to_str(recently_played)
        )
        self.user_context = user_context
        print("User context initialized", self.user_context)

    async def prepare(self, image_data: bytes, audio_data: bytes, location: str, session_id: str):
        """
        Prepare all analysis data in parallel.
        """
        print("Starting parallel data preparation")
        # Create tasks for parallel execution
        tasks = [
            self.get_image_analysis(image_data, session_id),
            self.get_audio_analysis(audio_data),
            self.get_location_weather_analysis(location),
            self.get_user_context(session_id)
        ]
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
        print("All analysis tasks completed")
        
        # After all analyses are complete, prepare the prompt template
        self.prepare_prompt_template()

    async def make_candidate_pool(self, session_id: str):
        print("Creating candidate pool")
        genres = self.image_analysis.get("genres", [])
        print(f"Using genres from image analysis: {genres}")
        candidate_pool = CandidatePool(genres, session_id, spotify_service)
        await candidate_pool.add_songs_parallel()
        print(f"Candidate pool created with {len(candidate_pool.pool)} songs")
        candidate_pool.print_pool()
        
        return candidate_pool.pool

    async def find_recommendations(self, candidate_pool: list[Pool_Song]):
        print("Finding recommendations")
        # Use the cached prompt template
        prompt_template = self.prepare_prompt_template()
        tourney = Tourney(candidate_pool, self.open_ai_service, prompt_template, num_tournaments=3)
        recommendations = await tourney.run_tourney(num_recommendations=5)
        print(f"Found {len(recommendations)} recommendations")
        return recommendations
    
