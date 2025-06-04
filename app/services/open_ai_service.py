from typing import List, Optional, Dict
import os
import json
from pathlib import Path
import aiohttp
from openai import AsyncOpenAI
from app.models.song import Pool_Song
from app.services.ai_service import AIService
from app.core.config import settings
import base64
import io
from PIL import Image
import pillow_heif

class OpenAIService(AIService):
    def __init__(self):
        print("Initializing OpenAIService")
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4.1-nano"  # Using the fastest advanced model
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        
    def _is_heic(self, image_data: bytes) -> bool:
        """Check if the image data is in HEIC format"""
        return image_data.startswith(b'\x00\x00\x00\x20\x66\x74\x79\x70\x68\x65\x69\x63')

    def _convert_heic_to_jpeg(self, image_data: bytes) -> bytes:
        """Convert HEIC image data to JPEG format"""
        heif_file = pillow_heif.read_heif(image_data)
        image = Image.frombytes(
            heif_file.mode, 
            heif_file.size, 
            heif_file.data,
            "raw",
        )
        jpeg_buffer = io.BytesIO()
        image.save(jpeg_buffer, format="JPEG")
        return jpeg_buffer.getvalue()

    def _load_prompt(self, prompt_file: str) -> str:
        """Load prompt template from file"""
        print(f"Loading prompt from file: {prompt_file}")
        with open(self.prompts_dir / prompt_file, "r") as f:
            return f.read().strip()

    async def analyze_image(self, image_data: bytes, track_titles_and_artists: list[str], artist_names: list[str]) -> dict:
        """
        Analyze image using OpenAI Vision API
        """
        print("Starting image analysis")
        prompt = self._load_prompt("image_analysis.txt")
        prompt = prompt.format(top_songs=track_titles_and_artists, top_artists=artist_names)
        
        # Check if image is HEIC and convert if needed
        if self._is_heic(image_data):
            print("Converting HEIC image to JPEG")
            image_data = self._convert_heic_to_jpeg(image_data)
        
        # Encode image data as base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        print("Image encoded to base64")
        print(prompt)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "text", "text": """ Please provide your analysis in JSON format with the following structure:
                        {
                            "mood": "description of mood",
                            "genres": ["list of genres"], // Consider niche genres as well as well known ones
                            "energy_level": "low/medium/high",
                            "musical_characteristics": {
                                "tempo": "suggested_tempo",
                                "instrumentation": ["list of instruments"],
                                "style": "musical_style"
                            }
                        }

                            Focus on how these visual elements translate into specific musical characteristics and provide concrete musical suggestions. """},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format={ "type": "json_object" },
            max_tokens=1000
        )
        print("Received response from OpenAI Vision API")
        
        try:
            analysis = json.loads(response.choices[0].message.content)
            print(f"Successfully parsed image analysis: {analysis}")
            return {
                "mood": analysis.get("mood", "neutral"),
                "genres": analysis.get("genres", []),
                "energy_level": analysis.get("energy_level", "medium"),
                "musical_characteristics": analysis.get("musical_characteristics", {})
            }
        except json.JSONDecodeError as e:
            print(f"Failed to parse image analysis JSON: {e}")
            # Fallback to simple parsing if JSON parsing fails
            content = response.choices[0].message.content
            print(f"Using fallback parsing for content: {content}")
            return {
                "mood": "happy" if "happy" in content.lower() else "sad",
                "genre": "rock" if "rock" in content.lower() else "pop",
                "energy_level": "medium",
                "musical_characteristics": {}
            }

    async def analyze_audio(self, audio_data: bytes) -> dict:
        """
        Analyze audio using OpenAI Whisper API
        """
        print("Starting audio analysis")
        prompt = self._load_prompt("audio_analysis.txt")
        
        # Create a temporary file-like object from bytes
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.mp3"  # Add a filename
        print("Created audio file object")
        
        # First transcribe the audio
        print("Starting audio transcription")
        transcription = await self.client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1"
        )
        print(f"Audio transcription completed: {transcription.text[:100]}...")
        
        # Then analyze the transcription
        print("Starting transcription analysis")
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\nTranscription: {transcription.text}"
                }
            ],
            response_format={ "type": "json_object" },
            max_tokens=1000
        )
        print("Received response from OpenAI for audio analysis")
        
        try:
            analysis = json.loads(response.choices[0].message.content)
            print(f"Successfully parsed audio analysis: {analysis}")
            return {
                "tempo": analysis.get("tempo", "medium"),
                "genre": analysis.get("genre", "unknown"),
                "energy_level": analysis.get("energy_level", "medium"),
                "technical_details": analysis.get("technical_details", {})
            }
        except json.JSONDecodeError as e:
            print(f"Failed to parse audio analysis JSON: {e}")
            # Fallback to simple parsing if JSON parsing fails
            content = response.choices[0].message.content
            print(f"Using fallback parsing for content: {content}")
            return {
                "tempo": "medium" if "medium" in content.lower() else "fast",
                "genre": "rock" if "rock" in content.lower() else "pop",
                "energy_level": "medium",
                "technical_details": {}
            }
    
    async def get_recommendation(
        self,
        song_1: Pool_Song,
        song_2: Pool_Song,
        prompt_template: str,
    ) -> int:
        """
        Get song recommendations based on analyzed features
        """
        print("Starting song recommendation analysis")
        # print(f"Comparing songs: {song_1.title} vs {song_2.title}")
        
        # Format the prompt with song details
        try:
            prompt = prompt_template.format(
                song1_title=song_1.title,
                song1_artist=song_1.artist,
                song1_popularity=song_1.popularity_score,
                song1_duration=song_1.duration_ms,
                song1_release_date=song_1.release_date,
                song2_title=song_2.title,
                song2_artist=song_2.artist,
                song2_popularity=song_2.popularity_score,
                song2_duration=song_2.duration_ms,
                song2_release_date=song_2.release_date,
            )
            print("Prompt formatted with song details")
        except Exception as e:
            print(f"Error formatting prompt: {e}")
            return 0
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt 
                },
                {
                    "role": "user",
                    "content": 
                    """ Provide your response in JSON with the following structure: 
                    { 
                        "song_1_analysis": "One sentence analysis of song 1",
                        "song_2_analysis": "One sentence analysis of song 2",
                        "winner": "1" or "2",
                        "reason": "One sentence explanation of why the winning song is better"
                    } """
                }
            ],
            response_format={ "type": "json_object" },
            max_tokens=1000
        )
        print("Received response from OpenAI for song recommendation")
        print(f"Raw response content for {song_1.title} vs {song_2.title}: {response.choices[0].message.content}")
        
        try:
            analysis = json.loads(response.choices[0].message.content)
            print(f"Successfully parsed recommendation analysis: {analysis}")
            # Extract the final recommendation from the comparison
            winner = analysis.get("winner", "")
            print(f"Winner from analysis: {winner}")

            return 0 if "1" in winner else 1
        except json.JSONDecodeError as e:
            print(f"Failed to parse recommendation JSON: {e}")
            print(f"Raw content that failed to parse: {response.choices[0].message.content}")
            # Fallback to simple parsing if JSON parsing fails
            recommendation = response.choices[0].message.content.strip()
            print(f"Using fallback parsing for content: {recommendation}")
            return 0 if "1" in recommendation.lower() else 1
    
    async def generate_user_context(
        self,
        name: str,
        top_songs_short: list,
        top_songs_medium: list,
        top_songs_long: list,
        top_artists_short: list,
        top_artists_medium: list,
        top_artists_long: list,
        recently_played: list
    ) -> dict:
        """
        Generate a user context summary using the LLM and the user_context prompt.
        """
        prompt = self._load_prompt("user_context.txt")
        # Format the prompt with user data (convert lists to comma-separated strings or JSON as needed)
        prompt = prompt.format(
            top_songs_short=top_songs_short,
            top_songs_medium=top_songs_medium,
            top_songs_long=top_songs_long,
            top_artists_short=top_artists_short,
            top_artists_medium=top_artists_medium,
            top_artists_long=top_artists_long,
            recently_played=recently_played
        )
        print("Prompt for user context", prompt)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "user", "content": """
                Respond ONLY with a valid JSON object in the following format:
                {
                    "description": "<2-3 sentence summary of their music tastes and tendencies>",
                    "genres": ["<genre1>", "<genre2>", ...]
                }"""}
            ],
            response_format={"type": "json_object"},
            max_tokens=500
        )
        try:
            user_context = json.loads(response.choices[0].message.content)
            return user_context
        except Exception as e:
            print(f"Failed to parse user context JSON: {e}")
            print(f"Raw content: {response.choices[0].message.content}")
            return {}


