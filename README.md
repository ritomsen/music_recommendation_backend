## Music Recommendation Backend (FastAPI)

Backend service that generates personalized song recommendations by combining:
- User context from Spotify (via OAuth and Spotipy)
- Image analysis (OpenAI Vision or Gemini)
- Optional audio analysis (OpenAI Whisper, placeholder on Gemini)
- Optional location-based weather context (Google Weather API)

### Key features
- **Spotify OAuth flow** with short-lived session IDs used by the frontend
- **Recommendations** via LLM tournament or a **genetic algorithm**
- **Typed responses** using Pydantic models
- **Interactive docs** at `/docs` and `/redoc`

## Project structure

```
music_recommendation_backend/
├── app/
│   ├── main.py                       # FastAPI app & router wiring
│   ├── api/
│   │   └── routes/
│   │       ├── recommendation.py     # /api/v1/recommend, /recommend-genetic
│   │       └── spotify.py            # /api/v1/spotify/* (OAuth + helpers)
│   ├── core/
│   │   └── config.py                 # Settings loaded from .env
│   ├── models/
│   │   └── song.py                   # Pool_Song, SpotifyArtist, etc.
│   ├── prompts/                      # Prompt templates used by LLMs
│   ├── rec_service/
│   │   ├── recommendation.py         # Orchestrates context + LLMs
│   │   ├── candidate_pool.py         # Builds song pool from Spotify
│   │   └── tourney.py                # LLM tournament logic
│   ├── genetic_algo/
│   │   └── genetic.py                # Genetic algorithm recommender
│   ├── services/
│   │   ├── service_instances.py      # Shared singletons
│   │   ├── spotify_service.py        # Spotify data access (Spotipy)
│   │   ├── open_ai_service.py        # OpenAI (Vision, Whisper, Chat)
│   │   ├── gemini_service.py         # Gemini (Vision, Chat)
│   │   ├── weather_service.py        # Google Weather API client
│   │   ├── shazam_service.py         # Shazam lookup helpers
│   │   └── genius_service.py         # (Placeholder) lyrics
│   └── utils/
│       └── file_handlers.py          # Upload helpers
├── tests/                            # Pytest suite
├── requirements.txt
└── README.md
```

## Prerequisites
- Python 3.11+ (recommended)
- A Spotify Developer App (Client ID/Secret + Redirect URI)
- API keys as listed below

## Installation

```bash
python3 -m venv .venv
source ./.venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in this directory with at least the following variables:

```env
# Core
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/api/v1/spotify/callback
FRONTEND_URL=http://localhost:3000

# LLMs (choose one or both)
OPENAI_API_KEY=sk-...                # required if using OpenAI paths
GEMINI_API_KEY=...                   # required if using Gemini paths

# Other integrations
GENIUS_ACCESS_TOKEN=...              # optional, currently placeholder
GOOGLE_MAPS_KEY=...                  # for weather context
```

Notes:
- The app reads `.env` via Pydantic settings in `app/core/config.py`.
- CORS is currently set in `app/main.py` to allow `http://localhost:3000`.

## Running the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Docs: `http://localhost:8000/docs` (Swagger) and `http://localhost:8000/redoc`.

## OAuth flow (Spotify)
Endpoints (all are prefixed by `/api/v1/spotify`):
- `GET /login` → returns `{ auth_url, state }` for the client to redirect the user
- `GET /callback?code=...&state=...` → exchanges code, then redirects to `FRONTEND_URL?session_id=...`
- `GET /check-auth?session_id=...` → `{ authenticated: bool, message: string }`
- `POST /logout` body: `{ "session_id": "..." }`
- `GET /user-profile?session_id=...` → returns Spotify profile
- `GET /top-tracks?session_id=...&time_range=short_term|medium_term|long_term` → testing helper

The frontend should capture `session_id` from the callback redirect and include it in subsequent calls.

## Recommendation endpoints

Base path prefix: `/api/v1`

### POST `/api/v1/recommend`
Multipart form fields:
- `image` (file, required)
- `audio` (file, optional)
- `location` (string, optional, format: "lat,lon")
- `session_id` (string, required) — Spotify session ID from OAuth

Response: list of tuples `[Pool_Song, score]`. Example:

```json
[
  [
    {
      "title": "Song Title",
      "artist": "Artist Name",
      "album": "Album Name",
      "img_link": "https://...",
      "genre": "",
      "spotify_link": "https://open.spotify.com/track/...",
      "popularity_score": 73,
      "duration_ms": 207000,
      "release_date": "2019-01-01",
      "lyrics": ""
    },
    0.92
  ]
]
```

### POST `/api/v1/recommend-genetic`
Same request fields as above. Returns the same shape but uses a genetic algorithm under the hood.

### cURL examples

```bash
curl -X POST "http://localhost:8000/api/v1/recommend" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@/path/to/image.jpg" \
  -F "audio=@/path/to/audio.mp3" \
  -F "location=37.7749,-122.4194" \
  -F "session_id=YOUR_SESSION_ID"
```

```bash
curl -X GET "http://localhost:8000/api/v1/spotify/check-auth?session_id=YOUR_SESSION_ID"
```

## Data models

`Pool_Song` fields (see `app/models/song.py`):
- `title`, `artist`, `album`, `img_link`, `genre?`, `spotify_link`, `popularity_score?`, `duration_ms?`, `release_date?`, `lyrics?`

The recommendation endpoints return a list of `[Pool_Song, score]`, where `score` is a float between 0 and 1.

## Testing

```bash
pytest -q
# or
python tests/run_tests.py
```

Some tests or manual flows may require valid credentials and a logged-in Spotify session.

## Troubleshooting

- **Spotify redirect mismatch**: Ensure your Spotify app's redirect URI matches `SPOTIFY_REDIRECT_URI` exactly and is HTTPS in production.
- **HEIC images**: For HEIC uploads, `pillow-heif` is used. On macOS you may need: `brew install libheif`.
- **python-magic**: If you see import or runtime errors for `magic`, install libmagic. On macOS: `brew install libmagic` (or `brew install file`).
- **401 Invalid session**: Obtain a fresh `session_id` by visiting `/api/v1/spotify/login` and completing the OAuth flow.
- **CORS**: Default allowed origin is `http://localhost:3000` in `app/main.py`. Update as needed for your frontend.
- **Rate limits / API keys**: OpenAI, Google, and Spotify keys may rate limit; use appropriate models and quotas.

## Notes for development
- Candidate pool may be truncated to a max size of 75 in `recommendation.py` to keep tournaments fast.
- Prompts live in `app/prompts/*` and are loaded by the LLM services.

---

Maintained as part of the `music_recommendation` project. Contributions welcome!