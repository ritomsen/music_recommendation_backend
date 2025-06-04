from typing import List, Optional, Dict
import os
import json
from pathlib import Path
import google.generativeai as genai
from app.models.song import Pool_Song
from app.services.ai_service import AIService
import base64
import io

class GeminiService(AIService):
    def __init__(self):
        print("Initializing GeminiService")
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        
    def _load_prompt(self, prompt_file: str) -> str:
        """Load prompt template from file"""
        print(f"Loading prompt from file: {prompt_file}")
        with open(self.prompts_dir / prompt_file, "r") as f:
            return f.read().strip()

    async def analyze_image(self, image_data: bytes, track_titles_and_artists: list[str], artist_names: list[str]) -> dict:
        """
        Analyze image using Gemini Vision API
        """
        print("Starting image analysis")
        prompt = self._load_prompt("image_analysis.txt")
        prompt = prompt.format(top_songs=track_titles_and_artists, top_artists=artist_names)
        
        # Encode image data as base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        print("Image encoded to base64")
        print(prompt)

        response = await self.vision_model.generate_content_async([
            prompt,
            """ Please provide your analysis in JSON format with the following structure:
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

            Focus on how these visual elements translate into specific musical characteristics and provide concrete musical suggestions. """,
            {"mime_type": "image/jpeg", "data": image_data}
        ])
        
        print("Received response from Gemini Vision API")
        
        try:
            analysis = json.loads(response.text)
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
            content = response.text
            print(f"Using fallback parsing for content: {content}")
            return {
                "mood": "happy" if "happy" in content.lower() else "sad",
                "genre": "rock" if "rock" in content.lower() else "pop",
                "energy_level": "medium",
                "musical_characteristics": {}
            }

    async def analyze_audio(self, audio_data: bytes) -> dict:
        """
        Analyze audio using Gemini API
        Note: Since Gemini doesn't have direct audio analysis, we'll use text analysis
        """
        print("Starting audio analysis")
        prompt = self._load_prompt("audio_analysis.txt")
        
        # Create a temporary file-like object from bytes
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.mp3"  # Add a filename
        print("Created audio file object")
        
        # Since Gemini doesn't have direct audio analysis, we'll need to convert audio to text first
        # This is a placeholder - you'll need to implement audio transcription separately
        transcription = "Placeholder for audio transcription"
        print(f"Audio transcription completed: {transcription[:100]}...")
        
        # Then analyze the transcription
        print("Starting transcription analysis")
        response = await self.model.generate_content_async([
            f"{prompt}\n\nTranscription: {transcription}"
        ])
        
        print("Received response from Gemini for audio analysis")
        
        try:
            analysis = json.loads(response.text)
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
            content = response.text
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
        print(f"Comparing songs: {song_1.title} vs {song_2.title}")
        
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
        
        response = await self.model.generate_content_async([
            prompt,
            """ Provide your response in JSON with the following structure: 
            { 
                "winner": "1" or "2",
                "reason": "Explanation of why the winning song is better, max 2 sentences"
            } """
        ])
        
        print("Received response from Gemini for song recommendation")
        print(f"Raw response content: {response.text}")
        
        try:
            analysis = json.loads(response.text)
            print(f"Successfully parsed recommendation analysis: {analysis}")
            # Extract the final recommendation from the comparison
            winner = analysis.get("winner", "")
            print(f"Winner from analysis: {winner}")

            return 0 if "1" in winner else 1
        except json.JSONDecodeError as e:
            print(f"Failed to parse recommendation JSON: {e}")
            print(f"Raw content that failed to parse: {response.text}")
            # Fallback to simple parsing if JSON parsing fails
            recommendation = response.text.strip()
            print(f"Using fallback parsing for content: {recommendation}")
            return 0 if "song1" in recommendation.lower() else 1 