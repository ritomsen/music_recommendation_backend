# Music Recommendation API

This API provides song recommendations based on image and audio inputs, with optional location data.

## Project Structure

```
music_recommendation_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   │   ├── __init__.py
│   │   └── main.py
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── recommendation.py
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   └── config.py
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   └── song.py
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── ai_service.py
│   │   └── recommendation_service.py
│   └── utils/                 # Utility functions
│       ├── __init__.py
│       └── file_handlers.py
├── tests/                     # Test files
│   └── __init__.py
├── requirements.txt
└── README.md
```

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory and add your configuration:
```env
OPENAI_API_KEY=your_api_key_here
```

4. Run the API server:
```bash
python -m app.main
```

The server will start at `http://localhost:8000`

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoint

### POST /api/v1/recommend

Get song recommendations based on image and audio inputs.

**Request:**
- `image`: Image file (required)
- `audio`: Audio file (required)
- `location`: Location string (optional)

**Response:**
```json
[
    {
        "title": "Song Title",
        "artist": "Artist Name",
        "album": "Album Name",
        "spotify_link": "https://open.spotify.com/track/...",
        "img_link": "https://i.scdn.co/image/..."
    }
]
```

## Example Usage

You can test the API using curl:
```bash
curl -X POST "http://localhost:8000/api/v1/recommend" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "image=@path/to/image.jpg" \
     -F "audio=@path/to/audio.mp3" \
     -F "location=New York"
```

Or using Python requests:
```python
import requests

url = "http://localhost:8000/api/v1/recommend"
files = {
    'image': ('image.jpg', open('path/to/image.jpg', 'rb')),
    'audio': ('audio.mp3', open('path/to/audio.mp3', 'rb'))
}
data = {'location': 'New York'}

response = requests.post(url, files=files, data=data)
print(response.json())
```

## Development

The project is structured to make it easy to add new features:

1. Add new routes in `app/api/routes/`
2. Add new services in `app/services/`
3. Add new models in `app/models/`
4. Add utility functions in `app/utils/`

## Testing

To run tests (when implemented):
```bash
pytest
``` 